package app

import (
	"jysecai/internal/config"
	"jysecai/internal/mcp"
	"jysecai/internal/vision"

	"go.uber.org/zap"
)

func registerVisionTools(mcpServer *mcp.Server, cfg *config.Config, logger *zap.Logger) {
	vision.RegisterAnalyzeImageTool(mcpServer, cfg, logger)
}
