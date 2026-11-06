package handler

import (
	"testing"

	"jysecai/internal/config"
)

func TestRobotSecretsMaskedAndPreservedOnUpdate(t *testing.T) {
	original := config.RobotsConfig{}
	original.Wechat.BotToken = "wechat-secret"
	original.Wecom.Token = "wecom-token"
	original.Wecom.EncodingAESKey = "wecom-aes"
	original.Wecom.Secret = "wecom-secret"
	original.Dingtalk.ClientSecret = "ding-secret"
	original.Lark.AppSecret = "lark-secret"
	original.Lark.VerifyToken = "lark-verify"
	original.Telegram.BotToken = "telegram-secret"
	original.Slack.BotToken = "slack-bot"
	original.Slack.AppToken = "slack-app"
	original.Discord.BotToken = "discord-secret"
	original.QQ.ClientSecret = "qq-secret"

	masked := maskRobotSecrets(original)
	if masked.Wechat.BotToken != maskedConfigSecret || masked.Wecom.Secret != maskedConfigSecret || masked.QQ.ClientSecret != maskedConfigSecret {
		t.Fatalf("robot secrets were not masked: %#v", masked)
	}
	if masked.Wecom.CorpID != original.Wecom.CorpID {
		t.Fatal("non-secret robot settings must not be changed")
	}

	merged := mergeRobotSecrets(masked, original)
	if merged.Wechat.BotToken != original.Wechat.BotToken || merged.Wecom.EncodingAESKey != original.Wecom.EncodingAESKey || merged.Slack.AppToken != original.Slack.AppToken {
		t.Fatalf("masked secrets were not preserved: %#v", merged)
	}
	masked.Telegram.BotToken = "rotated-token"
	merged = mergeRobotSecrets(masked, original)
	if merged.Telegram.BotToken != "rotated-token" {
		t.Fatalf("explicit rotated token was not accepted: %q", merged.Telegram.BotToken)
	}
}
