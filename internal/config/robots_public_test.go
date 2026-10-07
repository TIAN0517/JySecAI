package config

import (
	"encoding/json"
	"reflect"
	"strings"
	"testing"
)

// secretFieldNameParts 命中任一段即視為憑證欄位。
// 測試用反射走訪 RobotsConfig，確保任何新增的憑證欄位只要名稱符合，
// 就必須被 Public() 遮罩 —— 避免日後新增平台時忘了加遮罩而再次外洩。
var secretFieldNameParts = []string{"token", "secret", "password", "key", "credential"}

// filledRobotsConfig 刻意把每個欄位都填上可辨識的假值，用來驗證遮罩涵蓋率。
// 回傳欄位名稱 → 假值。
func filledRobotsConfig() RobotsConfig {
	const v = "SENTINEL-SECRET-VALUE"
	return RobotsConfig{
		Session: RobotSessionConfig{StrictUserIdentity: boolPtr(true)},
		Wechat: RobotWechatConfig{
			Enabled: true, BotToken: v, ILinkBotID: v, ILinkUserID: v,
			BaseURL: v, BotType: v, BotAgent: v, GetUpdatesBuf: v,
		},
		Wecom: RobotWecomConfig{
			Enabled: true, Token: v, EncodingAESKey: v, CorpID: v, Secret: v, AgentID: 1,
		},
		Dingtalk: RobotDingtalkConfig{
			Enabled: true, ClientID: v, ClientSecret: v, AllowConversationIDFallback: true,
		},
		Lark: RobotLarkConfig{
			Enabled: true, AppID: v, AppSecret: v, VerifyToken: v, AllowChatIDFallback: true,
		},
		Telegram: RobotTelegramConfig{
			Enabled: true, BotToken: v, BotUsername: v, AllowGroupMessages: true, UpdateOffset: 7,
		},
		Slack:   RobotSlackConfig{Enabled: true, BotToken: v, AppToken: v},
		Discord: RobotDiscordConfig{Enabled: true, BotToken: v, AllowGuildMessages: true},
		QQ:      RobotQQConfig{Enabled: true, AppID: v, ClientSecret: v, Sandbox: true},
	}
}

func boolPtr(b bool) *bool { return &b }

func isSecretField(name string) bool {
	lower := strings.ToLower(name)
	for _, part := range secretFieldNameParts {
		if strings.Contains(lower, part) {
			return true
		}
	}
	return false
}

// walkStrings 走訪任意結構體的所有 string 欄位（含巢狀 struct 與 slice 元素）。
func walkStrings(t *testing.T, v reflect.Value, path string, visit func(fieldPath, value string)) {
	t.Helper()
	switch v.Kind() {
	case reflect.String:
		visit(path, v.String())
	case reflect.Struct:
		typ := v.Type()
		for i := 0; i < v.NumField(); i++ {
			f := typ.Field(i)
			if f.PkgPath != "" { // unexported
				continue
			}
			walkStrings(t, v.Field(i), path+"."+f.Name, visit)
		}
	case reflect.Slice, reflect.Array:
		for i := 0; i < v.Len(); i++ {
			walkStrings(t, v.Index(i), path+"[]", visit)
		}
	}
}

// TestRobotsPublicRedactsEverySecretField 是本項修補的核心回歸釘選：
// RobotsConfig 內所有名稱含 token/secret/password/key/credential 的欄位，
// 在 Public() 之後都不得保留原值。
func TestRobotsPublicRedactsEverySecretField(t *testing.T) {
	full := filledRobotsConfig()
	redacted := full.Public()

	walkStrings(t, reflect.ValueOf(full), "Robots", func(fieldPath, original string) {
		fieldName := fieldPath[strings.LastIndex(fieldPath, ".")+1:]
		if !isSecretField(fieldName) {
			return
		}
		if original == "" {
			return
		}
		got := reflect.ValueOf(redacted).FieldByName(strings.Split(fieldPath, ".")[1]).FieldByName(fieldName)
		if got.Kind() != reflect.String {
			t.Fatalf("%s 預期為 string，實際 %s", fieldPath, got.Kind())
		}
		if value := got.String(); value != RedactedSecretPlaceholder {
			t.Errorf("憑證欄位 %s 未被遮罩：Public() 回傳 %q，期望 %q", fieldPath, value, RedactedSecretPlaceholder)
		}
	})
}

// TestRobotsPublicKeepsNonSecretFields 確認遮罩沒有過度：非憑證欄位（平台 ID、
// 啟用旗標、授權策略）必須原樣保留，否則設定頁會失去可用性。
func TestRobotsPublicKeepsNonSecretFields(t *testing.T) {
	full := filledRobotsConfig()
	redacted := full.Public()

	checks := []struct {
		name string
		got  interface{}
		want interface{}
	}{
		{"telegram.enabled", redacted.Telegram.Enabled, true},
		{"telegram.bot_username", redacted.Telegram.BotUsername, "SENTINEL-SECRET-VALUE"},
		{"telegram.update_offset", redacted.Telegram.UpdateOffset, int64(7)},
		{"wecom.corp_id", redacted.Wecom.CorpID, "SENTINEL-SECRET-VALUE"},
		{"wecom.agent_id", redacted.Wecom.AgentID, int64(1)},
		{"wecom.enabled", redacted.Wecom.Enabled, true},
		{"slack.enabled", redacted.Slack.Enabled, true},
		{"qq.sandbox", redacted.QQ.Sandbox, true},
		{"wechat.ilink_bot_id", redacted.Wechat.ILinkBotID, "SENTINEL-SECRET-VALUE"},
	}
	for _, c := range checks {
		if c.got != c.want {
			t.Errorf("非憑證欄位 %s 被過度遮罩：got %v, want %v", c.name, c.got, c.want)
		}
	}
}

