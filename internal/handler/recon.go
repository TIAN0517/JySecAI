package handler

import (
	"net/http"
	"strings"

	"jysecai/internal/recon"

	"github.com/gin-gonic/gin"
)

type ReconHandler struct {
	engine *recon.Engine
}

func NewReconHandler(engine *recon.Engine) *ReconHandler {
	return &ReconHandler{engine: engine}
}

type reconStartRequest struct {
	Target     string   `json:"target" binding:"required"`
	Profile    string   `json:"profile"`
	Collectors []string `json:"collectors"`
}

// Auto starts the complete native registry without requiring the caller to
// enumerate individual collectors.
func (h *ReconHandler) Auto(c *gin.Context) {
	var request reconStartRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid_request", "message": err.Error()})
		return
	}
	run, err := h.engine.Start(c.Request.Context(), request.Target, "deep", nil)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "recon_start_failed", "message": err.Error()})
		return
	}
	c.JSON(http.StatusAccepted, run)
}

func (h *ReconHandler) Start(c *gin.Context) {
	var request reconStartRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid_request", "message": err.Error()})
		return
	}
	profile := strings.TrimSpace(request.Profile)
	if profile == "" {
		profile = "quick"
	}
	run, err := h.engine.Start(c.Request.Context(), request.Target, profile, request.Collectors)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "recon_start_failed", "message": err.Error()})
		return
	}
	c.JSON(http.StatusAccepted, run)
}

func (h *ReconHandler) Get(c *gin.Context) {
	run, ok := h.engine.Get(c.Param("id"))
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "recon_run_not_found"})
		return
	}
	c.JSON(http.StatusOK, run)
}

func (h *ReconHandler) Cancel(c *gin.Context) {
	if !h.engine.Cancel(c.Param("id")) {
		c.JSON(http.StatusNotFound, gin.H{"error": "recon_run_not_found_or_finished"})
		return
	}
	c.JSON(http.StatusAccepted, gin.H{"status": "cancelled", "id": c.Param("id")})
}
