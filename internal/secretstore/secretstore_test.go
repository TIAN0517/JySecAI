package secretstore

import (
	"encoding/base64"
	"encoding/hex"
	"errors"
	"os"
	"strings"
	"testing"
)

const (
	testMasterKeyHex  = "0000000000000000000000000000000000000000000000000000000000000001"
	otherMasterKeyHex = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
)

// withMasterKey 設定主金鑰並清掉快取；測試結束後把快取清掉、環境變數還原。
// 清單單元測試不能平行執行（共用同一份環境變數），因此這裡刻意不呼叫 t.Parallel。
func withMasterKey(t *testing.T, value string) {
	t.Helper()
	t.Setenv(MasterKeyEnvVar, value)
	ResetForTesting()
	// t.Cleanup 以 LIFO 執行：先清快取，再由 t.Setenv 還原環境變數。
	t.Cleanup(ResetForTesting)
}

func TestEncryptDecryptRoundTrip(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)

	for _, plaintext := range []string{
		"a",
		"super-secret-webshell-password",
		"中文密碼與 emoji 🔑 也要能往返",
		strings.Repeat("x", 4096),
	} {
		sealed, err := Encrypt(plaintext)
		if err != nil {
			t.Fatalf("Encrypt(%q): %v", truncateForLog(plaintext), err)
		}
		if !IsEncrypted(sealed) {
			t.Fatalf("Encrypt(%q) 回傳的值缺少 %q 前綴：%q", truncateForLog(plaintext), CipherPrefix, truncateForLog(sealed))
		}
		if sealed == plaintext {
			t.Fatalf("Encrypt 回傳明文：%q", truncateForLog(sealed))
		}
		got, err := Decrypt(sealed)
		if err != nil {
			t.Fatalf("Decrypt: %v", err)
		}
		if got != plaintext {
			t.Errorf("往返後不一致：got %q, want %q", truncateForLog(got), truncateForLog(plaintext))
		}
	}
}

// 空字串代表「此欄位沒有值」，加密與解密都必須原樣往返。
func TestEmptyStringStaysEmpty(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)

	sealed, err := Encrypt("")
	if err != nil {
		t.Fatalf("Encrypt(\"\"): %v", err)
	}
	if sealed != "" {
		t.Errorf("Encrypt(\"\") = %q, want 空字串", sealed)
	}
	opened, err := Decrypt("")
	if err != nil {
		t.Fatalf("Decrypt(\"\"): %v", err)
	}
	if opened != "" {
		t.Errorf("Decrypt(\"\") = %q, want 空字串", opened)
	}
}

// 已加密的值不該被再疊一層密文，否則遷移重跑會產生多層巢狀。
func TestEncryptDoesNotDoubleSealCiphertext(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)

	first, err := Encrypt("value")
	if err != nil {
		t.Fatalf("Encrypt: %v", err)
	}
	second, err := Encrypt(first)
	if err != nil {
		t.Fatalf("Encrypt(ciphertext): %v", err)
	}
	if second != first {
		t.Fatalf("已加密的值被再次加密：%q → %q", truncateForLog(first), truncateForLog(second))
	}
	if got, err := Decrypt(second); err != nil || got != "value" {
		t.Fatalf("Decrypt = (%q, %v), want (\"value\", nil)", truncateForLog(got), err)
	}
}

func TestIsEncrypted(t *testing.T) {
	cases := map[string]bool{
		"":                             false,
		"plaintext":                    false,
		"v1:":                          true,
		"v1:YWJj":                      true,
		"v2:YWJj":                      false,
		"  v1:leading-space-is-not-it": false,
	}
	for input, want := range cases {
		if got := IsEncrypted(input); got != want {
			t.Errorf("IsEncrypted(%q) = %v, want %v", input, got, want)
		}
	}
}

// 遷移前的歷史資料是明文，Decrypt 必須原樣放行，讓服務在遷移完成前仍可運作。
func TestDecryptPassesThroughLegacyPlaintext(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)

	legacy := "legacy-plaintext-token"
	got, err := Decrypt(legacy)
	if err != nil {
		t.Fatalf("Decrypt(legacy): %v", err)
	}
	if got != legacy {
		t.Errorf("Decrypt(legacy) = %q, want %q", got, legacy)
	}
}

