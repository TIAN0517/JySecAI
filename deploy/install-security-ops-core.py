#!/usr/bin/env python3
"""Incrementally install the governed security-operations UI into JySecAI."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one insertion anchor, found {count}")
    return text.replace(old, new, 1)


def extract_between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    start = text.rfind("\n", 0, start) + 1
    end = text.index(end_marker, start)
    end = text.rfind("\n", 0, end) + 1
    return text[start:end]


def atomic_write(path: Path, content: str) -> None:
    mode = path.stat().st_mode
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: install-security-ops-core.py CORE_ROOT BUNDLE_ROOT", file=sys.stderr)
        return 2
    core = Path(sys.argv[1]).resolve()
    bundle = Path(sys.argv[2]).resolve()

    app_path = core / "internal/app/app.go"
    rbac_path = core / "internal/security/rbac_middleware.go"
    index_path = core / "web/templates/index.html"
    router_path = core / "web/static/js/router.js"
    handler_path = core / "internal/handler/security_ops.go"
    js_path = core / "web/static/js/security-ops.js"
    css_path = core / "web/static/css/security-ops.css"
    reference_index = (bundle / "reference-index.html").read_text(encoding="utf-8")
    reference_style = (bundle / "reference-style.css").read_text(encoding="utf-8")

    app = app_path.read_text(encoding="utf-8")
    app = replace_once(
        app,
        "\tterminalHandler := handler.NewTerminalHandler(log.Logger)\n",
        "\tterminalHandler := handler.NewTerminalHandler(log.Logger)\n"
        "\tsecurityOpsHandler := handler.NewSecurityOpsHandler(log.Logger)\n"
        "\tsecurityOpsHandler.SetAudit(auditSvc)\n",
        "handler initialization",
    )
    app = replace_once(
        app,
        "\t\tfofaHandler,\n\t\tterminalHandler,\n\t\tapp.c2Handler,\n",
        "\t\tfofaHandler,\n\t\tterminalHandler,\n\t\tsecurityOpsHandler,\n\t\tapp.c2Handler,\n",
        "setupRoutes call",
    )
    app = replace_once(
        app,
        "\tfofaHandler *handler.FofaHandler,\n\tterminalHandler *handler.TerminalHandler,\n\tc2Handler *handler.C2Handler,\n",
        "\tfofaHandler *handler.FofaHandler,\n\tterminalHandler *handler.TerminalHandler,\n"
        "\tsecurityOpsHandler *handler.SecurityOpsHandler,\n\tc2Handler *handler.C2Handler,\n",
        "setupRoutes signature",
    )
    routes = (
        "\n\t\t// Governed Web security operations.\n"
        "\t\tprotected.GET(\"/security-ops/catalog\", securityOpsHandler.Catalog)\n"
        "\t\tprotected.GET(\"/security-ops/runs\", securityOpsHandler.ListRuns)\n"
        "\t\tprotected.POST(\"/security-ops/runs\", securityOpsHandler.CreateRun)\n"
        "\t\tprotected.GET(\"/security-ops/runs/:runId\", securityOpsHandler.GetRun)\n"
        "\t\tprotected.GET(\"/security-ops/runs/:runId/events\", securityOpsHandler.ListEvents)\n"
        "\t\tprotected.GET(\"/security-ops/runs/:runId/artifacts\", securityOpsHandler.ListArtifacts)\n"
        "\t\tprotected.GET(\"/security-ops/projects/:projectId/findings\", securityOpsHandler.ListFindings)\n"
        "\t\tprotected.POST(\"/security-ops/runs/:runId/approve\", security.RequirePermission(\"hitl:write\"), securityOpsHandler.ApproveRun)\n"
        "\t\tprotected.POST(\"/security-ops/runs/:runId/cancel\", securityOpsHandler.CancelRun)\n"
    )
    app = replace_once(
        app,
        "\t\tprotected.DELETE(\"/batch-tasks/:queueId\", agentHandler.DeleteBatchQueue)\n",
        "\t\tprotected.DELETE(\"/batch-tasks/:queueId\", agentHandler.DeleteBatchQueue)\n" + routes,
        "security routes",
    )

    rbac = rbac_path.read_text(encoding="utf-8")
    rbac = replace_once(
        rbac,
        "\tcase strings.HasPrefix(path, \"/agent-loop\"), strings.HasPrefix(path, \"/batch-tasks\"):\n\t\treturn crudPermission(method, \"tasks\")\n",
        "\tcase strings.HasPrefix(path, \"/agent-loop\"), strings.HasPrefix(path, \"/batch-tasks\"):\n"
        "\t\treturn crudPermission(method, \"tasks\")\n"
        "\tcase strings.HasPrefix(path, \"/security-ops\"):\n\t\treturn crudPermission(method, \"tasks\")\n",
        "RBAC mapping",
    )

    nav = extract_between(
        reference_index,
        '<div class="nav-item" data-page="security-ops"',
        '<div class="nav-item" data-page="tasks"',
    )
    page = extract_between(
        reference_index,
        "<!-- Web 安全扫描工作台 -->",
        "<!-- 任务管理页面 -->",
    )
    index = index_path.read_text(encoding="utf-8")
    if 'data-page="security-ops"' not in index:
        index = replace_once(index, '                    <div class="nav-item" data-page="tasks">\n', nav + '                    <div class="nav-item" data-page="tasks">\n', "navigation")
    if 'id="page-security-ops"' not in index:
        index = replace_once(index, "                <!-- 任务管理页面 -->\n", page + "                <!-- 任务管理页面 -->\n", "page")
    if "security-ops.css" not in index:
        style_line = next(line for line in index.splitlines(keepends=True) if "/static/css/style.css" in line)
        index = replace_once(index, style_line, style_line + '    <link rel="stylesheet" href="/static/css/security-ops.css?v=20260907-1">\n', "stylesheet")
    if "security-ops.js" not in index:
        index = replace_once(index, '    <script src="/static/js/tasks.js"></script>\n', '    <script src="/static/js/tasks.js"></script>\n    <script src="/static/js/security-ops.js?v=20260907-1"></script>\n', "script")

    router = router_path.read_text(encoding="utf-8")
    router_lines = []
    for line in router.splitlines(keepends=True):
        if ".includes(pageId)" in line and "'tasks'" in line and "'security-ops'" not in line:
            line = line.replace("'tasks',", "'tasks', 'security-ops',", 1)
        router_lines.append(line)
    router = "".join(router_lines)
    router = replace_once(
        router,
        "        case 'mcp-monitor':\n",
        "        case 'security-ops':\n"
        "            if (typeof initSecurityOpsPage === 'function') {\n"
        "                initSecurityOpsPage();\n"
        "            }\n"
        "            break;\n"
        "        case 'mcp-monitor':\n",
        "router initialization",
    )

    css_marker = "/* Governed Web security operations workbench */"
    css = reference_style[reference_style.index(css_marker):]

    planned = {
        app_path: app,
        rbac_path: rbac,
        index_path: index,
        router_path: router,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = core / "backups" / f"security-ops-{stamp}"
    backup.mkdir(parents=True, mode=0o700)
    for path in planned:
        relative = path.relative_to(core)
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    for path, content in planned.items():
        atomic_write(path, content)
    shutil.copy2(bundle / "security_ops.go", handler_path)
    shutil.copy2(bundle / "security-ops.js", js_path)
    css_path.write_text(css, encoding="utf-8")
    print(f"installed security operations UI; backup={backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
