package logger

import (
	"bytes"
	"encoding/json"
	"testing"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"jysecai/internal/logger/zhconv"
)

func TestS2TMap(t *testing.T) {
	cases := map[string]string{
		"载": "載", "资": "資", "产": "產",
		"连": "連", "结": "結", "描": "描",
		"全": "全", "优": "優", "化": "化",
	}
	for s, want := range cases {
		if got := zhconv.S2T(s); got != want {
			t.Errorf("S2T(%q) = %q, want %q", s, got, want)
		}
	}
}

func TestS2TEncoder(t *testing.T) {
	var buf bytes.Buffer
	enc := newS2TEncoder(zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()))
	core := zapcore.NewCore(enc, zapcore.AddSync(&buf), zapcore.InfoLevel)
	log := zap.New(core)
	log.Info("正在加载资产配置", zap.String("status", "连接成功"))

	var out map[string]interface{}
	if err := json.Unmarshal(buf.Bytes(), &out); err != nil {
		t.Fatalf("unmarshal log json: %v", err)
	}
	if out["msg"] != "正在加載資產配置" {
		t.Errorf("msg = %v, want 正在加載資產配置", out["msg"])
	}
}
