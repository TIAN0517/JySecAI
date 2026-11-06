package robot

// MessageHandler 供飞书/钉钉长连接调用的消息处理接口（由 handler.RobotHandler 实现）
type MessageHandler interface {
	HandleMessage(platform, userID, text string) string
}

// CallbackHandler 處理 inline 按鈕點擊（目前只有 telegram 支援）。
//
// 這是選用介面：沒有實作時按鈕點擊只會被確認（answerCallbackQuery）而不做動作，
// 所以其他機器人平台不需要改動既有流程。
type CallbackHandler interface {
	// HandleCallback 處理一次按鈕點擊，回傳要顯示給使用者的短訊息。
	HandleCallback(platform, userID, callbackData string) string
}
