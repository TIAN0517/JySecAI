package handler

import (
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestGovernancePageIsServed(t *testing.T) {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	MountGovernancePage(router, filepath.Join("..", "..", "web", "governance"))

	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/governance/", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("GET /governance/ status = %d, body = %s", rec.Code, rec.Body.String())
	}
	if !strings.Contains(rec.Body.String(), "GOVERNED MULTI-ENGINE") {
		t.Fatal("restored governance page is missing its original heading")
	}

	rec = httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/governance", nil))
	if rec.Code != http.StatusPermanentRedirect {
		t.Fatalf("GET /governance status = %d", rec.Code)
	}

	rec = httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/v1/catalog", nil))
	if rec.Code != http.StatusOK || !strings.Contains(rec.Body.String(), `"active":false`) {
		t.Fatalf("catalog = %d %s", rec.Code, rec.Body.String())
	}

	rec = httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodPost, "/v1/runs", strings.NewReader(`{}`)))
	if rec.Code != http.StatusGone {
		t.Fatalf("POST /v1/runs status = %d", rec.Code)
	}
}
