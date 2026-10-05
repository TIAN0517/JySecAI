package c2

import (
	"errors"
	"net"
	"strings"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

// ResolveBeaconDialHost 决定植入端应连接的主机名（不含端口）。
// 优先级：explicitOverride > 监听器 config_json 中的 callback_host > bind_host（0.0.0.0/::/空 时 detectExternalIP，失败则 127.0.0.1）。
func ResolveBeaconDialHost(listener *database.C2Listener, explicitOverride string, logger *zap.Logger, listenerID string) string {
	if h := strings.TrimSpace(explicitOverride); h != "" {
		// This value is interpolated into the Go source of a generated beacon and
		// into shell one-liners. Reject anything that is not a plain host or IP so
		// a quote can never reach those sinks, even if a future template change
		// drops the %q quoting applied in payload_builder.go.
		if err := validateBeaconHost(h); err != nil {
			if logger != nil {
				logger.Warn("拒绝非法的 beacon 回连主机", zap.String("host", h), zap.Error(err))
			}
		} else {
			return h
		}
	}
	cfg := &ListenerConfig{}
	if listener != nil && listener.ConfigJSON != "" {
		_ = parseJSON(listener.ConfigJSON, cfg)
	}
	// callback_host 同样来自监听器配置，必须走同一套校验，否则它会成为绕过
	// explicitOverride 校验的旁路。
	if h := strings.TrimSpace(cfg.CallbackHost); h != "" {
		if err := validateBeaconHost(h); err != nil {
			if logger != nil {
				logger.Warn("拒绝非法的 callback_host", zap.String("host", h), zap.Error(err))
			}
		} else {
			return h
		}
	}
	if listener == nil {
		return "127.0.0.1"
	}
	host := strings.TrimSpace(listener.BindHost)
	if host == "0.0.0.0" || host == "" || host == "::" {
		host = detectExternalIP()
		if host == "" {
			if logger != nil {
				logger.Warn("listener binds 0.0.0.0 but no external IP detected, falling back to 127.0.0.1; set callback_host or pass explicit host",
					zap.String("listener_id", listenerID))
			}
			return "127.0.0.1"
		}
	}
	// bind_host 是第三个来源，同样来自请求（CreateListener / UpdateListener 只做
	// TrimSpace）。不校验它就等于留了一条绕过前两道校验的旁路：listener 根本
	// 不需要成功 net.Listen，只要存在于资料库就能把恶意值送进模板与 oneliner。
	if err := validateBeaconHost(host); err != nil {
		if logger != nil {
			logger.Warn("拒绝非法的 listener bind_host", zap.String("host", host), zap.Error(err))
		}
		return "127.0.0.1"
	}
	return host
}

// ValidateBeaconHost 是 validateBeaconHost 的导出包装，供 handler / MCP 工具在
// 写入点（CreateListener / UpdateListener）使用：让 an unusable value never
// reaches the database at all, rather than being sanitised on every read.
func ValidateBeaconHost(host string) error { return validateBeaconHost(host) }

// validateBeaconHost accepts only a literal IP or a syntactically valid DNS
// name. The value is spliced into generated Go source and into shell
// one-liners, so quotes, backticks, whitespace, and shell metacharacters are
// rejected outright rather than escaped downstream.
func validateBeaconHost(host string) error {
	if host == "" {
		return errors.New("empty host")
	}
	if len(host) > 253 {
		return errors.New("host too long")
	}
	if net.ParseIP(host) != nil {
		return nil
	}
	// IPv6 literals in a URL authority may carry brackets and a zone.
	if strings.HasPrefix(host, "[") {
		if i := strings.LastIndex(host, "]"); i > 0 {
			if i+1 == len(host) {
				inner := host[1:i]
				if net.ParseIP(inner) != nil || strings.HasPrefix(inner, "fe80:") {
					return nil
				}
			}
		}
		return errors.New("invalid IPv6 literal")
	}
	for _, label := range strings.Split(strings.TrimSuffix(host, "."), ".") {
		if label == "" || len(label) > 63 {
			return errors.New("invalid DNS label")
		}
		if label[0] == '-' || label[len(label)-1] == '-' {
			return errors.New("DNS label may not start or end with '-'")
		}
		for i := 0; i < len(label); i++ {
			ch := label[i]
			isAlnum := (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9')
			if !isAlnum && ch != '-' && ch != '_' {
				return errors.New("invalid character in DNS label")
			}
		}
	}
	return nil
}
