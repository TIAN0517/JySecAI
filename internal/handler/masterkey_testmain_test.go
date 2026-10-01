package handler

import (
	"os"
	"testing"
)

// TestMain 為整個測試套件注入固定的測試主金鑰。
//
// internal/secretstore 對缺少 JY_SECMASTER_KEY 的情況是 fail closed 的
// （這是刻意的：絕不回退到明文寫入）。測試需要走的是與正式環境相同的
// 加密路徑，因此在此設定一把確定性的金鑰，而不是繞過加密。
func TestMain(m *testing.M) {
	// 這是公開的測試用固定值，不是任何環境的正式金鑰。
	const testMasterKey = "0000000000000000000000000000000000000000000000000000000000000001"
	if _, ok := os.LookupEnv("JY_SECMASTER_KEY"); !ok {
		if err := os.Setenv("JY_SECMASTER_KEY", testMasterKey); err != nil {
			panic("設定 JY_SECMASTER_KEY 失敗: " + err.Error())
		}
	}
	os.Exit(m.Run())
}
