package app

import (
	"context"
	"encoding/json"
	"errors"
	"regexp"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"go.uber.org/zap"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/receiver"
	"jysecai/internal/vulnmask"
	"jysecai/internal/vulnoutbound"
)

// receiverBridge 把平台收割到的成果送到外部 MySQL 接收端。
//
// 這條路徑只有一條紅線：不能拖慢、不能拖垮主寫入。
//
//   - 成果先落在本地寄件箱（平台自己的 SQLite），再由背景 worker 送往外部 MySQL。
//     外部 MySQL 掛掉時成果不會消失，只是留在寄件箱裡等它回來。
//   - 寫寄件箱發生在 hook 自己的 goroutine 上，不在平台的寫入路徑上。
//   - 送出失敗會記錄並保留，絕不因為「送不出去」而丟資料。
//
// 為什麼不直接在 hook 裡同步送出：hook 是被漏洞寫入路徑呼叫的，
// 同步送出等於把外部 MySQL 的可用性與延遲灌進平台的核心寫入路徑。
// 一旦外部庫變慢，主流程就跟著變慢 —— 這正是「外部接收端」和「主資料庫」
// 必須分開的理由。
type receiverBridge struct {
	mu   sync.RWMutex
	sink receiver.Sink

	// outbox 本地持久化寄件箱。成果的唯一真實來源。
	outbox *receiver.SQLiteOutbox
	// wake 喚醒排程器的單格訊號。送出是非阻塞的：滿了就等下一個 tick。
	wake chan struct{}

	logger *zap.Logger

	// host 外部 MySQL 的主機位址。只用來把錯誤訊息裡的位址遮掉 ——
	// 日誌是除錯時最常被外帶的東西，內網位址不該跟著跑。
	host string

	timeout      time.Duration
	batchSize    int
	pollInterval time.Duration

	// maskPolicy 對外輸出去識別化政策。預設遮蔽位址與憑證。
	maskPolicy vulnmask.Policy

	ctx    context.Context
	cancel context.CancelFunc
	wg     sync.WaitGroup

	delivered atomic.Int64
	skipped   atomic.Int64
	failed    atomic.Int64
	dropped   atomic.Int64
}

// newReceiverBridge 建立接收橋接。
func newReceiverBridge(outbox *receiver.SQLiteOutbox, cfg config.ExternalMySQLConfig, logger *zap.Logger) *receiverBridge {
	batchSize := cfg.BatchSize
	if batchSize <= 0 {
		batchSize = 50
	}
	timeout := time.Duration(cfg.TimeoutSeconds) * time.Second
	if timeout <= 0 {
		timeout = 10 * time.Second
	}
	pollInterval := time.Duration(cfg.PollIntervalSeconds) * time.Second
	if pollInterval <= 0 {
		pollInterval = 5 * time.Second
	}
	if logger == nil {
		logger = zap.NewNop()
	}
	ctx, cancel := context.WithCancel(context.Background())
	policy := vulnmask.DefaultPolicy()
	if cfg.DisableMasking {
		// 明示關閉才關閉。預設必須是遮蔽 —— 送出去的資料一旦離開平台就無法收回。
		policy.MaskIPs = false
		policy.MaskSecrets = false
		policy.MaskHosts = false
		logger.Warn("外部 MySQL 對外輸出遮蔽已被關閉：target/evidence 會以原文寫入外部資料庫")
	}
	if cfg.MaskHosts {
		policy.MaskHosts = true
	}
	if len(cfg.RedactIPs) > 0 {
		policy = policy.WithRedactedIPs(cfg.RedactIPs...)
	}
	return &receiverBridge{
		outbox:       outbox,
		wake:         make(chan struct{}, 1),
		logger:       logger,
		host:         strings.TrimSpace(cfg.Host),
		timeout:      timeout,
		batchSize:    batchSize,
		pollInterval: pollInterval,
		maskPolicy:   policy,
		ctx:          ctx,
		cancel:       cancel,
	}
}

