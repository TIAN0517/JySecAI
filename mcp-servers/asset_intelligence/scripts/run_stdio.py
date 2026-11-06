#!/usr/bin/env python3
"""Asset Intelligence MCP stdio 進入點。

stdout 僅供 MCP 協定使用;所有日誌輸出到 stderr 並經金鑰遮蔽。
"""
import sys
from pathlib import Path

# 允許以指令碼方式直接執行 (不要求安裝為套件)
_PKG_PARENT = Path(__file__).resolve().parent.parent.parent  # .../mcp-servers
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from asset_intelligence.server import main  # noqa: E402

if __name__ == "__main__":
    main()
