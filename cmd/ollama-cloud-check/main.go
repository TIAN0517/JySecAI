// 用現有的 OpenAI 相容客戶端打 Ollama Cloud 的 ollama-cloud 通道。
// 金鑰只從 OLLAMA_API_KEY（.env 或環境變數）讀入，不寫進程式、也不印出。
package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/openai"
	"jysecai/internal/security"

	"go.uber.org/zap"
)

func main() {
	cfgPath := "config.yaml"
	if len(os.Args) > 1 {
		cfgPath = os.Args[1]
	}
	cfg, err := config.Load(cfgPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "load config: %v\n", err)
		os.Exit(1)
	}
	oa, id, ok := cfg.AI.ResolveChannel("ollama-cloud")
	if !ok {
		fmt.Fprintln(os.Stderr, "channel ollama-cloud is not configured")
		os.Exit(1)
	}
	if oa.APIKey == "" {
		fmt.Fprintln(os.Stderr, "OLLAMA_API_KEY is empty. Put it in .env next to config.yaml.")
		os.Exit(1)
	}

	client := openai.NewClient(&oa, security.NewSSRFGuardedClient(120*time.Second), zap.NewNop())
	var out struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}
	err = client.ChatCompletion(context.Background(), map[string]any{
		"model": oa.Model,
		"messages": []map[string]string{
			{"role": "user", "content": "Reply with one short sentence: what color is the sky?"},
		},
		"stream": false,
	}, &out)
	if err != nil {
		if apiErr, ok := err.(*openai.APIError); ok {
			fmt.Fprintf(os.Stderr, "ollama http %d\n%s\n", apiErr.StatusCode, apiErr.Body)
			os.Exit(1)
		}
		fmt.Fprintf(os.Stderr, "channel %s: %v\n", id, err)
		os.Exit(1)
	}
	if len(out.Choices) == 0 || out.Choices[0].Message.Content == "" {
		fmt.Fprintln(os.Stderr, "ollama returned an empty reply")
		os.Exit(1)
	}
	fmt.Println(out.Choices[0].Message.Content)
}