// 缺少主金鑰時必須 fail closed —— 絕不回退到明文寫入。
func TestEncryptFailsClosedWithoutMasterKey(t *testing.T) {
	withMasterKey(t, "")

	sealed, err := Encrypt("must-not-be-plaintext")
	if err == nil {
		t.Fatalf("缺少主金鑰時 Encrypt 竟成功：%q", truncateForLog(sealed))
	}
	if !errors.Is(err, ErrMasterKeyMissing) {
		t.Errorf("錯誤未指向 ErrMasterKeyMissing：%v", err)
	}
	if sealed != "" {
		t.Errorf("失敗時仍回傳了內容：%q", truncateForLog(sealed))
	}
	// 訊息必須可操作：明確講出環境變數名與產生方式。
	if !strings.Contains(err.Error(), MasterKeyEnvVar) {
		t.Errorf("錯誤訊息未提及 %s：%v", MasterKeyEnvVar, err)
	}
}

func TestEncryptFailsClosedWhenKeyMissingEntirely(t *testing.T) {
	t.Setenv(MasterKeyEnvVar, "")
	if err := os.Unsetenv(MasterKeyEnvVar); err != nil {
		t.Fatalf("Unsetenv: %v", err)
	}
	ResetForTesting()
	t.Cleanup(ResetForTesting)

	if _, err := Encrypt("x"); !errors.Is(err, ErrMasterKeyMissing) {
		t.Fatalf("完全未設定環境變數時的錯誤 = %v, want ErrMasterKeyMissing", err)
	}
}

func TestDecryptFailsClosedWithoutMasterKey(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)
	sealed, err := Encrypt("secret")
	if err != nil {
		t.Fatalf("Encrypt: %v", err)
	}
	// 模擬重啟後忘了設金鑰。
	withMasterKey(t, "")

	if got, err := Decrypt(sealed); err == nil {
		t.Fatalf("缺少主金鑰時 Decrypt 竟成功：%q", truncateForLog(got))
	}
}

func TestLoadMasterKeyRejectsNonHex(t *testing.T) {
	withMasterKey(t, strings.Repeat("z", 64))

	if _, err := LoadMasterKey(); err == nil {
		t.Fatal("非十六進位的金鑰竟被接受")
	} else if !strings.Contains(err.Error(), "十六進位") {
		t.Errorf("錯誤訊息未說明格式問題：%v", err)
	}
}

func TestLoadMasterKeyRejectsWrongLength(t *testing.T) {
	for _, raw := range []string{
		"",
		"abcd",
		strings.Repeat("ab", 31), // 62 hex chars = 31 bytes
		strings.Repeat("ab", 33), // 66 hex chars = 33 bytes
	} {
		withMasterKey(t, raw)
		if _, err := LoadMasterKey(); err == nil {
			t.Errorf("長度 %d 的金鑰竟被接受", len(raw)/2)
		}
	}
}

func TestLoadMasterKeyReturnsRaw32Bytes(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)

	key, err := LoadMasterKey()
	if err != nil {
		t.Fatalf("LoadMasterKey: %v", err)
	}
	if len(key) != 32 {
		t.Fatalf("金鑰長度 = %d, want 32", len(key))
	}
	want, _ := hex.DecodeString(testMasterKeyHex)
	if hex.EncodeToString(key) != hex.EncodeToString(want) {
		t.Errorf("金鑰內容不符：%x", key)
	}
}

// 金鑰載入後會快取；同一行程內不應因環境變數被竄改而換金鑰（否則
// 同一份資料庫會出現兩種加密結果）。
func TestLoadMasterKeyCachesUntilReset(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)
	first, err := LoadMasterKey()
	if err != nil {
		t.Fatalf("LoadMasterKey: %v", err)
	}

	if err := os.Setenv(MasterKeyEnvVar, otherMasterKeyHex); err != nil {
		t.Fatalf("Setenv: %v", err)
	}
	second, err := LoadMasterKey()
	if err != nil {
		t.Fatalf("LoadMasterKey(after change): %v", err)
	}
	if hex.EncodeToString(first) != hex.EncodeToString(second) {
		t.Error("金鑰未快取：環境變數改變後載入了不同的金鑰")
	}

	ResetForTesting()
	third, err := LoadMasterKey()
	if err != nil {
		t.Fatalf("LoadMasterKey(after reset): %v", err)
	}
	if hex.EncodeToString(third) != otherMasterKeyHex {
		t.Error("ResetForTesting 後未重新讀取環境變數")
	}
}

