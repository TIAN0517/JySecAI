//go:build ignore

package main

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/cloudwego/eino/components/tool"
	"github.com/cloudwego/eino/components/tool/utils"
	"github.com/cloudwego/eino/schema"
)

// Mirror of eino filesystem grepArgs (subset) to see reflected schema.
type grepArgs struct {
	Pattern           string  `json:"pattern" jsonschema:"description=The regular expression pattern to search for in file contents"`
	Path              *string `json:"path,omitempty" jsonschema:"description=File or directory to search in"`
	Glob              *string `json:"glob,omitempty" jsonschema:"description=Glob pattern"`
	OutputMode        string  `json:"output_mode,omitempty" jsonschema:"description=Output mode,enum=content,enum=files_with_matches,enum=count"`
	Context           *int    `json:"-C,omitempty" jsonschema:"description=Context lines"`
	BeforeLines       *int    `json:"-B,omitempty" jsonschema:"description=Before lines"`
	AfterLines        *int    `json:"-A,omitempty" jsonschema:"description=After lines"`
	ShowLineNumbers   *bool   `json:"-n,omitempty" jsonschema:"description=Show line numbers"`
	CaseInsensitive   *bool   `json:"-i,omitempty" jsonschema:"description=Case insensitive"`
	FileType          *string `json:"type,omitempty" jsonschema:"description=File type"`
	HeadLimit         *int    `json:"head_limit,omitempty" jsonschema:"description=Head limit"`
	Offset            *int    `json:"offset,omitempty" jsonschema:"description=Offset"`
	Multiline         *bool   `json:"multiline,omitempty" jsonschema:"description=Multiline"`
}

func main() {
	t, err := utils.InferTool("grep", "search files", func(ctx context.Context, input grepArgs) (string, error) {
		return "ok", nil
	})
	if err != nil {
		panic(err)
	}
	info, err := t.Info(context.Background())
	if err != nil {
		panic(err)
	}
	b, _ := json.MarshalIndent(info, "", "  ")
	fmt.Println("ToolInfo:")
	fmt.Println(string(b))

	js, err := info.ParamsOneOf.ToJSONSchema()
	if err != nil {
		panic(err)
	}
	jb, _ := json.MarshalIndent(js, "", "  ")
	fmt.Println("JSONSchema:")
	fmt.Println(string(jb))

	// Simulate OpenAI tool envelope
	params, _ := json.Marshal(js)
	var paramsObj any
	_ = json.Unmarshal(params, &paramsObj)
	openaiTool := map[string]any{
		"type": "function",
		"function": map[string]any{
			"name":        info.Name,
			"description": info.Desc,
			"parameters":   paramsObj,
		},
	}
	ob, _ := json.MarshalIndent(openaiTool, "", "  ")
	fmt.Println("OpenAI tool:")
	fmt.Println(string(ob))

	_ = tool.BaseTool(nil)
	_ = schema.ToolInfo{}
}
