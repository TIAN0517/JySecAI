package handler

import (
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"

	"jysecai/internal/database"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func TestAssetHandlersRejectMissingSession(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "a401.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	h := NewAssetHandler(db, zap.NewNop())

	cases := []struct {
		name   string
		target string
		fn     gin.HandlerFunc
	}{
		{"list", "/api/assets", h.List},
		{"stats", "/api/assets/stats", h.Stats},
		{"delete", "/api/assets/a1", h.Delete},
	}
	for _, tc := range cases {
		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		c.Request = httptest.NewRequest(http.MethodGet, tc.target, nil)
		c.Params = gin.Params{{Key: "id", Value: "a1"}}
		tc.fn(c)
		if w.Code != http.StatusUnauthorized {
			t.Errorf("%s: status=%d, want 401; body=%s", tc.name, w.Code, w.Body.String())
		}
	}
}
