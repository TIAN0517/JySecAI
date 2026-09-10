package config

import (
	"bufio"
	"os"
	"path/filepath"
	"strings"
)

// loadDotEnvIfPresent 尝试从指定目录载入 .env 文件。
// 仅当环境中尚无对应 key 时才设置，不覆盖已有的系统环境变量。
func loadDotEnvIfPresent(dir string) {
	if strings.TrimSpace(dir) == "" {
		return
	}
	envPath := filepath.Join(dir, ".env")
	f, err := os.Open(envPath)
	if err != nil {
		return
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		eqIdx := strings.IndexByte(line, '=')
		if eqIdx <= 0 {
			continue
		}
		key := strings.TrimSpace(line[:eqIdx])
		val := strings.TrimSpace(line[eqIdx+1:])
		// 移除包围的单双引号
		if len(val) >= 2 {
			if (val[0] == '"' && val[len(val)-1] == '"') || (val[0] == '\'' && val[len(val)-1] == '\'') {
				val = val[1 : len(val)-1]
			}
		}
		if _, exists := os.LookupEnv(key); !exists {
			_ = os.Setenv(key, val)
		}
	}
}

// expandEnvVar 展开字符串中的 ${VAR} 和 ${VAR:-default} 环境变量引用。
// 与官方 MCP 配置格式一致（Claude Desktop / Cursor / VS Code 均支持此语法）。
func expandEnvVar(s string) string {
	var b strings.Builder
	i := 0
	for i < len(s) {
		// 查找 ${
		idx := strings.Index(s[i:], "${")
		if idx < 0 {
			b.WriteString(s[i:])
			break
		}
		b.WriteString(s[i : i+idx])
		i += idx + 2 // skip ${

		// 查找对应的 }
		end := strings.IndexByte(s[i:], '}')
		if end < 0 {
			// 没有 }，原样保留
			b.WriteString("${")
			continue
		}
		expr := s[i : i+end]
		i += end + 1 // skip }

		// 解析 VAR:-default
		varName := expr
		defaultVal := ""
		hasDefault := false
		if colonIdx := strings.Index(expr, ":-"); colonIdx >= 0 {
			varName = expr[:colonIdx]
			defaultVal = expr[colonIdx+2:]
			hasDefault = true
		}

		val := os.Getenv(varName)
		if val == "" && hasDefault {
			val = defaultVal
		}
		b.WriteString(val)
	}
	return b.String()
}

// ExpandConfigEnv 展开 ExternalMCPServerConfig 中所有支持环境变量的字段。
// 展开范围：Command、Args、Env values、URL、Headers values。
func ExpandConfigEnv(cfg *ExternalMCPServerConfig) {
	if cfg == nil {
		return
	}
	cfg.Command = expandEnvVar(cfg.Command)
	for i, arg := range cfg.Args {
		cfg.Args[i] = expandEnvVar(arg)
	}
	for k, v := range cfg.Env {
		cfg.Env[k] = expandEnvVar(v)
	}
	cfg.URL = expandEnvVar(cfg.URL)
	for k, v := range cfg.Headers {
		cfg.Headers[k] = expandEnvVar(v)
	}
}