// maskError 把錯誤訊息裡的外部主機位址遮掉再拿去記錄。
func (b *receiverBridge) maskError(err error) error {
	if err == nil || b == nil || b.host == "" {
		return err
	}
	return errors.New(strings.ReplaceAll(err.Error(), b.host, "<mysql-host>"))
}

// Start 啟動排程器。
func (b *receiverBridge) Start() {
	if b == nil {
		return
	}
	b.wg.Add(1)
	go b.drainer()
}

// Stop 停止排程器並等待在途的送出結束。
func (b *receiverBridge) Stop() {
	if b == nil {
		return
	}
	b.cancel()
	b.wg.Wait()
	b.mu.Lock()
	sink := b.sink
	b.sink = nil
	b.mu.Unlock()
	if sink != nil {
		_ = sink.Close()
	}
}

// SetSink 換掉接收端。連線失敗後靠背景重連補上時會用到。
func (b *receiverBridge) SetSink(sink receiver.Sink) {
	if b == nil {
		return
	}
	b.mu.Lock()
	old := b.sink
	b.sink = sink
	b.mu.Unlock()
	if old != nil && old != sink {
		_ = old.Close()
	}
}

func (b *receiverBridge) currentSink() receiver.Sink {
	b.mu.RLock()
	defer b.mu.RUnlock()
	return b.sink
}

// Stats 回傳接收端統計。供啟動日誌、關機日誌與診斷使用。
func (b *receiverBridge) Stats() (delivered, skipped, failed, dropped int64) {
	if b == nil {
		return 0, 0, 0, 0
	}
	return b.delivered.Load(), b.skipped.Load(), b.failed.Load(), b.dropped.Load()
}

// Pending 回傳寄件箱裡還有多少筆待送成果。
func (b *receiverBridge) Pending(ctx context.Context) int {
	if b == nil || b.outbox == nil {
		return 0
	}
	n, err := b.outbox.Pending(ctx)
	if err != nil {
		return 0
	}
	return n
}

// signal 喚醒排程器。非阻塞：訊號格滿了代表排程器反正已經被喚醒過。
func (b *receiverBridge) signal() {
	select {
	case b.wake <- struct{}{}:
	default:
	}
}

// Enqueue 放一份成果進本地寄件箱。
//
// 這是 harvest 的第一步。寫進寄件箱就代表成果已經安全落地 —— 外部 MySQL
// 連不連得上，都不會影響這一步。所以這裡只會有兩種結果：寫進去，或寫失敗
// 並記錄。沒有「丟棄」這個選項。
func (b *receiverBridge) Enqueue(p receiver.Payload) {
	if b == nil || b.outbox == nil {
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), b.timeout)
	defer cancel()
	if err := b.outbox.Enqueue(ctx, p); err != nil {
		b.dropped.Add(1)
		b.logger.Error("寫入接收端本地寄件箱失敗，本次收割成果未落地",
			zap.String("source_kind", p.SourceKind),
			zap.String("source_id", p.SourceID),
			zap.Error(b.maskError(err)),
		)
		return
	}
	b.signal()
}

// drainer 背景排程器：把寄件箱裡的成果送到外部 MySQL。
func (b *receiverBridge) drainer() {
	defer b.wg.Done()
	ticker := time.NewTicker(b.pollInterval)
	defer ticker.Stop()
	for {
		select {
		case <-b.ctx.Done():
			return
		case <-b.wake:
		case <-ticker.C:
		}
		b.drainOnce()
	}
}

