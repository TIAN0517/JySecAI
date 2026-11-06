package robot

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"jysecai/internal/config"

	"go.uber.org/zap"
)

const (
	telegramPlatform        = "telegram"
	telegramLongPollSec     = 30
	telegramMaxMessageRunes = 4096
	// telegramHTTPTimeout 长轮询的 HTTP 客户端超时。
	// Telegram 的 long poll 最长会挂 30 秒，网络抖动时响应可能超过 40 秒，
	// 超时会导致无谓的重连（每次重连都可能重新拉取积压），这里放宽到 60 秒。
	telegramHTTPTimeout = telegramLongPollSec*time.Second + 30*time.Second
)

// telegramAPIBase 抽成变量，便于测试注入本地假服务端。
var telegramAPIBase = "https://api.telegram.org"

type telegramUpdate struct {
	UpdateID      int                    `json:"update_id"`
	Message       *telegramMessage       `json:"message"`
	CallbackQuery *telegramCallbackQuery `json:"callback_query"`
}

type telegramMessage struct {
	MessageID int64            `json:"message_id"`
	Chat      telegramChat     `json:"chat"`
	From      *telegramUser    `json:"from"`
	Text      string           `json:"text"`
	Entities  []telegramEntity `json:"entities"`
}

type telegramChat struct {
	ID    int64  `json:"id"`
	Type  string `json:"type"`
	Title string `json:"title"`
}

type telegramUser struct {
	ID       int64  `json:"id"`
	Username string `json:"username"`
	IsBot    bool   `json:"is_bot"`
}

type telegramEntity struct {
	Type   string `json:"type"`
	Offset int    `json:"offset"`
	Length int    `json:"length"`
}

type telegramGetUpdatesResp struct {
	OK          bool             `json:"ok"`
	Result      []telegramUpdate `json:"result"`
	Description string           `json:"description"`
}

type telegramBotMe struct {
	OK          bool   `json:"ok"`
	Description string `json:"description"`
	Result      struct {
		ID       int64  `json:"id"`
		Username string `json:"username"`
	} `json:"result"`
}

// StartTelegram 启动 Telegram Bot 长轮询（getUpdates，无需公网回调）。
// 调用方（app.startRobotConnections）已用 go 启动本函数；这里必须同步跑
// runTelegramLoop，否则会开出两条 getUpdates 长轮询互相 Conflict，群消息过滤也失效。
// offsets 用于持久化已消费的 update_id，跨重启避免重放历史消息（可传 nil）。
func StartTelegram(ctx context.Context, robotsCfg config.RobotsConfig, h MessageHandler, logger *zap.Logger, offsets StreamOffsetStore, callbacks ...CallbackHandler) {
	cfg := robotsCfg.Telegram
	if !cfg.Enabled || strings.TrimSpace(cfg.BotToken) == "" {
		return
	}
	runTelegramLoop(ctx, cfg, h, logger, offsets, callbacks)
}

func runTelegramLoop(ctx context.Context, cfg config.RobotTelegramConfig, h MessageHandler, logger *zap.Logger, offsets StreamOffsetStore, callbacks []CallbackHandler) {
	backoff := reconnectInitial
	for {
		err := runTelegramPoll(ctx, cfg, h, logger, offsets, callbacks)
		if ctx.Err() != nil {
			logger.Info("Telegram 长轮询已按配置关闭")
			return
		}
		if err != nil {
			logger.Warn("Telegram 长轮询异常，将自动重连", zap.Error(err), zap.Duration("retry_after", backoff))
		}
		if !waitReconnect(ctx, &backoff) {
			return
		}
	}
}

