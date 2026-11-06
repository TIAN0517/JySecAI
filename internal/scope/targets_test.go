package scope

import (
	"os"
	"path/filepath"
	"testing"

	"jysecai/internal/config"
)

// positionalParam 建立一個位置參數。
func positionalParam(name string, position int) config.ParameterConfig {
	return config.ParameterConfig{
		Name:     name,
		Type:     "string",
		Position: &position,
		Format:   "positional",
	}
}

// flagParam 建立一個旗標參數。
func flagParam(name, flag string) config.ParameterConfig {
	return config.ParameterConfig{
		Name:   name,
		Type:   "string",
		Flag:   flag,
		Format: "flag",
	}
}

// templateParam 建立一個模板參數。
func templateParam(name, template string) config.ParameterConfig {
	return config.ParameterConfig{
		Name:     name,
		Type:     "string",
		Template: template,
		Format:   "template",
	}
}

// writeListFile 寫出一個目標清單檔。
func writeListFile(t *testing.T, lines ...string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "targets.txt")
	content := ""
	for _, line := range lines {
		content += line + "\n"
	}
	if err := os.WriteFile(path, []byte(content), 0o600); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestExtractTargetsFromPositionalParameter(t *testing.T) {
	params := []config.ParameterConfig{positionalParam("target", 0)}
	args := map[string]any{"target": "example.com"}

	targets, arbitrary, err := ExtractTargets("nmap", params, args, nil, "")
	if err != nil {
		t.Fatal(err)
	}
	if arbitrary {
		t.Fatal("有宣告目標參數的工具不該被視為任意執行類")
	}
	if len(targets) != 1 || targets[0] != "example.com" {
		t.Fatalf("目標抽取不正確：%v", targets)
	}
}

func TestExtractTargetsFromFlagParameter(t *testing.T) {
	params := []config.ParameterConfig{flagParam("url", "-u")}
	args := map[string]any{"url": "https://example.com/admin"}

	targets, arbitrary, err := ExtractTargets("ffuf", params, args, nil, "")
	if err != nil {
		t.Fatal(err)
	}
	if arbitrary {
		t.Fatal("有宣告目標參數的工具不該被視為任意執行類")
	}
	if len(targets) != 1 || targets[0] != "https://example.com/admin" {
		t.Fatalf("目標抽取不正確：%v", targets)
	}
}

func TestExtractTargetsFromTemplateParameter(t *testing.T) {
	params := []config.ParameterConfig{templateParam("host", "{value}")}
	args := map[string]any{"host": "example.com"}

	targets, arbitrary, err := ExtractTargets("custom", params, args, nil, "")
	if err != nil {
		t.Fatal(err)
	}
	if arbitrary {
		t.Fatal("有宣告目標參數的工具不該被視為任意執行類")
	}
	if len(targets) != 1 || targets[0] != "example.com" {
		t.Fatalf("目標抽取不正確：%v", targets)
	}
}

func TestExtractTargetsFromListFileInAdditionalArgs(t *testing.T) {
	path := writeListFile(t, "a.example.com", "# 這是註解，要被忽略", "", "b.example.com:8443")

	params := []config.ParameterConfig{positionalParam("targets", 0)}
	args := map[string]any{}

	// 兩種呼叫形式都要能處理：已切好的 token 與整串。
	for _, additional := range [][]string{
		{"-l", path, "-silent"},
		{"-l " + path + " -silent"},
	} {
		targets, arbitrary, err := ExtractTargets("httpx", params, args, additional, "")
		if err != nil {
			t.Fatal(err)
		}
		if arbitrary {
			t.Fatalf("有清單檔就不該是任意執行類：%v", additional)
		}
		if len(targets) != 2 {
			t.Fatalf("清單檔應展開成 2 個目標（註解與空行要略過），實際：%v", targets)
		}
		if targets[0] != "a.example.com" || targets[1] != "b.example.com:8443" {
			t.Fatalf("清單檔展開結果不正確：%v", targets)
		}
	}
}

func TestExtractTargetsFromMissingListFileFails(t *testing.T) {
	missing := filepath.Join(t.TempDir(), "not-exist.txt")
	params := []config.ParameterConfig{positionalParam("targets", 0)}

	// 清單檔讀不到就不能放行（fail closed）：寧可報錯也不要漏掉未檢查的目標。
	if _, _, err := ExtractTargets("httpx", params, map[string]any{}, []string{"-l", missing}, ""); err == nil {
		t.Fatal("清單檔不存在時應回報錯誤")
	}
}

