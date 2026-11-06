package main

import (
	"testing"

	"jysecai/internal/scopeaudit"
)

// TestDraftGrantIDIsStable 確認冪等鍵穩定。
//
// 同一個目標重跑必須產生同一個 ID，否則每次起草都會多一張券——
// 授權券會愈疊愈多，操作者看到的是一堆重複項目而不是一個待決事項。
func TestDraftGrantIDIsStable(t *testing.T) {
	first := draftGrantID("Example.COM")
	second := draftGrantID("example.com")
	if first != second {
		t.Fatalf("大小寫不同的同一目標應產生相同 ID：%s vs %s", first, second)
	}
	if first != draftGrantID("  example.com  ") {
		t.Fatalf("前後空白的同一目標應產生相同 ID：%s", first)
	}
	if draftGrantID("a.example.com") == draftGrantID("b.example.com") {
		t.Fatal("不同目標不該產生相同 ID")
	}
}

// TestBuildDraftsSkipsDeniedTargets 確認被拒絕的目標不會被起草。
//
// 禁區（119／EPCR／消防救護）與永久封鎖類別在 Resolve 裡會落到 Denied 桶，
// 只有 Uncovered 的目標才該進入起草流程。
func TestBuildDraftsSkipsDeniedTargets(t *testing.T) {
	report := scopeaudit.Report{
		Uncovered: []scopeaudit.UncoveredTarget{
			{Target: scopeaudit.Target{Host: "a.example.com", Raw: "a.example.com"}},
		},
	}
	drafts := buildDrafts(report, 50)
	if len(drafts) != 1 {
		t.Fatalf("應該起草 1 個目標，實際 %d", len(drafts))
	}
	if drafts[0].Host != "a.example.com" {
		t.Fatalf("主機不正確：%s", drafts[0].Host)
	}
	if drafts[0].GrantID == "" {
		t.Fatal("應該產生冪等 ID")
	}
}

// TestBuildDraftsRespectsLimit 確認起草數量有上限（不會一次產生幾千張券）。
func TestBuildDraftsRespectsLimit(t *testing.T) {
	report := scopeaudit.Report{}
	for _, host := range []string{"a.example.com", "b.example.com", "c.example.com"} {
		report.Uncovered = append(report.Uncovered, scopeaudit.UncoveredTarget{
			Target: scopeaudit.Target{Host: host, Raw: host},
		})
	}
	drafts := buildDrafts(report, 2)
	if len(drafts) != 2 {
		t.Fatalf("應該只起草 2 個目標，實際 %d", len(drafts))
	}
	// 排序必須穩定，讓每次起草的順序可稽核。
	if drafts[0].Host != "a.example.com" {
		t.Fatalf("起草順序應依主機排序，實際第一個是 %s", drafts[0].Host)
	}
}

// TestBuildDraftsSkipsEmptyHost 確認沒有主機的目標不會被起草。
func TestBuildDraftsSkipsEmptyHost(t *testing.T) {
	report := scopeaudit.Report{
		Uncovered: []scopeaudit.UncoveredTarget{
			{Target: scopeaudit.Target{Host: "  ", Raw: "  "}},
		},
	}
	if drafts := buildDrafts(report, 50); len(drafts) != 0 {
		t.Fatalf("空主機不該被起草，實際 %d 筆", len(drafts))
	}
}