// drainOnce 送一批。
func (b *receiverBridge) drainOnce() {
	sink := b.currentSink()
	if sink == nil {
		// 外部 MySQL 還沒連上。成果留在寄件箱，不急 —— 它已經安全落地了。
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), b.timeout*4)
	defer cancel()
	items, err := b.outbox.Claim(ctx, b.batchSize)
	if err != nil {
		b.logger.Warn("讀取接收端本地寄件箱失敗", zap.Error(b.maskError(err)))
		return
	}
	for _, item := range items {
		if b.ctx.Err() != nil {
			return
		}
		if err := b.deliver(sink, item.Payload); err != nil {
			// 失敗就留在寄件箱。這一批先停 —— MySQL 掛了之後繼續送只是
			// 把同一個錯誤重複一遍，而且會把失敗紀錄灌滿。
			if nackErr := b.outbox.Nack(ctx, item.Payload.SourceKind, item.Payload.SourceID, err); nackErr != nil {
				b.logger.Warn("更新接收端寄件箱失敗狀態時出錯", zap.Error(b.maskError(nackErr)))
			}
			b.failed.Add(1)
			b.logger.Warn("外部接收端送出失敗，成果保留在本地寄件箱等待重試",
				zap.String("source_kind", item.Payload.SourceKind),
				zap.String("source_id", item.Payload.SourceID),
				zap.Error(b.maskError(err)),
			)
			return
		}
		if ackErr := b.outbox.Ack(ctx, item.Payload.SourceKind, item.Payload.SourceID); ackErr != nil {
			b.logger.Warn("清除接收端寄件箱紀錄失敗（成果已送出，下次會重送並被冪等跳過）",
				zap.Error(b.maskError(ackErr)))
		}
	}
}

// deliver 送出一筆成果。失敗回 error，成功回 nil。
func (b *receiverBridge) deliver(sink receiver.Sink, p receiver.Payload) error {
	ctx, cancel := context.WithTimeout(context.Background(), b.timeout)
	defer cancel()
	res, err := sink.Deliver(ctx, p)
	if err != nil {
		// 失敗也要在接收端留痕：沒有失敗紀錄的接收端，看起來就像
		// 「從來沒有東西要送」。
		if rec, ok := sink.(receiver.FailureRecorder); ok {
			failCtx, failCancel := context.WithTimeout(context.Background(), b.timeout)
			rec.RecordFailure(failCtx, p, err)
			failCancel()
		}
		return err
	}
	if res.Skipped {
		b.skipped.Add(1)
		return nil
	}
	b.delivered.Add(1)
	return nil
}

// OnVulnerabilityPersisted 漏洞記錄落地後的鉤子。
//
// 涵蓋建立、證據合併補強、更新三種情況 —— 收割成果的大宗在後續補強裡，
// 只接建立的話下游拿到的會永遠是第一版。
func (b *receiverBridge) OnVulnerabilityPersisted(v *database.Vulnerability) {
	b.Enqueue(vulnerabilityPayloadWithPolicy(v, b.maskPolicy))
}

// OnProjectFactUpserted 專案事實寫入後的鉤子。
//
// 專案事實是「利用後數據」的主要載體：黑板的 body 記著完整的攻擊鏈
// 與實際取到的資料。
func (b *receiverBridge) OnProjectFactUpserted(f *database.ProjectFact) {
	b.Enqueue(projectFactPayloadWithPolicy(f, b.maskPolicy))
}

// vulnerabilityPayload 把漏洞記錄映射成接收端成果。
//
// 遮蔽在這裡發生：送出外部的 target / evidence / 描述文字會含真實目標位址、
// 憑證與測試環境內網位址，離開平台後就無法收回。分類、嚴重度、狀態、信心值
// 這些分析維度不遮。
func vulnerabilityPayload(v *database.Vulnerability) receiver.Payload {
	return vulnoutbound.VulnerabilityPayload(v, vulnmask.DefaultPolicy())
}

// vulnerabilityPayloadWithPolicy 用指定政策產生成果（橋接器實際使用的路徑）。
func vulnerabilityPayloadWithPolicy(v *database.Vulnerability, policy vulnmask.Policy) receiver.Payload {
	return vulnoutbound.VulnerabilityPayload(v, policy)
}

