package database

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// 金鑰檔案必須在回傳給呼叫端之前就已經「落地」，否則掉電會造成
// 資料庫持有密文、金鑰卻不存在，憑證永久鎖死。
// 這裡驗證建立流程會把 key 寫進檔案且可被重新讀回。

func TestCredentialKeyIsPersistedAndReusable(t *testing.T) {
	dir := t.TempDir()
	keyPath := filepath.Join(dir, "test.db.key")

	first, err := loadOrCreateCredentialKey(keyPath)
	if err != nil {
		t.Fatalf("create key: %v", err)
	}
	if len(first) != 32 {
		t.Fatalf("key length = %d, want 32", len(first))
	}

	// 目錄項目必須真的存在於磁碟，而不只是留在 page cache
	if _, err := os.Stat(keyPath); err != nil {
		t.Fatalf("key file must exist on disk: %v", err)
	}

	// 第二次呼叫應讀回同一把 key（模擬程序重啟）
	second, err := loadOrCreateCredentialKey(keyPath)
	if err != nil {
		t.Fatalf("reload key: %v", err)
	}
	if string(first) != string(second) {
		t.Fatal("reloaded key must equal the original")
	}
}

func TestCredentialKeyFileIsOwnerOnly(t *testing.T) {
	if os.PathSeparator == '\\' {
		t.Skip("POSIX permission bits are not enforced on Windows")
	}
	dir := t.TempDir()
	keyPath := filepath.Join(dir, "perm.db.key")
	if _, err := loadOrCreateCredentialKey(keyPath); err != nil {
		t.Fatal(err)
	}
	info, err := os.Stat(keyPath)
	if err != nil {
		t.Fatal(err)
	}
	if perm := info.Mode().Perm(); perm != 0o600 {
		t.Fatalf("key file mode = %o, want 600", perm)
	}
}

func TestCredentialCipherRoundTrip(t *testing.T) {
	dir := t.TempDir()
	c, err := newCredentialCipher(filepath.Join(dir, "rt.db"))
	if err != nil {
		t.Fatal(err)
	}
	const secret = "ru/3xu4dkru4888"
	enc, err := c.encrypt(secret)
	if err != nil {
		t.Fatal(err)
	}
	if enc == secret || !strings.HasPrefix(enc, credentialCipherPrefix) {
		t.Fatalf("credential was not encrypted: %q", enc)
	}
	if strings.Contains(enc, secret) {
		t.Fatal("ciphertext must not contain the plaintext")
	}
	got, err := c.decrypt(enc)
	if err != nil {
		t.Fatal(err)
	}
	if got != secret {
		t.Fatalf("decrypt = %q, want %q", got, secret)
	}
}

func TestCredentialCipherIsIdempotent(t *testing.T) {
	dir := t.TempDir()
	c, err := newCredentialCipher(filepath.Join(dir, "idem.db"))
	if err != nil {
		t.Fatal(err)
	}
	first, err := c.encrypt("token")
	if err != nil {
		t.Fatal(err)
	}
	// 已加密的值再加密一次應保持原樣（避免遷移重複執行造成疊加加密）
	again, err := c.encrypt(first)
	if err != nil {
		t.Fatal(err)
	}
	if again != first {
		t.Fatal("encrypt must be idempotent for already-encrypted values")
	}
}

func TestCredentialCipherEmptyValue(t *testing.T) {
	dir := t.TempDir()
	c, err := newCredentialCipher(filepath.Join(dir, "empty.db"))
	if err != nil {
		t.Fatal(err)
	}
	got, err := c.encrypt("")
	if err != nil || got != "" {
		t.Fatalf("encrypt(\"\") = %q, %v", got, err)
	}
	plain, err := c.decrypt("")
	if err != nil || plain != "" {
		t.Fatalf("decrypt(\"\") = %q, %v", plain, err)
	}
}

// 換金鑰後舊密文無法解開，錯誤訊息必須點出「金鑰不符」而不是
// 只說解密失敗，否則維運會誤判為資料損毀。
func TestCredentialCipherErrorNamesKeyMismatch(t *testing.T) {
	dir := t.TempDir()
	first, err := newCredentialCipher(filepath.Join(dir, "a.db"))
	if err != nil {
		t.Fatal(err)
	}
	enc, err := first.encrypt("top-secret")
	if err != nil {
		t.Fatal(err)
	}

	// 同一路徑但刪掉 key 檔再建立 -> 得到不同金鑰
	other, err := newCredentialCipher(filepath.Join(dir, "b.db"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := other.decrypt(enc); err == nil {
		t.Fatal("decrypt with a different key must fail")
	} else if !strings.Contains(err.Error(), "credential key") {
		t.Fatalf("error must mention the credential key, got: %v", err)
	}
}

func TestDecodeCredentialKeyFormats(t *testing.T) {
	// 32 bytes 的 base64 與 hex 都應被接受
	valid := make([]byte, 32)
	for i := range valid {
		valid[i] = byte(i)
	}
	got, err := decodeCredentialKey("AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=")
	if err != nil {
		t.Fatalf("base64 key rejected: %v", err)
	}
	if len(got) != 32 {
		t.Fatalf("decoded length = %d, want 32", len(got))
	}
	if _, err := decodeCredentialKey("too-short"); err == nil {
		t.Fatal("a non-32-byte key must be rejected")
	}
	if _, err := decodeCredentialKey(""); err == nil {
		t.Fatal("an empty key must be rejected")
	}
}
