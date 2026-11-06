package robot

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

	"go.uber.org/zap"
)

// Telegram inline 按鈕（callback query）支援。
//
// 為什麼獨立成一個檔
// ------------------
// Telegram 的按鈕點擊是「callback_query」而不是訊息，資料形狀與既有訊息流程
// 完全不同。把這條路徑獨立出來，既不改動既有的訊息處理（那是線上服務的熱路徑），
// 也讓「按了按鈕要做什麼」這件事可以由上層決定，而不是硬寫在機器人套件裡。
//
// 三條安全規則
// ------------
//  1. 按鈕點擊一定會被確認（answerCallbackQuery），讓 Telegram 停止轉圈；
//     但「確認」不等於「執行」——真正的動作交給 CallbackHandler。
//  2. 沒有人實作 CallbackHandler 時，按鈕只會回一句「此按鈕未啟用」，
//     不會有任何副作用。
//  3. callback_data 只放短字串（放 grant ID 之類），不放任何憑證。

// telegramCallbackQuery 是 inline 按鈕的點擊事件。
type telegramCallbackQuery struct {
	// ID 是這次點擊的識別碼（用來回覆 Telegram）。
	ID string `json:"id"`
	// Data 是按鈕自帶的資料。
	Data string `json:"data"`
	// From 是點擊者。
	From *telegramUser `json:"from"`
	// Message 是被按的那則訊息（可能為 nil）。
	Message *telegramMessage `json:"message"`
}

// TelegramButton 是 inline 按鈕。
type TelegramButton struct {
	// Text 是按鈕上顯示的文字。
	Text string `json:"text"`
	// CallbackData 是點擊後回傳給伺服器的資料（Telegram 限制 64 bytes）。
	CallbackData string `json:"callback_data"`
}

// telegramCallbackAnswerMaxRunes 是按鈕回覆文字的上限（Telegram 的提示框上限）。
const telegramCallbackAnswerMaxRunes = 200

// handleTelegramCallback 處理一次 inline 按鈕點擊。
//
// 「點擊」與「動作」是分開的：按鈕一定會被確認（不然 Telegram 的圈會一直轉），
// 但真正的動作交給 CallbackHandler 決定。沒有實作時只回一句提示。
func handleTelegramCallback(ctx context.Context, client *http.Client, token string, cq *telegramCallbackQuery, callbacks []CallbackHandler, logger *zap.Logger) {
	if cq == nil {
		return
	}
	reply := "此按鈕未啟用"
	if len(callbacks) > 0 {
		userID := ""
		if cq.From != nil {
			userID = telegramSessionKey("private", 0, cq.From.ID)
		}
		for _, handler := range callbacks {
			if handler == nil {
				continue
			}
			reply = handler.HandleCallback(telegramPlatform, userID, cq.Data)
			break
		}
	}
	if err := telegramAnswerCallbackQuery(ctx, client, token, cq.ID, reply); err != nil {
		logger.Warn("Telegram 回覆按鈕失敗", zap.String("callback_id", cq.ID), zap.Error(err))
	}
}

// telegramAnswerCallbackQuery 確認一次按鈕點擊（把提示文字顯示在按鈕上方）。
func telegramAnswerCallbackQuery(ctx context.Context, client *http.Client, token, callbackID, text string) error {
	callbackID = strings.TrimSpace(callbackID)
	if callbackID == "" {
		return fmt.Errorf("callback_query id 為空")
	}
	payload := map[string]interface{}{
		"callback_query_id": callbackID,
	}
	trimmed := strings.TrimSpace(text)
	if trimmed != "" {
		payload["text"] = truncateRunes(trimmed, telegramCallbackAnswerMaxRunes)
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("序列化 answerCallbackQuery 失敗: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, telegramAPIURL(token, "answerCallbackQuery"), bytes.NewReader(body))
	if err != nil {
		return safeRobotHTTPError("telegram answerCallbackQuery request", err)
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return safeRobotHTTPError("telegram answerCallbackQuery", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("answerCallbackQuery status %d", resp.StatusCode)
	}
	return nil
}

// telegramSendMessageWithKeyboard 送出一則帶 inline 按鈕的訊息。
//
// 用獨立函式而不是改 telegramSendReply：既有回覆流程不帶按鈕，
// 兩者分開才能在不加載既有路徑的情況下加入按鈕能力。
func telegramSendMessageWithKeyboard(ctx context.Context, client *http.Client, token string, chatID int64, text string, buttons [][]TelegramButton) error {
	text = trimReply(text)
	if text == "" {
		return nil
	}
	payload := map[string]interface{}{
		"chat_id": chatID,
		"text":    text,
	}
	if len(buttons) > 0 {
		payload["reply_markup"] = map[string]interface{}{
			"inline_keyboard": buttons,
		}
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("序列化 sendMessage 失敗: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, telegramAPIURL(token, "sendMessage"), bytes.NewReader(body))
	if err != nil {
		return safeRobotHTTPError("telegram sendMessage request", err)
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return safeRobotHTTPError("telegram sendMessage", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("sendMessage status %d", resp.StatusCode)
	}
	return nil
}

// truncateRunes 依 rune 截斷字串（Telegram 以字元計數，不是位元組）。
func truncateRunes(text string, limit int) string {
	if limit <= 0 {
		return ""
	}
	runes := []rune(text)
	if len(runes) <= limit {
		return text
	}
	return string(runes[:limit])
}