// factConfidenceScore 把專案事實的字串等級數值化，讓倉儲側可以直接篩選。
//
// 數值只是篩選用的投影，原始字串仍在 meta.confidence —— 不要把它當成
// 漏洞的 95% 確認閘門分數，兩者語意不同。
func factConfidenceScore(confidence string) int {
	switch strings.ToLower(strings.TrimSpace(confidence)) {
	case "confirmed":
		return 95
	case "tentative":
		return 50
	default:
		return 0
	}
}

// projectFactPayload 把專案事實映射成接收端成果。
func projectFactPayload(f *database.ProjectFact) receiver.Payload {
	return projectFactPayloadWithPolicy(f, vulnmask.DefaultPolicy())
}

// projectFactPayloadWithPolicy 用指定遮蔽政策產生成果。
//
// 遮蔽分成兩輪：同一組預設帳密會以不同欄位、不同語境出現在同一筆事實裡，
// 第一輪各欄位獨立遮蔽並收集憑證值，第二輪把收集到的值一併抹掉。
func projectFactPayloadWithPolicy(f *database.ProjectFact, policy vulnmask.Policy) receiver.Payload {
	if f == nil {
		return receiver.Payload{}
	}
	session := policy.NewSession()

	factKey := session.Mask(f.FactKey)
	title := session.Mask(f.Summary)
	target := session.Mask(extractTargetDNS(f.FactKey, f.Summary))
	body := session.Mask(f.Body)

	factKey = session.Scrub(factKey)
	title = session.Scrub(title)
	target = session.Scrub(target)
	body = session.Scrub(body)

	return receiver.Payload{
		SourceKind:      receiver.SourceKindProjectFact,
		SourceID:        f.ID,
		ProjectID:       f.ProjectID,
		ConversationID:  f.SourceConversationID,
		VulnerabilityID: f.RelatedVulnerabilityID,
		FactKey:         factKey,
		Category:        f.Category,
		Title:           title,
		Target:          target,
		Confidence:      factConfidenceScore(f.Confidence),
		Body:            body,
		Meta: marshalMeta(map[string]any{
			"confidence":               f.Confidence,
			"pinned":                   f.Pinned,
			"source_conversation_id":   f.SourceConversationID,
			"source_message_id":        f.SourceMessageID,
			"related_vulnerability_id": f.RelatedVulnerabilityID,
		}),
		OccurredAt: f.CreatedAt,
	}
}

// factKeyDNSPattern 抓 fact key 裡的 DNS 片段。
//
// 攻擊鏈沉淀的 fact key 格式是「<namespace>/<dns>[-<slug>]」，
// 例如 finding/api.example.com-sql-injection。DNS 本身可能含「-」，
// 所以不能用「取第一段破折號」來切 —— 那會把 my-host.example.com 砍成 my。
// 用「整串裡第一個像 hostname 的 token」來抓，尾巴的 slug 自然被排除。
var factKeyDNSPattern = regexp.MustCompile(`(?i)\b((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,})\b`)

// extractTargetDNS 從 fact key（退而求其次是摘要）裡取出目標 DNS。
//
// 沒有 DNS 就回空字串：寧可讓目標欄位留空，也不要塞 IP 或猜出來的字串 ——
// 錯的目標比沒目標更難查。
func extractTargetDNS(factKey, fallback string) string {
	for _, candidate := range []string{factKey, fallback} {
		if m := factKeyDNSPattern.FindString(candidate); m != "" {
			return strings.ToLower(m)
		}
	}
	return ""
}

// marshalMeta 序列化來源專屬欄位。失敗就留空，不要讓附加欄位拖垮整筆送出。
func marshalMeta(m map[string]any) string {
	if len(m) == 0 {
		return ""
	}
	b, err := json.Marshal(m)
	if err != nil {
		return ""
	}
	return string(b)
}
