"""Asset Intelligence MCP — 資產測繪統一伺服器。

重用與對齊:
- FOFA: internal/handler/fofa.go Search() 已驗證邏輯 (providers/fofa.py)
- ZoomEye: internal/handler/fofa.go searchZoomEye() + tools/zoomeye_search.yaml (providers/zoomeye.py)
- MCP SDK: 與 mcp-servers/vuln_intel 相同的 FastMCP/MCPServer 相容匯入模式
- TLS: 與 tls_policy.py 相同策略 (第三方 API 驗證憑證鏈)
"""
from __future__ import annotations

try:  # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as _MCPServer
except ImportError:  # MCP SDK 1.x compatibility (專案現行: mcp 1.30.0)
    from mcp.server.fastmcp import FastMCP as _MCPServer

from .config import AssetIntelConfig
from .providers.fofa import FofaProvider
from .providers.zoomeye import ZoomEyeProvider
from .scope import ScopeRegistry, build_scope_from_config
from .storage import AssetStore

__version__ = "1.0.0"


def create_app(config: AssetIntelConfig | None = None) -> "_MCPServer":
    cfg = config or AssetIntelConfig.from_env()
    app = _MCPServer(
        name="jysecai-assets",
        instructions=(
            "JySecAI Asset Intelligence: unified asset mapping over FOFA and ZoomEye. "
            "External asset searches REQUIRE an authorized scope; out-of-scope targets are rejected. "
            "API keys are never exposed to agents. Query results are evidence-preserving "
            "(raw references kept, conflicts recorded, never silently overwritten)."
        ),
    )

    fofa = FofaProvider(
        api_key=cfg.fofa_api_key, base_url=cfg.fofa_base_url,
        timeout=cfg.timeout_seconds, max_retries=cfg.max_retries,
        verify_tls=cfg.verify_tls, ca_bundle=cfg.ca_bundle,
    )
    zoomeye = ZoomEyeProvider(
        api_key=cfg.zoomeye_api_key, base_url=cfg.zoomeye_base_url,
        timeout=cfg.timeout_seconds, max_retries=cfg.max_retries,
        verify_tls=cfg.verify_tls, ca_bundle=cfg.ca_bundle,
    )
    providers = {"fofa": fofa, "zoomeye": zoomeye}
    registry = ScopeRegistry()
    for sid, sc in (cfg.scopes or {}).items():
        scope = build_scope_from_config({**sc, "scope_id": sid})
        if scope:
            registry.register(scope)
    store = AssetStore(cfg.db_path)

    # ---- 工具匯入 (延遲註冊以避免循環匯入) ----
    from . import tools as toolmod

    toolmod.register(app, cfg=cfg, providers=providers, registry=registry, store=store)
    return app


def main() -> None:
    """stdio 進入點 — stdout 為協定專用, 所有日誌走 stderr (經遮蔽)。"""
    import logging
    import sys

    from .security import SecretRedactingFormatter

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(SecretRedactingFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")))
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)

    app = create_app()
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
