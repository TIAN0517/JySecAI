package database

import (
	"path/filepath"
	"strings"
	"testing"
	"time"

	"go.uber.org/zap"
)

func TestSensitiveCredentialsEncryptedAtRestAndTransparent(t *testing.T) {
	t.Setenv("JYSECAI_CREDENTIAL_KEY", "")
	t.Setenv("JYSSECAI_CREDENTIAL_KEY", "")
	db, err := NewDB(filepath.Join(t.TempDir(), "secrets.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()

	listener := &C2Listener{
		ID: "l_secret", Name: "secret", Type: "http_beacon", BindHost: "127.0.0.1", BindPort: 8443,
		EncryptionKey: "listener-key-plaintext", ImplantToken: "implant-token-plaintext", CreatedAt: time.Now(),
	}
	if err := db.CreateC2Listener(listener); err != nil {
		t.Fatal(err)
	}
	webshell := &WebShellConnection{
		ID: "ws_secret", URL: "https://example.invalid/shell", Password: "webshell-password-plaintext",
		Type: "php", Method: "post", CreatedAt: time.Now(),
	}
	if err := db.CreateWebshellConnection(webshell); err != nil {
		t.Fatal(err)
	}

	var rawKey, rawToken, rawPassword string
	if err := db.QueryRow(`SELECT encryption_key, implant_token FROM c2_listeners WHERE id = ?`, listener.ID).Scan(&rawKey, &rawToken); err != nil {
		t.Fatal(err)
	}
	if err := db.QueryRow(`SELECT password FROM webshell_connections WHERE id = ?`, webshell.ID).Scan(&rawPassword); err != nil {
		t.Fatal(err)
	}
	for name, value := range map[string]string{"listener key": rawKey, "implant token": rawToken, "webshell password": rawPassword} {
		if !strings.HasPrefix(value, credentialCipherPrefix) {
			t.Fatalf("%s was not encrypted at rest: %q", name, value)
		}
		if strings.Contains(value, "plaintext") {
			t.Fatalf("%s leaked plaintext into storage", name)
		}
	}

	gotListener, err := db.GetC2Listener(listener.ID)
	if err != nil {
		t.Fatal(err)
	}
	if gotListener.EncryptionKey != listener.EncryptionKey || gotListener.ImplantToken != listener.ImplantToken {
		t.Fatalf("listener credential round trip mismatch: %#v", gotListener)
	}
	gotWebshell, err := db.GetWebshellConnection(webshell.ID)
	if err != nil {
		t.Fatal(err)
	}
	if gotWebshell.Password != webshell.Password {
		t.Fatalf("webshell password round trip mismatch: %q", gotWebshell.Password)
	}
}

func TestLegacyPlaintextCredentialsMigratedOnOpen(t *testing.T) {
	t.Setenv("JYSECAI_CREDENTIAL_KEY", "")
	t.Setenv("JYSSECAI_CREDENTIAL_KEY", "")
	dbPath := filepath.Join(t.TempDir(), "legacy.db")
	db, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`INSERT INTO c2_listeners
		(id, name, type, bind_host, bind_port, encryption_key, implant_token, status, config_json, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		"l_legacy", "legacy", "http_beacon", "127.0.0.1", 8080, "legacy-key", "legacy-token", "stopped", "{}", time.Now()); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`INSERT INTO webshell_connections
		(id, url, password, type, method, created_at) VALUES (?, ?, ?, ?, ?, ?)`,
		"ws_legacy", "https://example.invalid", "legacy-password", "php", "post", time.Now()); err != nil {
		t.Fatal(err)
	}
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}

	db, err = NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var rawKey, rawPassword string
	if err := db.QueryRow(`SELECT encryption_key FROM c2_listeners WHERE id = 'l_legacy'`).Scan(&rawKey); err != nil {
		t.Fatal(err)
	}
	if err := db.QueryRow(`SELECT password FROM webshell_connections WHERE id = 'ws_legacy'`).Scan(&rawPassword); err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(rawKey, credentialCipherPrefix) || !strings.HasPrefix(rawPassword, credentialCipherPrefix) {
		t.Fatalf("legacy secrets were not migrated: key=%q password=%q", rawKey, rawPassword)
	}
	listener, err := db.GetC2Listener("l_legacy")
	if err != nil || listener.EncryptionKey != "legacy-key" || listener.ImplantToken != "legacy-token" {
		t.Fatalf("legacy listener did not decrypt: listener=%#v err=%v", listener, err)
	}
	webshell, err := db.GetWebshellConnection("ws_legacy")
	if err != nil || webshell.Password != "legacy-password" {
		t.Fatalf("legacy webshell did not decrypt: webshell=%#v err=%v", webshell, err)
	}
}

func TestCorruptEncryptedCredentialFailsClosed(t *testing.T) {
	t.Setenv("JYSECAI_CREDENTIAL_KEY", "")
	t.Setenv("JYSSECAI_CREDENTIAL_KEY", "")
	db, err := NewDB(filepath.Join(t.TempDir(), "corrupt.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err := db.Exec(`INSERT INTO webshell_connections
		(id, url, password, type, method, created_at) VALUES (?, ?, ?, ?, ?, ?)`,
		"ws_corrupt", "https://example.invalid", credentialCipherPrefix+"broken", "php", "post", time.Now()); err != nil {
		t.Fatal(err)
	}
	if _, err := db.GetWebshellConnection("ws_corrupt"); err == nil {
		t.Fatal("expected corrupt encrypted credential to fail closed")
	}
}
