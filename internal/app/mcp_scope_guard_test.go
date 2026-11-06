package app

import (
	"context"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/database"
	"jysecai/internal/mcp"

	"go.uber.org/zap"
)

// 專案授權範圍解析器的測試。

func newScopeGuardTestDB(t *testing.T) *database.DB {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "scope-guard.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	return db
}

func TestProjectScopeResolverResolvesConversationProject(t *testing.T) {
	db := newScopeGuardTestDB(t)
	project, err := db.CreateProject(&database.Project{
		Name:      "redirect project",
		ScopeJSON: `{"targets": ["portal.agency.gov.tw"], "exclude": ["legacy.gov.tw"]}`,
	})
	if err != nil {
		t.Fatal(err)
	}
	conversation, err := db.CreateConversation("scoped", database.ConversationCreateMeta{ProjectID: project.ID})
	if err != nil {
		t.Fatal(err)
	}

	resolver := newProjectScopeResolver(db)
	scope := resolver.Resolve(mcp.WithMCPConversationID(context.Background(), conversation.ID))
	if scope == nil {
		t.Fatal("expected a scope for the bound conversation")
	}
	allow := strings.Join(scope.AllowEntries(), ",")
	deny := strings.Join(scope.DenyEntries(), ",")
	if !strings.Contains(allow, "portal.agency.gov.tw") {
		t.Fatalf("allow entries missing: %s", allow)
	}
	if !strings.Contains(deny, "legacy.gov.tw") {
		t.Fatalf("deny entries missing: %s", deny)
	}
}

func TestProjectScopeResolverResolvesProjectFromContext(t *testing.T) {
	db := newScopeGuardTestDB(t)
	project, err := db.CreateProject(&database.Project{
		Name:      "direct project",
		ScopeJSON: `{"scope": {"allow": {"domains": ["portal.agency.gov.tw"]}}}`,
	})
	if err != nil {
		t.Fatal(err)
	}
	resolver := newProjectScopeResolver(db)
	scope := resolver.Resolve(mcp.WithMCPProjectID(context.Background(), project.ID))
	if scope == nil {
		t.Fatal("expected a scope for the project carried in the context")
	}
}

func TestProjectScopeResolverReturnsNilForUnboundConversation(t *testing.T) {
	db := newScopeGuardTestDB(t)
	conversation, err := db.CreateConversation("unbound", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	resolver := newProjectScopeResolver(db)
	if scope := resolver.Resolve(mcp.WithMCPConversationID(context.Background(), conversation.ID)); scope != nil {
		t.Fatalf("unbound conversation must not resolve a scope, got %#v", scope)
	}
	if scope := resolver.Resolve(context.Background()); scope != nil {
		t.Fatalf("empty context must not resolve a scope, got %#v", scope)
	}
}

func TestProjectScopeResolverIgnoresEmptyAndBrokenScope(t *testing.T) {
	db := newScopeGuardTestDB(t)
	empty, err := db.CreateProject(&database.Project{Name: "no scope"})
	if err != nil {
		t.Fatal(err)
	}
	broken, err := db.CreateProject(&database.Project{Name: "broken scope", ScopeJSON: "{not json"})
	if err != nil {
		t.Fatal(err)
	}
	resolver := newProjectScopeResolver(db)
	if scope := resolver.Resolve(mcp.WithMCPProjectID(context.Background(), empty.ID)); scope != nil {
		t.Fatal("project without scope must not resolve a scope")
	}
	if scope := resolver.Resolve(mcp.WithMCPProjectID(context.Background(), broken.ID)); scope != nil {
		t.Fatal("broken scope_json must not resolve a scope")
	}
}

func TestProjectScopeResolverPicksUpScopeChanges(t *testing.T) {
	db := newScopeGuardTestDB(t)
	project, err := db.CreateProject(&database.Project{
		Name:      "changing scope",
		ScopeJSON: `{"targets": ["first.example.com"]}`,
	})
	if err != nil {
		t.Fatal(err)
	}
	resolver := newProjectScopeResolver(db)
	first := resolver.Resolve(mcp.WithMCPProjectID(context.Background(), project.ID))
	if first == nil || !strings.Contains(strings.Join(first.AllowEntries(), ","), "first.example.com") {
		t.Fatalf("unexpected first scope: %#v", first)
	}

	updated := *project
	updated.ScopeJSON = `{"targets": ["second.example.com"]}`
	if err := db.UpdateProject(&updated); err != nil {
		t.Fatal(err)
	}
	second := resolver.Resolve(mcp.WithMCPProjectID(context.Background(), project.ID))
	if second == nil || !strings.Contains(strings.Join(second.AllowEntries(), ","), "second.example.com") {
		t.Fatalf("scope change must take effect immediately: %#v", second)
	}
}
