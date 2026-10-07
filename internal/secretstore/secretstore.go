// Package secretstore 提供資料庫敏感欄位的 at-rest 加密。
//
// 背景：c2_listeners.encryption_key / implant_token 與
// webshell_connections.password 原本以明文落盤。這些值等同於 C2 beacon
// 的偽造權限與目標主機的存取權，SQLite 檔案一旦外洩即全部失守。
//
// 金鑰來源：環境變數 JY_SECMASTER_KEY（64 個十六進位字元 = 32 bytes）。
// 金鑰本身永不入庫、不進版本庫、不寫入備份。
//
// 密文格式： "v1:" + base64(nonce(12) || ciphertext+tag(16))
// 前綴讓明文與密文可以並存於同一欄位，遷移可分批進行、可回滾。
package secretstore

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"os"
	"strings"
	"sync"
)

// MasterKeyEnvVar 存放主金鑰的環境變數名稱。
const MasterKeyEnvVar = "JY_SECMASTER_KEY"

// CipherPrefix 密文版本前綴。帶此前綴的值視為已加密。
const CipherPrefix = "v1:"

// ErrMasterKeyMissing 未設定 JY_SECMASTER_KEY，且目前確實需要保護機密欄位。
var ErrMasterKeyMissing = errors.New("secretstore: " + MasterKeyEnvVar + " 未設定")

var (
	loadMu    sync.Mutex
	loadedKey []byte
	loadedErr error
	loaded    bool
)

// LoadMasterKey 讀取並快取環境變數中的主金鑰。
//
// 呼叫端必須把錯誤往上傳：缺少金鑰時一律 fail closed，絕不回退到明文寫入。
func LoadMasterKey() ([]byte, error) {
	loadMu.Lock()
	defer loadMu.Unlock()
	if loaded {
		return loadedKey, loadedErr
	}
	raw := strings.TrimSpace(os.Getenv(MasterKeyEnvVar))
	if raw == "" {
		loadedErr = fmt.Errorf("%w：資料庫存在需要保護的機密欄位，但未提供主金鑰。請以 32 bytes（64 位十六進位）設定 %s 後重新啟動，例如 `openssl rand -hex 32`", ErrMasterKeyMissing, MasterKeyEnvVar)
		loaded = true
		return nil, loadedErr
	}
	key, err := hex.DecodeString(raw)
	if err != nil {
		loadedErr = fmt.Errorf("secretstore: %s 不是合法的十六進位字串: %w", MasterKeyEnvVar, err)
		loaded = true
		return nil, loadedErr
	}
	if len(key) != 32 {
		loadedErr = fmt.Errorf("secretstore: %s 長度必須為 32 bytes（64 位十六進位），目前為 %d bytes", MasterKeyEnvVar, len(key))
		loaded = true
		return nil, loadedErr
	}
	loadedKey = key
	loaded = true
	return loadedKey, nil
}

// ResetForTesting 清除金鑰快取。僅供測試在切換環境變數後重新載入。
func ResetForTesting() {
	loadMu.Lock()
	defer loadMu.Unlock()
	loadedKey, loadedErr, loaded = nil, nil, false
}

// IsEncrypted 判斷欄位值是否已是密文。
func IsEncrypted(v string) bool {
	return strings.HasPrefix(v, CipherPrefix)
}

// Encrypt 以主金鑰加密明文，回傳帶版本前綴的密文。
// 空字串原樣回傳（代表「此欄位沒有值」，不需加密）。
func Encrypt(plaintext string) (string, error) {
	if plaintext == "" {
		return "", nil
	}
	if IsEncrypted(plaintext) {
		// 已加密就不要再疊一層，避免遷移重跑時產生多層密文。
		return plaintext, nil
	}
	key, err := LoadMasterKey()
	if err != nil {
		return "", err
	}
	gcm, err := newGCM(key)
	if err != nil {
		return "", err
	}
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", fmt.Errorf("secretstore: 產生 nonce 失敗: %w", err)
	}
	ct := gcm.Seal(nil, nonce, []byte(plaintext), nil)
	return CipherPrefix + base64.StdEncoding.EncodeToString(append(nonce, ct...)), nil
}

// Decrypt 解密密文。若值尚未加密（遷移前的歷史資料），原樣回傳，
// 讓呼叫端可以在遷移完成前繼續運作。
func Decrypt(stored string) (string, error) {
	if stored == "" {
		return "", nil
	}
	if !IsEncrypted(stored) {
		return stored, nil
	}
	key, err := LoadMasterKey()
	if err != nil {
		return "", err
	}
	gcm, err := newGCM(key)
	if err != nil {
		return "", err
	}
	raw, err := base64.StdEncoding.DecodeString(strings.TrimPrefix(stored, CipherPrefix))
	if err != nil {
		return "", fmt.Errorf("secretstore: 密文 base64 格式錯誤: %w", err)
	}
	if len(raw) < gcm.NonceSize()+gcm.Overhead() {
		return "", fmt.Errorf("secretstore: 密文長度不足（%d bytes）", len(raw))
	}
	nonce, ct := raw[:gcm.NonceSize()], raw[gcm.NonceSize():]
	plain, err := gcm.Open(nil, nonce, ct, nil)
	if err != nil {
		// 可能是換過主金鑰。這裡不回傳任何明文片段，避免把密文內容
		// 當成錯誤訊息洩漏出去。
		return "", errors.New("secretstore: 解密失敗（主金鑰不符或密文已損毀）")
	}
	return string(plain), nil
}

func newGCM(key []byte) (cipher.AEAD, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("secretstore: 建立 AES cipher 失敗: %w", err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("secretstore: 建立 GCM 失敗: %w", err)
	}
	return gcm, nil
}
