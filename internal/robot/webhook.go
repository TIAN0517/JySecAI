package robot

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"time"

	"jysecai/internal/config"
)

// WebhookAlert is the payload POSTed to a RobotWebhookConfig URL when a
// vulnerability alert is due. It is deliberately a flat, stable struct: hermes
// consumes it, and changing a field name is a breaking change for that
// consumer. New optional fields may be added.
type WebhookAlert struct {
	Event           string `json:"event"`
	VulnerabilityID string `json:"vulnerability_id"`
	Title           string `json:"title"`
	Severity        string `json:"severity"`
	Status          string `json:"status"`
	Target          string `json:"target"`
	Type            string `json:"type"`
	Impact          string `json:"impact"`
	Recommendation  string `json:"recommendation"`
	ProjectID       string `json:"project_id"`
	ConversationID  string `json:"conversation_id"`
	RBACUserID      string `json:"rbac_user_id"`
	Platform        string `json:"platform"`
	ExternalUserID  string `json:"external_user_id"`
	Attempts        int    `json:"attempts"`
	Message         string `json:"message"`
	SentAt          string `json:"sent_at"`
}

// signWebhookBody produces the hex-encoded HMAC-SHA256 the receiver verifies.
// The receiver must compare with hmac.Equal (constant time) against the raw
// body -- a plain string compare leaks the signature one byte at a time.
func signWebhookBody(secret string, body []byte) string {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	return hex.EncodeToString(mac.Sum(nil))
}

// validateWebhookURL refuses anything but an absolute http/https URL. The
// intended target is a loopback receiver on the same host, so a caller-supplied
// URL is only ever a mistake or an injection attempt; both deserve a loud
// failure rather than a request to an arbitrary host carrying alert contents.
func validateWebhookURL(raw string) error {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return fmt.Errorf("webhook url is empty")
	}
	parsed, err := url.Parse(raw)
	if err != nil {
		return fmt.Errorf("webhook url is not parseable: %w", err)
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return fmt.Errorf("webhook url must be http or https, got %q", parsed.Scheme)
	}
	if parsed.Host == "" {
		return fmt.Errorf("webhook url has no host")
	}
	return nil
}

// SendWebhookAlert delivers one vulnerability alert to the configured webhook.
// The caller fills in the vulnerability fields; everything identity-related is
// derived here so the receiver never has to trust the caller's routing.
func SendWebhookAlert(ctx context.Context, cfg config.RobotsConfig, externalUserID, message string, alert WebhookAlert) error {
	alert.ExternalUserID = externalUserID
	return sendWebhookProactive(ctx, cfg.Webhook, externalUserID, message, alert)
}

// sendWebhookProactive POSTs one alert. The recipient is ignored on purpose:
// the webhook fan-out belongs to the receiver (hermes owns which chat targets
// exist), so JySecAI only guarantees "this alert happened, deliver it once".
func sendWebhookProactive(ctx context.Context, cfg config.RobotWebhookConfig, _ string, message string, alert WebhookAlert) error {
	if !cfg.Configured() {
		return fmt.Errorf("webhook is not configured (need enabled + url + secret)")
	}
	if err := validateWebhookURL(cfg.URL); err != nil {
		return err
	}
	alert.Event = "vulnerability.alert"
	alert.Message = message
	alert.SentAt = time.Now().UTC().Format(time.RFC3339)
	alert.Platform = "webhook"

	body, err := json.Marshal(alert)
	if err != nil {
		return fmt.Errorf("marshal webhook payload: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimSpace(cfg.URL), bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build webhook request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json; charset=utf-8")
	req.Header.Set("X-JySecAI-Signature", "sha256="+signWebhookBody(cfg.Secret, body))
	req.Header.Set("X-JySecAI-Event", alert.Event)
	req.Header.Set("User-Agent", "JySecAI/1.0")

	resp, err := nilSafeHTTPClient().Do(req)
	if err != nil {
		return fmt.Errorf("webhook request failed: %w", err)
	}
	defer func() { _ = resp.Body.Close() }()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		// Drain a bounded amount so the connection can be reused, but never let
		// a misbehaving receiver stream unbounded data into our logs.
		var snippet [512]byte
		n, _ := resp.Body.Read(snippet[:])
		return fmt.Errorf("webhook returned %s: %s", resp.Status, strings.TrimSpace(string(snippet[:n])))
	}
	return nil
}