func runTelegramPoll(ctx context.Context, cfg config.RobotTelegramConfig, h MessageHandler, logger *zap.Logger, offsets StreamOffsetStore, callbacks []CallbackHandler) error {
	token := strings.TrimSpace(cfg.BotToken)
	botUsername := strings.TrimSpace(cfg.BotUsername)
	if botUsername == "" {
		if name, err := telegramGetMe(ctx, token); err != nil {
			logger.Warn("Telegram getMe 失败", zap.Error(err))
		} else {
			botUsername = name
		}
	}
	client := &http.Client{Timeout: telegramHTTPTimeout}

	offset := resolveTelegramStartOffset(cfg, offsets, logger)
	skipBacklog := false
	if offset < 0 {
		// 从未持久化过游标：先用 offset=-1 探一次「最后一条 update」，
		// 把整段历史积压标记为已消费（不回覆），之后正常轮询就不会重播旧消息。
		established, err := telegramEstablishStartOffset(ctx, client, token)
		if err != nil {
			// 探测失败时退而求其次：以 -1 起步并静默消费首批更新，宁可漏答也不重播。
			logger.Warn("Telegram 跳过历史积压失败，改为静默消费首批更新", zap.Error(err))
			skipBacklog = true
		} else {
			offset = established
			logger.Info("Telegram 已跳过启动前的消息积压", zap.Int64("offset", offset))
		}
	}
	logger.Info("Telegram 长轮询已启动", zap.String("bot", botUsername), zap.Int64("offset", offset))

	persisted := int64(0)
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		updates, err := telegramGetUpdates(ctx, client, token, offset)
		if err != nil {
			return err
		}
		for _, u := range updates {
			next := int64(u.UpdateID) + 1
			if next > offset {
				offset = next
			}
			if skipBacklog {
				// 静默消费：只推进游标，不回覆历史消息。
				continue
			}
			if u.CallbackQuery != nil {
				// inline 按鈕點擊走的是 callback_query，不是訊息。
				handleTelegramCallback(ctx, client, token, u.CallbackQuery, callbacks, logger)
				continue
			}
			if u.Message == nil || u.Message.From == nil || u.Message.From.IsBot {
				continue
			}
			text := strings.TrimSpace(u.Message.Text)
			if text == "" {
				continue
			}
			chatType := strings.ToLower(strings.TrimSpace(u.Message.Chat.Type))
			if chatType != "private" {
				if !cfg.AllowGroupMessages {
					continue
				}
				if botUsername != "" && !telegramMentionsBot(text, u.Message.Entities, botUsername) {
					continue
				}
			}
			userID := telegramSessionKey(chatType, u.Message.Chat.ID, u.Message.From.ID)
			logger.Info("Telegram 收到消息", zap.String("from", userID), zap.Int("content_bytes", len(text)))
			reply := h.HandleMessage(telegramPlatform, userID, text)
			if err := telegramSendReply(ctx, client, token, u.Message.Chat.ID, reply); err != nil {
				logger.Warn("Telegram 发送回复失败", zap.String("to", userID), zap.Error(err))
			}
		}
		skipBacklog = false
		if offset > persisted {
			// 游标前进后立即落库，保证重启后不会重播已消费的消息。
			if offsets != nil {
				if err := offsets.SaveRobotStreamOffset(telegramPlatform, offset); err != nil {
					logger.Warn("保存 Telegram 轮询游标失败", zap.Error(err))
				}
			}
			persisted = offset
		}
	}
}

// resolveTelegramStartOffset 决定长轮询起点：
//  1. 优先使用持久化游标（跨重启不重播）；
//  2. 其次使用配置里的 update_offset；
//  3. 两者都没有时返回 -1，表示「跳过启动前的历史积压」。
//
// 只会取两者中较大的值，保证游标不回退。
func resolveTelegramStartOffset(cfg config.RobotTelegramConfig, offsets StreamOffsetStore, logger *zap.Logger) int64 {
	configured := cfg.UpdateOffset
	stored := int64(0)
	if offsets != nil {
		value, err := offsets.GetRobotStreamOffset(telegramPlatform)
		if err != nil {
			logger.Warn("读取 Telegram 轮询游标失败", zap.Error(err))
		} else {
			stored = value
		}
	}
	switch {
	case stored > 0 && configured > stored:
		return configured
	case stored > 0:
		return stored
	case configured > 0:
		return configured
	default:
		return -1
	}
}

func telegramSessionKey(chatType string, chatID, fromUserID int64) string {
	if chatType == "private" {
		return fmt.Sprintf("u:%d", fromUserID)
	}
	return fmt.Sprintf("g:%d|u:%d", chatID, fromUserID)
}

func telegramMentionsBot(text string, entities []telegramEntity, botUsername string) bool {
	needle := "@" + strings.TrimPrefix(strings.ToLower(botUsername), "@")
	lower := strings.ToLower(text)
	if strings.Contains(lower, needle) {
		return true
	}
	for _, e := range entities {
		if e.Type != "mention" {
			continue
		}
		if e.Offset < 0 || e.Length <= 0 || e.Offset+e.Length > len(text) {
			continue
		}
		mention := strings.ToLower(text[e.Offset : e.Offset+e.Length])
		if mention == needle {
			return true
		}
	}
	return false
}