// TestRobotsPublicEmptySecretStaysEmpty 未設定的憑證必須維持空字串，不能填入 "***"，
// 否則前端會把「未設定」誤判為「已設定」。
func TestRobotsPublicEmptySecretStaysEmpty(t *testing.T) {
	redacted := RobotsConfig{}.Public()
	if redacted.Telegram.BotToken != "" {
		t.Errorf("未設定的 Telegram token 應保持空字串，實際 %q", redacted.Telegram.BotToken)
	}
	if redacted.Slack.AppToken != "" {
		t.Errorf("未設定的 Slack app token 應保持空字串，實際 %q", redacted.Slack.AppToken)
	}
}

// TestRobotsPublicJSONCarriesNoSecret 端到端驗證：Public() 的結果序列化後，
// JSON 內不得出現任何原始憑證值。
func TestRobotsPublicJSONCarriesNoSecret(t *testing.T) {
	const secret = "123456:SUPER-SECRET-BOT-TOKEN"
	full := filledRobotsConfig()
	full.Telegram.BotToken = secret

	raw, err := json.Marshal(full.Public())
	if err != nil {
		t.Fatalf("序列化失敗: %v", err)
	}
	if strings.Contains(string(raw), secret) {
		t.Fatalf("Public() 的 JSON 仍含原始憑證：%s", string(raw))
	}
	if !strings.Contains(string(raw), RedactedSecretPlaceholder) {
		t.Fatalf("Public() 的 JSON 未含遮罩佔位符，遮罩可能未生效：%s", string(raw))
	}
}

// TestRobotsWithPreservedSecretsRoundTrip 模擬設定頁的讀-改-寫流程：
// GET 拿到遮罩值 → 使用者只改 Enabled → PUT 送回。原有憑證必須完好保留。
func TestRobotsWithPreservedSecretsRoundTrip(t *testing.T) {
	existing := RobotsConfig{
		Telegram: RobotTelegramConfig{Enabled: false, BotToken: "real-telegram-token"},
		Slack:    RobotSlackConfig{Enabled: true, BotToken: "xoxb-real", AppToken: "xapp-real"},
		Wecom:    RobotWecomConfig{Enabled: true, Token: "real-wecom-token", Secret: "real-wecom-secret", EncodingAESKey: "real-aes"},
	}

	// 前端拿到的就是 Public() 的輸出
	echoed := existing.Public()
	// 使用者只改了 Telegram 的啟用狀態
	echoed.Telegram.Enabled = true
	// 原樣送回
	merged := existing.WithPreservedSecrets(echoed)

	if merged.Telegram.BotToken != "real-telegram-token" {
		t.Errorf("Telegram token 被遮罩值覆蓋：%q", merged.Telegram.BotToken)
	}
	if merged.Slack.BotToken != "xoxb-real" {
		t.Errorf("Slack bot token 被遮罩值覆蓋：%q", merged.Slack.BotToken)
	}
	if merged.Slack.AppToken != "xapp-real" {
		t.Errorf("Slack app token 被遮罩值覆蓋：%q", merged.Slack.AppToken)
	}
	if merged.Wecom.Token != "real-wecom-token" {
		t.Errorf("WeCom token 被遮罩值覆蓋：%q", merged.Wecom.Token)
	}
	if merged.Wecom.Secret != "real-wecom-secret" {
		t.Errorf("WeCom secret 被遮罩值覆蓋：%q", merged.Wecom.Secret)
	}
	if merged.Wecom.EncodingAESKey != "real-aes" {
		t.Errorf("WeCom encoding AES key 被遮罩值覆蓋：%q", merged.Wecom.EncodingAESKey)
	}
	// 使用者的實際修改必須生效
	if !merged.Telegram.Enabled {
		t.Error("使用者的啟用狀態修改未生效")
	}
}

// TestRobotsWithPreservedSecretsAllowsRealUpdate 確認遮罩機制不會擋下真實的憑證更新。
func TestRobotsWithPreservedSecretsAllowsRealUpdate(t *testing.T) {
	existing := RobotsConfig{
		Telegram: RobotTelegramConfig{Enabled: true, BotToken: "old-token"},
	}
	incoming := RobotsConfig{
		Telegram: RobotTelegramConfig{Enabled: true, BotToken: "brand-new-token"},
	}
	merged := existing.WithPreservedSecrets(incoming)
	if merged.Telegram.BotToken != "brand-new-token" {
		t.Errorf("新的憑證值應被接受，實際 %q", merged.Telegram.BotToken)
	}
}

// TestRobotsWithPreservedSecretsAllowsClear 確認使用者仍能主動清空憑證（傳空字串即可），
// 不會被還原邏輯擋下。
func TestRobotsWithPreservedSecretsAllowsClear(t *testing.T) {
	existing := RobotsConfig{
		Telegram: RobotTelegramConfig{Enabled: true, BotToken: "old-token"},
	}
	incoming := RobotsConfig{
		Telegram: RobotTelegramConfig{Enabled: false, BotToken: ""},
	}
	merged := existing.WithPreservedSecrets(incoming)
	if merged.Telegram.BotToken != "" {
		t.Errorf("主動清空憑證應被允許，實際 %q", merged.Telegram.BotToken)
	}
}
