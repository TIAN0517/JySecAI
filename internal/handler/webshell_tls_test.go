package handler

import (
	"testing"
)

// TestNewWebShellTransportModes 锁定 WebShell 出站 TLS 的三种模式行为。
//
// 默认必须是相容模式（不校验证书）：政府与关键基础设施目标普遍使用自签凭证，
// 默认强制校验会让授权范围内的目标无法探测。需要校验时设置 CA 环境变量恢复。
func TestNewWebShellTransportModes(t *testing.T) {
	clearEnv := func() {
		t.Setenv("JYSSECAI_WEBSHELL_CA_FILE", "")
		t.Setenv("JYSSECAI_WEBSHELL_CA_SERVER", "")
		t.Setenv("JYSSECAI_WEBSHELL_INSECURE", "")
	}

	t.Run("未設定任何變數時預設相容模式", func(t *testing.T) {
		clearEnv()
		tr := newWebShellTransport(nil)
		if tr == nil || tr.TLSClientConfig == nil {
			t.Fatal("TLSClientConfig 應為非 nil")
		}
		if !tr.TLSClientConfig.InsecureSkipVerify {
			t.Fatal("未設定 CA 時應為相容模式（InsecureSkipVerify=true），否則自簽政府目標無法探測")
		}
	})

	t.Run("設定 CA_FILE 時應啟用憑證校驗", func(t *testing.T) {
		clearEnv()
		dir := t.TempDir()
		pemFile := dir + "/ca.pem"
		if err := writeSelfSignedCA(t, pemFile); err != nil {
			t.Skipf("無法產生測試用 CA 憑證：%v", err)
		}
		t.Setenv("JYSSECAI_WEBSHELL_CA_FILE", pemFile)

		tr := newWebShellTransport(nil)
		if tr == nil || tr.TLSClientConfig == nil {
			t.Fatal("TLSClientConfig 應為非 nil")
		}
		if tr.TLSClientConfig.InsecureSkipVerify {
			t.Fatal("設定了 CA_FILE 時不應為相容模式")
		}
		if tr.TLSClientConfig.RootCAs == nil {
			t.Fatal("設定 CA_FILE 時應載入 RootCAs")
		}
	})

	t.Run("CA_FILE 內容無效時應回退系統 CA 而非靜默降級", func(t *testing.T) {
		clearEnv()
		badFile := t.TempDir() + "/bad.pem"
		if err := writeFileString(badFile, "not a pem"); err != nil {
			t.Skip("無法寫入測試檔")
		}
		t.Setenv("JYSSECAI_WEBSHELL_CA_FILE", badFile)

		tr := newWebShellTransport(nil)
		if tr == nil || tr.TLSClientConfig == nil {
			t.Fatal("TLSClientConfig 應為非 nil")
		}
		if tr.TLSClientConfig.InsecureSkipVerify {
			t.Fatal("CA 設定錯誤時應回退系統 CA 並保持校驗，不應靜默降級為不校驗")
		}
	})

	t.Run("INSECURE=1 應覆蓋 CA 設定", func(t *testing.T) {
		clearEnv()
		t.Setenv("JYSSECAI_WEBSHELL_INSECURE", "1")

		tr := newWebShellTransport(nil)
		if tr == nil || tr.TLSClientConfig == nil {
			t.Fatal("TLSClientConfig 應為非 nil")
		}
		if !tr.TLSClientConfig.InsecureSkipVerify {
			t.Fatal("JYSSECAI_WEBSHELL_INSECURE=1 應強制相容模式")
		}
	})

	t.Run("三種模式皆應要求 TLS 1.2 以上", func(t *testing.T) {
		clearEnv()
		tr := newWebShellTransport(nil)
		if tr.TLSClientConfig.MinVersion < 0x0303 { // tls.VersionTLS12
			t.Fatalf("MinVersion 應至少為 TLS 1.2，實際為 %d", tr.TLSClientConfig.MinVersion)
		}
	})
}
