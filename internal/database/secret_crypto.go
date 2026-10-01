package database

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
	"path/filepath"
	"strings"
)

const credentialCipherPrefix = "enc:v1:"

type credentialCipher struct {
	aead cipher.AEAD
}

func newCredentialCipher(dbPath string) (*credentialCipher, error) {
	keyText := strings.TrimSpace(os.Getenv("JYSECAI_CREDENTIAL_KEY"))
	if keyText == "" {
		keyText = strings.TrimSpace(os.Getenv("JYSSECAI_CREDENTIAL_KEY"))
	}
	var key []byte
	var err error
	if keyText != "" {
		key, err = decodeCredentialKey(keyText)
	} else {
		key, err = loadOrCreateCredentialKey(dbPath + ".key")
	}
	if err != nil {
		return nil, err
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("initialize credential cipher: %w", err)
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("initialize credential GCM: %w", err)
	}
	return &credentialCipher{aead: aead}, nil
}

func decodeCredentialKey(value string) ([]byte, error) {
	value = strings.TrimSpace(value)
	decoders := []func(string) ([]byte, error){
		base64.StdEncoding.DecodeString,
		base64.RawStdEncoding.DecodeString,
		hex.DecodeString,
	}
	for _, decode := range decoders {
		if key, err := decode(value); err == nil && len(key) == 32 {
			return key, nil
		}
	}
	return nil, errors.New("JYSECAI_CREDENTIAL_KEY must encode exactly 32 bytes (base64 or hex)")
}

func loadOrCreateCredentialKey(path string) ([]byte, error) {
	if data, err := os.ReadFile(path); err == nil {
		return decodeCredentialKey(string(data))
	} else if !os.IsNotExist(err) {
		return nil, fmt.Errorf("read credential key: %w", err)
	}

	key := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, key); err != nil {
		return nil, fmt.Errorf("generate credential key: %w", err)
	}
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
	if err != nil {
		if os.IsExist(err) {
			data, readErr := os.ReadFile(path)
			if readErr != nil {
				return nil, fmt.Errorf("read concurrently created credential key: %w", readErr)
			}
			return decodeCredentialKey(string(data))
		}
		return nil, fmt.Errorf("create credential key: %w", err)
	}
	ok := false
	defer func() {
		_ = f.Close()
		if !ok {
			_ = os.Remove(path)
		}
	}()
	encoded := base64.StdEncoding.EncodeToString(key) + "\n"
	if _, err := f.WriteString(encoded); err != nil {
		_ = f.Close()
		return nil, fmt.Errorf("write credential key: %w", err)
	}
	if err := f.Sync(); err != nil {
		_ = f.Close()
		return nil, fmt.Errorf("sync credential key: %w", err)
	}
	if err := f.Close(); err != nil {
		return nil, fmt.Errorf("close credential key: %w", err)
	}
	// Sync the parent directory as well. f.Sync() only flushes the file's data
	// blocks; the directory entry that makes the new file visible can still be
	// lost on power failure. Without this, a crash here can leave the database
	// holding AES-GCM ciphertext whose key never reached disk, permanently
	// locking every stored credential.
	if err := syncParentDir(path); err != nil {
		return nil, err
	}
	ok = true
	return key, nil
}

// syncParentDir fsyncs the directory containing path so a newly created file's
// directory entry is durable. It is best-effort on platforms and filesystem
// drivers that reject directory sync (notably Windows, where os.Open on a
// directory fails); a failure there is not fatal because the Windows
// filesystems this project targets already guarantee directory-entry durability.
func syncParentDir(path string) error {
	dir := filepath.Dir(path)
	d, err := os.Open(dir)
	if err != nil {
		if isDirectorySyncUnsupported(err) {
			return nil
		}
		return fmt.Errorf("open parent directory for sync: %w", err)
	}
	defer d.Close()
	if err := d.Sync(); err != nil && !isDirectorySyncUnsupported(err) {
		return fmt.Errorf("sync parent directory: %w", err)
	}
	return nil
}

// isDirectorySyncUnsupported reports whether the error indicates the platform
// cannot fsync a directory handle rather than a real I/O failure.
func isDirectorySyncUnsupported(err error) bool {
	if err == nil {
		return false
	}
	if errors.Is(err, os.ErrInvalid) || errors.Is(err, os.ErrPermission) {
		return true
	}
	// Windows returns ERROR_INVALID_HANDLE / ERROR_ACCESS_DENIED for a
	// directory handle passed to FlushFileBuffers; syscall.EINVAL is the
	// portable form of the same condition.
	msg := strings.ToLower(err.Error())
	return strings.Contains(msg, "invalid handle") ||
		strings.Contains(msg, "access is denied") ||
		strings.Contains(msg, "incorrect function")
}

