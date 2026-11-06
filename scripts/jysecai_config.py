#!/usr/bin/env python3
"""scripts 共用的小工具：從 config.yaml 推導本機 API 的 base URL。

為什麼要這個
  config.yaml 的 server 區塊決定了 API 實際 listens 在哪：
    server.port         目前 8855（不是常見的 8080）
    server.tls_enabled  目前 true → 要走 https，不是 http
  把 base URL 寫死成 http://127.0.0.1:8080/api 會兩邊都錯，
  而且錯得很安靜：腳本看起來正常執行，卻在第一步就連不上。
  這裡集中讀一次，讓各腳本不會各自記錯。

用法
  from jysecai_config import default_base_url
  base = default_base_url('/var/lib/jysecai/core/config.yaml')

找不到設定檔或缺欄位時不硬失敗：回傳 FALLBACK_BASE_URL 並在 stderr 提示
用 --base-url 覆寫。這些腳本本來就常在開發機上對著本機服務跑，
設定檔不存在不代表使用者想被擋下。
"""
from __future__ import annotations

import sys

DEFAULT_CONFIG = "/var/lib/jysecai/core/config.yaml"

# 設定檔讀不到時的最後手段。port 與 scheme 取自 config.yaml 現值（tls_enabled: true）。
# 若實際環境不同，請用呼叫端提供的 --base-url 覆寫。
FALLBACK_BASE_URL = "https://127.0.0.1:8855/api"


def default_base_url(config_path: str = DEFAULT_CONFIG) -> str:
    """從 config.yaml 的 server 區塊推導 API base URL，回傳如 https://127.0.0.1:8855/api。

    port 與 tls_enabled 都要讀：只讀 port 的話，啟用 TLS 時會拿到 http://，
    然後卡在 self-signed 憑證或直接連不上。
    """
    try:
        import yaml
    except ImportError:
        print("[warn] 沒裝 PyYAML，改用預設 base-url；要指向別處請用 --base-url",
              file=sys.stderr)
        return FALLBACK_BASE_URL
    try:
        with open(config_path, "rb") as f:
            cfg = yaml.safe_load(f) or {}
    except OSError as e:
        print(f"[warn] 讀不到設定檔 {config_path}（{e.__class__.__name__}），"
              f"改用 {FALLBACK_BASE_URL}；要指向別處請用 --base-url", file=sys.stderr)
        return FALLBACK_BASE_URL
    except yaml.YAMLError as e:
        print(f"[warn] 設定檔 {config_path} YAML 解析失敗（{e.__class__.__name__}），"
              f"改用 {FALLBACK_BASE_URL}；要指向別處請用 --base-url", file=sys.stderr)
        return FALLBACK_BASE_URL

    srv = cfg.get("server") if isinstance(cfg, dict) else None
    srv = srv if isinstance(srv, dict) else {}
    port = srv.get("port")
    if not port:
        print(f"[warn] {config_path} 的 server.port 不存在，改用 {FALLBACK_BASE_URL}；"
              "要指向別處請用 --base-url", file=sys.stderr)
        return FALLBACK_BASE_URL
    scheme = "https" if srv.get("tls_enabled") else "http"
    return f"{scheme}://127.0.0.1:{port}/api"
