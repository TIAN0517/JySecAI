package robot

import (
	"context"
	"fmt"
	"strconv"
	"strings"

	"jysecai/internal/config"
)

// SendProactiveButtons 主動推播帶 inline 按鈕的訊息（目前支援 telegram）。
//
// 與 SendProactive 的差別只有「多一排按鈕」，但用途差很多：
// 純文字推播只能讓人「知道有件事」，按鈕才能讓人「按一下就處理掉」。
// 這正是授權券核准需要的互動——人按一次就轉成生效，不必再回平台操作。
//
// 其他平台（slack／discord／wecom／lark）尚未支援 inline 按鈕，
// 會明確回錯而不是默默降級成純文字（默默降級會讓人以為按鈕生效了）。
func SendProactiveButtons(ctx context.Context, cfg config.RobotsConfig, platform, externalUserID, message string, buttons [][]TelegramButton) error {
	platform = strings.ToLower(strings.TrimSpace(platform))
	userID := robotIdentityUserPart(externalUserID)
	if userID == "" {
		return fmt.Errorf("invalid robot recipient")
	}
	switch platform {
	case "telegram":
		if !cfg.Telegram.Enabled || strings.TrimSpace(cfg.Telegram.BotToken) == "" {
			return fmt.Errorf("telegram is not configured")
		}
		id, err := strconv.ParseInt(userID, 10, 64)
		if err != nil {
			return fmt.Errorf("invalid telegram user id: %w", err)
		}
		return telegramSendMessageWithKeyboard(ctx, nilSafeHTTPClient(), strings.TrimSpace(cfg.Telegram.BotToken), id, message, buttons)
	default:
		return fmt.Errorf("platform %s does not support inline buttons yet", platform)
	}
}