func (c *credentialCipher) encrypt(value string) (string, error) {
	if value == "" {
		return "", nil
	}
	if strings.HasPrefix(value, credentialCipherPrefix) {
		if _, err := c.decrypt(value); err != nil {
			return "", err
		}
		return value, nil
	}
	nonce := make([]byte, c.aead.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", err
	}
	sealed := c.aead.Seal(nil, nonce, []byte(value), nil)
	payload := append(nonce, sealed...)
	return credentialCipherPrefix + base64.RawStdEncoding.EncodeToString(payload), nil
}

func (c *credentialCipher) decrypt(value string) (string, error) {
	if value == "" || !strings.HasPrefix(value, credentialCipherPrefix) {
		return value, nil
	}
	payload, err := base64.RawStdEncoding.DecodeString(strings.TrimPrefix(value, credentialCipherPrefix))
	if err != nil {
		return "", fmt.Errorf("decode encrypted credential: %w", err)
	}
	if len(payload) < c.aead.NonceSize() {
		return "", errors.New("encrypted credential is truncated")
	}
	nonce, ciphertext := payload[:c.aead.NonceSize()], payload[c.aead.NonceSize():]
	plain, err := c.aead.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		// A wrong key and a corrupted row are indistinguishable to AES-GCM, but
		// the operator-facing remedy differs completely. Name both causes so a
		// lost JYSSECAI_CREDENTIAL_KEY is not mistaken for data corruption.
		return "", fmt.Errorf(
			"decrypt credential: %w (the stored value is encrypted but does not "+
				"match the current credential key; either %s points at a different "+
				"key than the one used to write this row, or the key file was lost — "+
				"restore the same key to read existing credentials)",
			err, "JYSECAI_CREDENTIAL_KEY")
	}
	return string(plain), nil
}

func (db *DB) encryptCredential(value string) (string, error) {
	if db == nil || db.credentialCipher == nil {
		return "", errors.New("credential cipher unavailable")
	}
	return db.credentialCipher.encrypt(value)
}

func (db *DB) decryptCredential(value string) (string, error) {
	if db == nil || db.credentialCipher == nil {
		return "", errors.New("credential cipher unavailable")
	}
	return db.credentialCipher.decrypt(value)
}

func (db *DB) migrateCredentialEncryption() error {
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	rows, err := tx.Query(`SELECT id, encryption_key, implant_token FROM c2_listeners`)
	if err != nil {
		return err
	}
	type c2CredentialRow struct{ id, key, token string }
	var listeners []c2CredentialRow
	for rows.Next() {
		var row c2CredentialRow
		if err := rows.Scan(&row.id, &row.key, &row.token); err != nil {
			_ = rows.Close()
			return err
		}
		listeners = append(listeners, row)
	}
	if err := rows.Close(); err != nil {
		return err
	}
	for _, row := range listeners {
		key, err := db.encryptCredential(row.key)
		if err != nil {
			return fmt.Errorf("encrypt c2 listener %s key: %w", row.id, err)
		}
		token, err := db.encryptCredential(row.token)
		if err != nil {
			return fmt.Errorf("encrypt c2 listener %s token: %w", row.id, err)
		}
		if key != row.key || token != row.token {
			if _, err := tx.Exec(`UPDATE c2_listeners SET encryption_key = ?, implant_token = ? WHERE id = ?`, key, token, row.id); err != nil {
				return err
			}
		}
	}

	rows, err = tx.Query(`SELECT id, password FROM webshell_connections`)
	if err != nil {
		return err
	}
	type webshellCredentialRow struct{ id, password string }
	var webshells []webshellCredentialRow
	for rows.Next() {
		var row webshellCredentialRow
		if err := rows.Scan(&row.id, &row.password); err != nil {
			_ = rows.Close()
			return err
		}
		webshells = append(webshells, row)
	}
	if err := rows.Close(); err != nil {
		return err
	}
	for _, row := range webshells {
		password, err := db.encryptCredential(row.password)
		if err != nil {
			return fmt.Errorf("encrypt webshell %s password: %w", row.id, err)
		}
		if password != row.password {
			if _, err := tx.Exec(`UPDATE webshell_connections SET password = ? WHERE id = ?`, password, row.id); err != nil {
				return err
			}
		}
	}
	return tx.Commit()
}