// ExpandConfigEnvAll 展开 Config 全局配置中所有支持环境变量的字段。
// 涵盖 AI 通道、资产测绘 (FOFA/ZoomEye/Quake/Shodan)、视觉、知识库、外部 MCP、代理池等。
func ExpandConfigEnvAll(cfg *Config) {
	if cfg == nil {
		return
	}

	// 1. AI 渠道与默认渠道
	cfg.AI.DefaultChannel = expandEnvVar(cfg.AI.DefaultChannel)
	if cfg.AI.Channels != nil {
		for id, ch := range cfg.AI.Channels {
			ch.Name = expandEnvVar(ch.Name)
			ch.Provider = expandEnvVar(ch.Provider)
			ch.APIKey = expandEnvVar(ch.APIKey)
			ch.BaseURL = expandEnvVar(ch.BaseURL)
			ch.Model = expandEnvVar(ch.Model)
			cfg.AI.Channels[id] = ch
		}
	}

	// 2. OpenAI 主配置（向后兼容）
	cfg.OpenAI.Provider = expandEnvVar(cfg.OpenAI.Provider)
	cfg.OpenAI.APIKey = expandEnvVar(cfg.OpenAI.APIKey)
	cfg.OpenAI.BaseURL = expandEnvVar(cfg.OpenAI.BaseURL)
	cfg.OpenAI.Model = expandEnvVar(cfg.OpenAI.Model)

	// 3. 空间资产测绘 API (FOFA, ZoomEye, Quake, Shodan)
	cfg.FOFA.BaseURL = expandEnvVar(cfg.FOFA.BaseURL)
	cfg.FOFA.APIKey = expandEnvVar(cfg.FOFA.APIKey)
	if cfg.FOFA.APIKey == "" {
		if k := strings.TrimSpace(os.Getenv("FOFA_API_KEY")); k != "" {
			cfg.FOFA.APIKey = k
		}
	}
	if cfg.FOFA.BaseURL == "" {
		if u := strings.TrimSpace(os.Getenv("FOFA_BASE_URL")); u != "" {
			cfg.FOFA.BaseURL = u
		}
	}

	cfg.ZoomEye.BaseURL = expandEnvVar(cfg.ZoomEye.BaseURL)
	cfg.ZoomEye.APIKey = expandEnvVar(cfg.ZoomEye.APIKey)
	if cfg.ZoomEye.APIKey == "" {
		if k := strings.TrimSpace(os.Getenv("ZOOMEYE_API_KEY")); k != "" {
			cfg.ZoomEye.APIKey = k
		}
	}
	if cfg.ZoomEye.BaseURL == "" {
		if u := strings.TrimSpace(os.Getenv("ZOOMEYE_BASE_URL")); u != "" {
			cfg.ZoomEye.BaseURL = u
		}
	}

	cfg.Quake.BaseURL = expandEnvVar(cfg.Quake.BaseURL)
	cfg.Quake.APIKey = expandEnvVar(cfg.Quake.APIKey)
	if cfg.Quake.APIKey == "" {
		if k := strings.TrimSpace(os.Getenv("QUAKE_API_KEY")); k != "" {
			cfg.Quake.APIKey = k
		}
	}
	if cfg.Quake.BaseURL == "" {
		if u := strings.TrimSpace(os.Getenv("QUAKE_BASE_URL")); u != "" {
			cfg.Quake.BaseURL = u
		}
	}

	cfg.Shodan.BaseURL = expandEnvVar(cfg.Shodan.BaseURL)
	cfg.Shodan.APIKey = expandEnvVar(cfg.Shodan.APIKey)
	if cfg.Shodan.APIKey == "" {
		if k := strings.TrimSpace(os.Getenv("SHODAN_API_KEY")); k != "" {
			cfg.Shodan.APIKey = k
		}
	}
	if cfg.Shodan.BaseURL == "" {
		if u := strings.TrimSpace(os.Getenv("SHODAN_BASE_URL")); u != "" {
			cfg.Shodan.BaseURL = u
		}
	}

	// 4. 视觉配置
	cfg.Vision.BaseURL = expandEnvVar(cfg.Vision.BaseURL)
	cfg.Vision.APIKey = expandEnvVar(cfg.Vision.APIKey)
	cfg.Vision.Model = expandEnvVar(cfg.Vision.Model)
	cfg.Vision.Provider = expandEnvVar(cfg.Vision.Provider)

	// 5. 知识库配置
	cfg.Knowledge.BasePath = expandEnvVar(cfg.Knowledge.BasePath)
	cfg.Knowledge.Embedding.Provider = expandEnvVar(cfg.Knowledge.Embedding.Provider)
	cfg.Knowledge.Embedding.Model = expandEnvVar(cfg.Knowledge.Embedding.Model)
	cfg.Knowledge.Embedding.BaseURL = expandEnvVar(cfg.Knowledge.Embedding.BaseURL)
	cfg.Knowledge.Embedding.APIKey = expandEnvVar(cfg.Knowledge.Embedding.APIKey)
	if cfg.Knowledge.Embedding.APIKey == "" {
		if k := strings.TrimSpace(os.Getenv("EMBEDDING_API_KEY")); k != "" {
			cfg.Knowledge.Embedding.APIKey = k
		} else if k := strings.TrimSpace(os.Getenv("DASHSCOPE_API_KEY")); k != "" {
			cfg.Knowledge.Embedding.APIKey = k
		}
	}
	cfg.Knowledge.Retrieval.Rerank.Provider = expandEnvVar(cfg.Knowledge.Retrieval.Rerank.Provider)
	cfg.Knowledge.Retrieval.Rerank.Model = expandEnvVar(cfg.Knowledge.Retrieval.Rerank.Model)
	cfg.Knowledge.Retrieval.Rerank.BaseURL = expandEnvVar(cfg.Knowledge.Retrieval.Rerank.BaseURL)
	cfg.Knowledge.Retrieval.Rerank.APIKey = expandEnvVar(cfg.Knowledge.Retrieval.Rerank.APIKey)

	// 6. 人机协同审计模型
	cfg.Hitl.AuditModel.Provider = expandEnvVar(cfg.Hitl.AuditModel.Provider)
	cfg.Hitl.AuditModel.BaseURL = expandEnvVar(cfg.Hitl.AuditModel.BaseURL)
	cfg.Hitl.AuditModel.APIKey = expandEnvVar(cfg.Hitl.AuditModel.APIKey)
	cfg.Hitl.AuditModel.Model = expandEnvVar(cfg.Hitl.AuditModel.Model)

	// 7. MCP 认证
	cfg.MCP.AuthHeaderValue = expandEnvVar(cfg.MCP.AuthHeaderValue)

	// 8. 代理池
	cfg.ProxyPool.HealthCheckURL = expandEnvVar(cfg.ProxyPool.HealthCheckURL)
	for i := range cfg.ProxyPool.Proxies {
		cfg.ProxyPool.Proxies[i].Name = expandEnvVar(cfg.ProxyPool.Proxies[i].Name)
		cfg.ProxyPool.Proxies[i].URL = expandEnvVar(cfg.ProxyPool.Proxies[i].URL)
	}

	// 9. 外部 MCP 服务器
	if cfg.ExternalMCP.Servers != nil {
		for name, serverCfg := range cfg.ExternalMCP.Servers {
			ExpandConfigEnv(&serverCfg)
			cfg.ExternalMCP.Servers[name] = serverCfg
		}
	}
}