func TestExtractTargetsFromStdin(t *testing.T) {
	params := []config.ParameterConfig{positionalParam("targets", 0)}

	targets, arbitrary, err := ExtractTargets("httpx", params, map[string]any{}, nil,
		"one.example.com\ntwo.example.com, three.example.com")
	if err != nil {
		t.Fatal(err)
	}
	if arbitrary {
		t.Fatal("有 stdin 就不該是任意執行類")
	}
	if len(targets) != 3 {
		t.Fatalf("stdin 應展開成 3 個目標，實際：%v", targets)
	}
}

func TestExtractTargetsFromStdinInArgsPayload(t *testing.T) {
	params := []config.ParameterConfig{positionalParam("targets", 0)}
	args := map[string]any{"stdin": "api.example.com"}

	targets, arbitrary, err := ExtractTargets("httpx", params, args, nil, "")
	if err != nil {
		t.Fatal(err)
	}
	if arbitrary {
		t.Fatal("payload 有 stdin 就不該是任意執行類")
	}
	if len(targets) != 1 || targets[0] != "api.example.com" {
		t.Fatalf("目標抽取不正確：%v", targets)
	}
}

func TestExtractTargetsArbitraryWhenNothingDeclared(t *testing.T) {
	params := []config.ParameterConfig{
		{Name: "script_content", Type: "string"},
		{Name: "additional_args", Type: "string", Format: "positional"},
	}

	targets, arbitrary, err := ExtractTargets("exec", params, map[string]any{}, nil, "")
	if err != nil {
		t.Fatal(err)
	}
	if !arbitrary {
		t.Fatal("沒有任何目標來源的工具必須被視為任意執行類")
	}
	if len(targets) != 0 {
		t.Fatalf("任意執行類不該自行生出目標：%v", targets)
	}
}

func TestExtractTargetsIgnoresNonTargetParameters(t *testing.T) {
	params := []config.ParameterConfig{
		flagParam("ports", "-p"),
		{Name: "additional_args", Type: "string", Format: "positional"},
	}
	args := map[string]any{"ports": "80,443", "additional_args": "-Pn"}

	targets, arbitrary, err := ExtractTargets("nmap", params, args, nil, "")
	if err != nil {
		t.Fatal(err)
	}
	if !arbitrary {
		t.Fatal("只有埠位與額外參數的工具屬任意執行類")
	}
	if len(targets) != 0 {
		t.Fatalf("埠位不是目標：%v", targets)
	}
}

func TestExtractTargetsCombinesAllThreeSources(t *testing.T) {
	path := writeListFile(t, "from-file.example.com")
	params := []config.ParameterConfig{positionalParam("target", 0)}
	args := map[string]any{"target": "from-param.example.com"}

	targets, arbitrary, err := ExtractTargets("httpx", params, args, []string{"-l", path},
		"from-stdin.example.com")
	if err != nil {
		t.Fatal(err)
	}
	if arbitrary {
		t.Fatal("三個來源都有目標，不該是任意執行類")
	}
	if len(targets) != 3 {
		t.Fatalf("三個來源應合併成 3 個目標，實際：%v", targets)
	}
}

func TestExtractTargetsDeduplicates(t *testing.T) {
	params := []config.ParameterConfig{positionalParam("target", 0)}
	args := map[string]any{"target": "example.com,example.com"}

	targets, _, err := ExtractTargets("nmap", params, args, nil, "")
	if err != nil {
		t.Fatal(err)
	}
	if len(targets) != 1 {
		t.Fatalf("重複目標應被去重，實際：%v", targets)
	}
}

func TestExtractTargetsExpandsFileParameter(t *testing.T) {
	path := writeListFile(t, "file-a.example.com", "file-b.example.com")
	params := []config.ParameterConfig{positionalParam("host_file", 0)}
	args := map[string]any{"host_file": path}

	targets, _, err := ExtractTargets("nuclei", params, args, nil, "")
	if err != nil {
		t.Fatal(err)
	}
	if len(targets) != 2 {
		t.Fatalf("檔案參數應被展開成 2 個目標，實際：%v", targets)
	}
}