func telegramAPIURL(token, method string) string {
	return fmt.Sprintf("%s/bot%s/%s", telegramAPIBase, token, method)
}

func telegramGetMe(ctx context.Context, token string) (string, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, telegramAPIURL(token, "getMe"), nil)
	if err != nil {
		return "", safeRobotHTTPError("telegram getMe request", err)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", safeRobotHTTPError("telegram getMe", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	var parsed telegramBotMe
	if err := json.Unmarshal(body, &parsed); err != nil {
		return "", err
	}
	if !parsed.OK {
		return "", fmt.Errorf("getMe failed: %s", parsed.Description)
	}
	return parsed.Result.Username, nil
}

// telegramGetUpdatesURL 构造长轮询请求地址。
// offset 为 0 时不传该参数（Telegram 会回传最早的未确认消息）；
// offset 为 -1 时只取最后一条（用于跳过历史积压）；offset > 0 则从该位置继续。
func telegramGetUpdatesURL(token string, offset int64) string {
	url := fmt.Sprintf("%s?timeout=%d&allowed_updates=%s", telegramAPIURL(token, "getUpdates"), telegramLongPollSec, `["message"]`)
	if offset != 0 {
		url += fmt.Sprintf("&offset=%d", offset)
	}
	return url
}

// telegramLatestUpdateURL 构造「取最后一条 update」的探测请求（不等待，立即返回）。
func telegramLatestUpdateURL(token string) string {
	return fmt.Sprintf("%s?timeout=0&allowed_updates=%s&offset=-1", telegramAPIURL(token, "getUpdates"), `["message"]`)
}

func telegramGetUpdates(ctx context.Context, client *http.Client, token string, offset int64) ([]telegramUpdate, error) {
	return telegramGetUpdatesWithURL(ctx, client, token, telegramGetUpdatesURL(token, offset))
}

func telegramGetUpdatesWithURL(ctx context.Context, client *http.Client, token, url string) ([]telegramUpdate, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, safeRobotHTTPError("telegram getUpdates request", err)
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, safeRobotHTTPError("telegram getUpdates", err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	var parsed telegramGetUpdatesResp
	if err := json.Unmarshal(body, &parsed); err != nil {
		return nil, err
	}
	if !parsed.OK {
		if parsed.Description != "" {
			return nil, fmt.Errorf("getUpdates: %s", parsed.Description)
		}
		return nil, fmt.Errorf("getUpdates failed without a description")
	}
	return parsed.Result, nil
}

// telegramEstablishStartOffset 用 offset=-1 探测一次，返回「历史积压之后的起点」。
// 没有积压时返回 0（后续轮询不传 offset，等新消息）；有积压时返回最后一条 update_id + 1，
// 该批次会被 Telegram 确认丢弃，机器人不会重播旧消息。
func telegramEstablishStartOffset(ctx context.Context, client *http.Client, token string) (int64, error) {
	updates, err := telegramGetUpdatesWithURL(ctx, client, token, telegramLatestUpdateURL(token))
	if err != nil {
		return 0, err
	}
	if len(updates) == 0 {
		return 0, nil
	}
	return int64(updates[len(updates)-1].UpdateID) + 1, nil
}

func telegramSendReply(ctx context.Context, client *http.Client, token string, chatID int64, reply string) error {
	reply = trimReply(reply)
	if reply == "" {
		return nil
	}
	for _, chunk := range splitTextChunks(reply, telegramMaxMessageRunes) {
		payload := map[string]interface{}{
			"chat_id": chatID,
			"text":    chunk,
		}
		body, _ := json.Marshal(payload)
		req, err := http.NewRequestWithContext(ctx, http.MethodPost, telegramAPIURL(token, "sendMessage"), bytes.NewReader(body))
		if err != nil {
			return safeRobotHTTPError("telegram sendMessage request", err)
		}
		req.Header.Set("Content-Type", "application/json")
		resp, err := client.Do(req)
		if err != nil {
			return safeRobotHTTPError("telegram sendMessage", err)
		}
		resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			return fmt.Errorf("sendMessage status %d", resp.StatusCode)
		}
	}
	return nil
}
