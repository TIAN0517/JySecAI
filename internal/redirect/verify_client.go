package redirect

import (
	"net/http"
	"strings"
	"time"
)

// NewVerifyClient 依代理設定建立 HTTP client；proxyURL 為空時直連。
//
// 這是受控跳轉驗證（單筆複測與批次複測）共用的 client 建立方式，
// 避免 app 與 handler 兩邊各寫一份而行為漂移。
func NewVerifyClient(proxyURL string, timeout time.Duration) (*http.Client, error) {
	if strings.TrimSpace(proxyURL) == "" {
		return &http.Client{Timeout: timeout}, nil
	}
	client, err := NewProxyClient(proxyURL, timeout)
	if err != nil {
		return nil, err
	}
	if client == nil {
		return &http.Client{Timeout: timeout}, nil
	}
	return client, nil
}
