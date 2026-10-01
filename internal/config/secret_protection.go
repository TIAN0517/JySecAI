package config

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
)

const protectedConfigPrefix = "enc:cfg:v1:"

func configSecretAEAD(configPath string, createKey bool) (cipher.AEAD, error) {
	keyText := strings.TrimSpace(os.Getenv("JYSECAI_CONFIG_KEY"))
	if keyText == "" {
		keyText = strings.TrimSpace(os.Getenv("JYSECAI_CREDENTIAL_KEY"))
	}
	var key []byte
	var err error
	if keyText == "" {
		keyPath := configPath + ".secrets.key"
		if createKey {
			key, err = loadOrCreateConfigSecretKey(keyPath)
		} else {
			var data []byte
			data, err = os.ReadFile(keyPath)
			if err == nil {
				key, err = decodeConfigSecretKey(string(data))
			}
		}
	} else {
		key, err = decodeConfigSecretKey(keyText)
	}
	if err != nil {
		return nil, err
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	return cipher.NewGCM(block)
}

func decodeConfigSecretKey(value string) ([]byte, error) {
	for _, decoder := range []func(string) ([]byte, error){base64.StdEncoding.DecodeString, base64.RawStdEncoding.DecodeString, hex.DecodeString} {
		if key, err := decoder(strings.TrimSpace(value)); err == nil && len(key) == 32 {
			return key, nil
		}
	}
	return nil, errors.New("JYSECAI_CONFIG_KEY must encode exactly 32 bytes (base64 or hex)")
}

func loadOrCreateConfigSecretKey(path string) ([]byte, error) {
	if data, err := os.ReadFile(path); err == nil {
		return decodeConfigSecretKey(string(data))
	} else if !os.IsNotExist(err) {
		return nil, err
	}
	key := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, key); err != nil {
		return nil, err
	}
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
	if err != nil {
		if os.IsExist(err) {
			data, readErr := os.ReadFile(path)
			if readErr != nil {
				return nil, readErr
			}
			return decodeConfigSecretKey(string(data))
		}
		return nil, err
	}
	ok := false
	defer func() {
		_ = f.Close()
		if !ok {
			_ = os.Remove(path)
		}
	}()
	if _, err := f.WriteString(base64.StdEncoding.EncodeToString(key) + "\n"); err != nil {
		return nil, err
	}
	if err := f.Sync(); err != nil {
		return nil, err
	}
	if err := f.Close(); err != nil {
		return nil, err
	}
	ok = true
	return key, nil
}

func protectConfigValue(aead cipher.AEAD, value string) (string, error) {
	if value == "" || strings.HasPrefix(value, protectedConfigPrefix) || strings.Contains(value, "${") {
		return value, nil
	}
	nonce := make([]byte, aead.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", err
	}
	payload := append(nonce, aead.Seal(nil, nonce, []byte(value), nil)...)
	return protectedConfigPrefix + base64.RawStdEncoding.EncodeToString(payload), nil
}

func unprotectConfigValue(aead cipher.AEAD, value string) (string, error) {
	if value == "" || !strings.HasPrefix(value, protectedConfigPrefix) {
		return value, nil
	}
	payload, err := base64.RawStdEncoding.DecodeString(strings.TrimPrefix(value, protectedConfigPrefix))
	if err != nil || len(payload) < aead.NonceSize() {
		return "", errors.New("invalid protected config secret")
	}
	plain, err := aead.Open(nil, payload[:aead.NonceSize()], payload[aead.NonceSize():], nil)
	if err != nil {
		return "", fmt.Errorf("decrypt protected config secret: %w", err)
	}
	return string(plain), nil
}

func transformRobotSecrets(cfg *RobotsConfig, transform func(string) (string, error)) error {
	values := []*string{
		&cfg.Wechat.BotToken, &cfg.Wecom.Token, &cfg.Wecom.EncodingAESKey, &cfg.Wecom.Secret,
		&cfg.Dingtalk.ClientSecret, &cfg.Lark.AppSecret, &cfg.Lark.VerifyToken,
		&cfg.Telegram.BotToken, &cfg.Slack.BotToken, &cfg.Slack.AppToken,
		&cfg.Discord.BotToken, &cfg.QQ.ClientSecret,
	}
	for _, value := range values {
		updated, err := transform(*value)
		if err != nil {
			return err
		}
		*value = updated
	}
	return nil
}

// ProtectSensitiveConfig returns copies suitable for persistence; runtime values remain plaintext in memory.
func ProtectSensitiveConfig(configPath string, robots RobotsConfig, external ExternalMCPConfig) (RobotsConfig, ExternalMCPConfig, error) {
	aead, err := configSecretAEAD(configPath, true)
	if err != nil {
		return robots, external, err
	}
	if err := transformRobotSecrets(&robots, func(v string) (string, error) { return protectConfigValue(aead, v) }); err != nil {
		return robots, external, err
	}
	protectedServers := make(map[string]ExternalMCPServerConfig, len(external.Servers))
	for name, server := range external.Servers {
		server.Env, err = transformStringMap(server.Env, func(v string) (string, error) { return protectConfigValue(aead, v) })
		if err != nil {
			return robots, external, err
		}
		server.Headers, err = transformStringMap(server.Headers, func(v string) (string, error) { return protectConfigValue(aead, v) })
		if err != nil {
			return robots, external, err
		}
		protectedServers[name] = server
	}
	external.Servers = protectedServers
	return robots, external, nil
}

func unprotectSensitiveConfig(configPath string, cfg *Config) error {
	needsKey := false
	check := func(value string) { needsKey = needsKey || strings.HasPrefix(value, protectedConfigPrefix) }
	robotCopy := cfg.Robots
	_ = transformRobotSecrets(&robotCopy, func(v string) (string, error) { check(v); return v, nil })
	for _, server := range cfg.ExternalMCP.Servers {
		for _, value := range server.Env {
			check(value)
		}
		for _, value := range server.Headers {
			check(value)
		}
	}
	if !needsKey {
		return nil
	}
	aead, err := configSecretAEAD(configPath, false)
	if err != nil {
		return err
	}
	if err := transformRobotSecrets(&cfg.Robots, func(v string) (string, error) { return unprotectConfigValue(aead, v) }); err != nil {
		return err
	}
	for name, server := range cfg.ExternalMCP.Servers {
		server.Env, err = transformStringMap(server.Env, func(v string) (string, error) { return unprotectConfigValue(aead, v) })
		if err != nil {
			return err
		}
		server.Headers, err = transformStringMap(server.Headers, func(v string) (string, error) { return unprotectConfigValue(aead, v) })
		if err != nil {
			return err
		}
		cfg.ExternalMCP.Servers[name] = server
	}
	return nil
}

func transformStringMap(values map[string]string, transform func(string) (string, error)) (map[string]string, error) {
	if values == nil {
		return nil, nil
	}
	out := make(map[string]string, len(values))
	for key, value := range values {
		updated, err := transform(value)
		if err != nil {
			return nil, err
		}
		out[key] = updated
	}
	return out, nil
}
