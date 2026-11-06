package config

import (
	"os"
	"path/filepath"
	"strings"
)

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

// LoadDotEnv 讀取與設定檔同目錄的 .env，只補上程序裡還沒有的變數。
// 已存在的環境變數與檔內其他列都保持原樣，避免蓋掉另外載入的密鑰。
func LoadDotEnv(configPath string) {
	path := filepath.Join(filepath.Dir(configPath), ".env")
	data, err := os.ReadFile(path)
	if err != nil {
		return
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "export ") {
			line = strings.TrimSpace(strings.TrimPrefix(line, "export "))
		}
		key, val, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		key = strings.TrimSpace(key)
		if key == "" || os.Getenv(key) != "" {
			continue
		}
		val = strings.TrimSpace(val)
		if len(val) >= 2 {
			if (val[0] == '\'' && val[len(val)-1] == '\'') || (val[0] == '"' && val[len(val)-1] == '"') {
				val = val[1 : len(val)-1]
			}
		}
		_ = os.Setenv(key, val)
	}
}

// ExpandConfigEnv 展开 ExternalMCPServerConfig 中所有支持环境变量的字段。
// 展开范围：Command、Args、Env values、URL、Headers values。
func ExpandConfigEnv(cfg *ExternalMCPServerConfig) {
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

// ExpandExternalMySQLEnv 展开外部 MySQL 接收端设定中的环境变量引用。
// 展开范围：Host、User、Password、Database、TablePrefix。
//
// 密码最该走环境变量：它是最不想落在磁盘上的字段，而 config.yaml 会跟着
// 仓库一起走（虽然被 .gitignore 排除，但备份、同步、贴聊天记录都会漏出去）。
func ExpandExternalMySQLEnv(cfg *ExternalMySQLConfig) {
	cfg.Host = expandEnvVar(cfg.Host)
	cfg.User = expandEnvVar(cfg.User)
	cfg.Password = expandEnvVar(cfg.Password)
	cfg.Database = expandEnvVar(cfg.Database)
	cfg.TablePrefix = expandEnvVar(cfg.TablePrefix)
}
