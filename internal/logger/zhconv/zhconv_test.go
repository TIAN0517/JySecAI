package zhconv

import "testing"

func TestS2T(t *testing.T) {
	cases := map[string]string{
		"":         "",
		"MCP":      "MCP",
		"123abc":   "123abc",
		"加载":      "加載",
		"外部":      "外部",
		"模型":      "模型",
		"新":         "新",
		"门":         "門",
		"类":         "類",
		"检":         "檢",
		"简":         "簡",
		"级":         "級",
		"绝":         "絕",
		"罗":         "羅",
		"妈":         "媽",
		"码":         "碼",
		"猫":         "貓",
		"扫":         "掃",
		"描":         "描",
		"结":         "結",
		"果":         "果",
		"全":         "全",
		"部":         "部",
		"优":         "優",
		"化":         "化",
	}
	for in, want := range cases {
		if got := S2T(in); got != want {
			t.Errorf("S2T(%q)=%q, want %q", in, got, want)
		}
	}

	if got := S2T("加载外部模型"); got != "加載外部模型" {
		t.Errorf("compound: %q want 加載外部模型", got)
	}
}
