#!/usr/bin/env python3
"""Host-ops injection for Grok scan turns. Run: python tools/grok_openai_bridge_host_ops_test.py"""
from grok_openai_bridge_slim import HOST_OPS_MARK, apply_host_ops, scan_turn_needs_tools


def test_hello_does_not_force_tools():
    req = {
        "messages": [{"role": "user", "content": "Reply with the single word ok."}],
        "tools": [{"type": "function", "function": {"name": "skill"}}],
    }
    out = apply_host_ops(req)
    assert HOST_OPS_MARK in out["messages"][0]["content"]
    assert out.get("tool_choice") in (None, "auto") or "tool_choice" not in out
    assert not scan_turn_needs_tools(req)


def test_scan_url_forces_required():
    req = {
        "messages": [{"role": "user", "content": "对 http://127.0.0.1/ 做授权范围内侦察"}],
        "tools": [{"type": "function", "function": {"name": "skill"}}],
        "tool_choice": "auto",
    }
    out = apply_host_ops(req)
    assert scan_turn_needs_tools(out)
    assert out["tool_choice"] == "required"
    assert out["messages"][0]["role"] == "system"
    assert HOST_OPS_MARK in out["messages"][0]["content"]


def test_idempotent_system_mark():
    first = apply_host_ops({"messages": [{"role": "user", "content": "hi"}]})
    second = apply_host_ops(first)
    marks = [m for m in second["messages"] if m.get("role") == "system" and HOST_OPS_MARK in m.get("content", "")]
    assert len(marks) == 1


if __name__ == "__main__":
    test_hello_does_not_force_tools()
    test_scan_url_forces_required()
    test_idempotent_system_mark()
    print("ok")
