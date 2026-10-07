package config

// RedactedSecretPlaceholder 是設定 API 回傳給前端時，用來表示「該欄位有值但已遮罩」的佔位字串。
//
// 與 C2 listener handler 的處理一致（internal/handler/c2.go 對 encryption_key /
// implant_token 的處理）：保留欄位本身與「是否已設定」的資訊，但不洩漏實際值。
const RedactedSecretPlaceholder = "***"

// Public 回傳適合透過 API 序列化給前端的機器人設定副本。
//
// 背景：GET /api/config 只需要 config:read 權限，而 RobotsConfig 的欄位帶有
// json:"bot_token" / json:"app_secret" 等標籤，會把第三方機器人憑證完整回傳。
// 持有該憑證等同於完全接管對應的機器人帳號（可讀取機器人收發訊息、以機器人身分發言），
// 遠超「檢視系統設定」所需的權限。
//
// 這裡只遮罩憑證類欄位；Enabled、AppID、Auth 授權策略等非機密欄位維持原值，
// 讓設定頁仍能正確顯示各平台的啟用狀態與綁定身分。
func (c RobotsConfig) Public() RobotsConfig {
	out := c

	// 微信 iLink
	out.Wechat.BotToken = maskIfSet(c.Wechat.BotToken)
	out.Wechat.GetUpdatesBuf = maskIfSet(c.Wechat.GetUpdatesBuf)

	// 企業微信
	out.Wecom.Token = maskIfSet(c.Wecom.Token)
	out.Wecom.EncodingAESKey = maskIfSet(c.Wecom.EncodingAESKey)
	out.Wecom.Secret = maskIfSet(c.Wecom.Secret)

	// 钉钉
	out.Dingtalk.ClientSecret = maskIfSet(c.Dingtalk.ClientSecret)

	// 飞书
	out.Lark.AppSecret = maskIfSet(c.Lark.AppSecret)
	out.Lark.VerifyToken = maskIfSet(c.Lark.VerifyToken)

	// Telegram
	out.Telegram.BotToken = maskIfSet(c.Telegram.BotToken)

	// Slack
	out.Slack.BotToken = maskIfSet(c.Slack.BotToken)
	out.Slack.AppToken = maskIfSet(c.Slack.AppToken)

	// Discord
	out.Discord.BotToken = maskIfSet(c.Discord.BotToken)

	// QQ
	out.QQ.ClientSecret = maskIfSet(c.QQ.ClientSecret)

	return out
}

func maskIfSet(v string) string {
	if v == "" {
		return ""
	}
	return RedactedSecretPlaceholder
}

// WithPreservedSecrets 把前端回傳的設定與現有設定合併：凡是被遮罩佔位符
// RedactedSecretPlaceholder 佔據的憑證欄位，一律沿用 existing 的原值。
//
// 這是 Public() 的必要配套。設定頁的讀-改-寫流程會把 GET /api/config 的回應
// 原樣送回 PUT /api/config；若不還原遮罩值，原本已設定的機器人憑證會被
// "***" 覆蓋，機器人將永久失效。
func (c RobotsConfig) WithPreservedSecrets(incoming RobotsConfig) RobotsConfig {
	out := incoming

	if out.Wechat.BotToken == RedactedSecretPlaceholder {
		out.Wechat.BotToken = c.Wechat.BotToken
	}
	if out.Wechat.GetUpdatesBuf == RedactedSecretPlaceholder {
		out.Wechat.GetUpdatesBuf = c.Wechat.GetUpdatesBuf
	}

	if out.Wecom.Token == RedactedSecretPlaceholder {
		out.Wecom.Token = c.Wecom.Token
	}
	if out.Wecom.EncodingAESKey == RedactedSecretPlaceholder {
		out.Wecom.EncodingAESKey = c.Wecom.EncodingAESKey
	}
	if out.Wecom.Secret == RedactedSecretPlaceholder {
		out.Wecom.Secret = c.Wecom.Secret
	}

	if out.Dingtalk.ClientSecret == RedactedSecretPlaceholder {
		out.Dingtalk.ClientSecret = c.Dingtalk.ClientSecret
	}

	if out.Lark.AppSecret == RedactedSecretPlaceholder {
		out.Lark.AppSecret = c.Lark.AppSecret
	}
	if out.Lark.VerifyToken == RedactedSecretPlaceholder {
		out.Lark.VerifyToken = c.Lark.VerifyToken
	}

	if out.Telegram.BotToken == RedactedSecretPlaceholder {
		out.Telegram.BotToken = c.Telegram.BotToken
	}

	if out.Slack.BotToken == RedactedSecretPlaceholder {
		out.Slack.BotToken = c.Slack.BotToken
	}
	if out.Slack.AppToken == RedactedSecretPlaceholder {
		out.Slack.AppToken = c.Slack.AppToken
	}

	if out.Discord.BotToken == RedactedSecretPlaceholder {
		out.Discord.BotToken = c.Discord.BotToken
	}

	if out.QQ.ClientSecret == RedactedSecretPlaceholder {
		out.QQ.ClientSecret = c.QQ.ClientSecret
	}

	return out
}