// 同一明文每次加密都必須產生不同密文（nonce 不可重複）。
func TestEncryptUsesFreshNoncePerCall(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)

	seen := make(map[string]bool)
	for i := 0; i < 32; i++ {
		sealed, err := Encrypt("same-plaintext-every-time")
		if err != nil {
			t.Fatalf("Encrypt: %v", err)
		}
		if seen[sealed] {
			t.Fatal("兩次加密產生完全相同的密文，nonce 可能重複")
		}
		seen[sealed] = true
	}
}

// 換錯金鑰時的錯誤訊息不得回傳任何明文片段。
func TestDecryptWithWrongKeyFailsWithoutLeakingPlaintext(t *testing.T) {
	const secret = "PLAINTEXT-SENTINEL-DO-NOT-LEAK"

	withMasterKey(t, testMasterKeyHex)
	sealed, err := Encrypt(secret)
	if err != nil {
		t.Fatalf("Encrypt: %v", err)
	}

	withMasterKey(t, otherMasterKeyHex)
	got, err := Decrypt(sealed)
	if err == nil {
		t.Fatalf("以錯誤金鑰解密竟成功：%q", got)
	}
	if strings.Contains(err.Error(), secret) {
		t.Errorf("錯誤訊息洩漏明文：%v", err)
	}
	if got != "" {
		t.Errorf("解密失敗卻回傳了內容：%q", truncateForLog(got))
	}
}

// 密文被竄改（GCM tag 驗證）時必須拒絕。
func TestDecryptRejectsTamperedCiphertext(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)

	sealed, err := Encrypt("tamper-me")
	if err != nil {
		t.Fatalf("Encrypt: %v", err)
	}
	raw, err := base64.StdEncoding.DecodeString(strings.TrimPrefix(sealed, CipherPrefix))
	if err != nil {
		t.Fatalf("DecodeString: %v", err)
	}
	raw[len(raw)-1] ^= 0x01 // 翻轉 tag 的最後一個 bit
	tampered := CipherPrefix + base64.StdEncoding.EncodeToString(raw)

	if got, err := Decrypt(tampered); err == nil {
		t.Fatalf("竄改過的密文竟解密成功：%q", got)
	}
}

func TestDecryptRejectsMalformedCiphertext(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)

	cases := map[string]string{
		"base64 損毀":   CipherPrefix + "!!!not-base64!!!",
		"長度不足（無 tag）": CipherPrefix + base64.StdEncoding.EncodeToString(make([]byte, 8)),
		"只有 nonce":    CipherPrefix + base64.StdEncoding.EncodeToString(make([]byte, 12)),
	}
	for name, sealed := range cases {
		if got, err := Decrypt(sealed); err == nil {
			t.Errorf("%s：竟解密成功：%q", name, truncateForLog(got))
		}
	}
}

// 密文不得以任何形式包含明文，且信封格式（nonce||ct+tag）必須成立。
func TestCiphertextEnvelopeShape(t *testing.T) {
	withMasterKey(t, testMasterKeyHex)

	const secret = "SENTINEL-PLAINTEXT-1234"
	sealed, err := Encrypt(secret)
	if err != nil {
		t.Fatalf("Encrypt: %v", err)
	}
	if strings.Contains(sealed, secret) {
		t.Fatal("密文包含明文")
	}
	raw, err := base64.StdEncoding.DecodeString(strings.TrimPrefix(sealed, CipherPrefix))
	if err != nil {
		t.Fatalf("DecodeString: %v", err)
	}
	// AES-GCM：12 bytes nonce + 密文 + 16 bytes tag。
	if len(raw) != 12+len(secret)+16 {
		t.Errorf("信封長度 = %d, want %d", len(raw), 12+len(secret)+16)
	}
}

// 測試輔助：避免把長的測試資料整段印進失敗訊息。
func truncateForLog(s string) string {
	if len(s) <= 48 {
		return s
	}
	return s[:48] + "…"
}
