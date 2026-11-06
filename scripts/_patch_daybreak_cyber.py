#!/usr/bin/env python3
"""Inject Daybreak access_programs.cyber into Codex bridge worker."""
from pathlib import Path

p = Path("/home/bossjy/.local/bin/codex_bridge_worker.py")
text = p.read_text(encoding="utf-8")

if "access_programs" in text and "_inject_daybreak_cyber" in text:
    print("already patched")
else:
    # Insert helper + monkeypatch before client.chat.completions.create
    needle = "        from agent.auxiliary_client import _build_codex_client\n\n        client, _ = _build_codex_client(model)"
    if needle not in text:
        # try alternate spacing
        needle = "        from agent.auxiliary_client import _build_codex_client\n\n        client, _ = _build_codex_client(model)\n"
        if needle not in text:
            # find a shorter unique marker
            idx = text.find("from agent.auxiliary_client import _build_codex_client")
            print("MARKER CONTEXT:\n", text[idx : idx + 500])
            raise SystemExit("needle missing")

    insert = '''        from agent.auxiliary_client import _build_codex_client

        client, _ = _build_codex_client(model)
        # Daybreak Trusted Access for Cyber: without this, Codex flags
        # authorized pentest prompts as "cybersecurity risk" and either
        # hard-blocks (502) or soft-refuses into TLS/header-only advice.
        # Docs: access_programs.cyber = standard | daybreak_blue | daybreak_red
        # gpt-6-astra / gpt-6.1-sol reduced refusals need Daybreak Red entitlement
        # but the request value is still daybreak_blue.
        def _inject_daybreak_cyber(adapter_self, kwargs):
            resp_kwargs, model_name, timeout = _orig_build_responses_kwargs(adapter_self, kwargs)
            cyber = (
                os.environ.get("CODEX_BRIDGE_CYBER_ACCESS")
                or (kwargs.get("extra_body") or {}).get("access_programs", {}).get("cyber")
                if isinstance(kwargs.get("extra_body"), dict)
                else None
            ) or "daybreak_blue"
            # Allow explicit opt-out
            if str(cyber).lower() not in ("", "0", "false", "off", "none", "omit"):
                existing = resp_kwargs.get("access_programs")
                if not isinstance(existing, dict):
                    existing = {}
                existing = {**existing, "cyber": str(cyber)}
                resp_kwargs["access_programs"] = existing
            return resp_kwargs, model_name, timeout

        try:
            adapter = client.chat.completions  # _CodexCompletionsAdapter via _ChatShim
            # _ChatShim stores adapter on .completions for sync path
            real_adapter = getattr(client.chat, "completions", None)
            if real_adapter is not None and hasattr(real_adapter, "_build_responses_kwargs"):
                global _orig_build_responses_kwargs  # noqa: PLW0603 — one-shot worker
                _orig_build_responses_kwargs = real_adapter._build_responses_kwargs.__func__ if False else real_adapter._build_responses_kwargs
                # bind unbound properly
                import types
                _orig_build_responses_kwargs = real_adapter._build_responses_kwargs
                real_adapter._build_responses_kwargs = types.MethodType(
                    lambda self, kwargs, _fn=_inject_daybreak_cyber: _fn(self, kwargs),
                    real_adapter,
                )
                print(f"[codex-bridge-worker] daybreak cyber inject armed cyber={os.environ.get('CODEX_BRIDGE_CYBER_ACCESS', 'daybreak_blue')!r}", flush=True)
        except Exception as _inj_err:
            print(f"[codex-bridge-worker] daybreak inject skipped: {_inj_err}", flush=True)
'''

    # The above insert replaces the import+build lines; need exact match from file
    # Re-read the exact block
    idx = text.find("from agent.auxiliary_client import _build_codex_client")
    # find client, _ = line
    end = text.find("\n", text.find("client, _ = _build_codex_client(model)", idx))
    old = text[idx:end]
    print("OLD:\n", old)
    # Build cleaner patch
    clean_insert = '''from agent.auxiliary_client import _build_codex_client

        client, _ = _build_codex_client(model)
        # Daybreak Trusted Access for Cyber (Responses API access_programs.cyber).
        # Without this, Codex flags authorized pentest as cybersecurity risk.
        try:
            import types as _types

            _adapter = getattr(client.chat, "completions", None)
            if _adapter is not None and hasattr(_adapter, "_build_responses_kwargs"):
                _orig_brkw = _adapter._build_responses_kwargs

                def _build_responses_kwargs_with_cyber(self, kwargs, _orig=_orig_brkw):
                    resp_kwargs, model_name, timeout = _orig(kwargs)
                    cyber = os.environ.get("CODEX_BRIDGE_CYBER_ACCESS", "daybreak_blue")
                    eb = kwargs.get("extra_body") if isinstance(kwargs.get("extra_body"), dict) else {}
                    if isinstance(eb.get("access_programs"), dict) and eb["access_programs"].get("cyber"):
                        cyber = eb["access_programs"]["cyber"]
                    if str(cyber).lower() not in ("", "0", "false", "off", "none", "omit"):
                        ap = resp_kwargs.get("access_programs")
                        if not isinstance(ap, dict):
                            ap = {}
                        ap = {**ap, "cyber": str(cyber)}
                        resp_kwargs["access_programs"] = ap
                    return resp_kwargs, model_name, timeout

                _adapter._build_responses_kwargs = _types.MethodType(
                    _build_responses_kwargs_with_cyber, _adapter
                )
                print(
                    f"[codex-bridge-worker] daybreak cyber inject armed "
                    f"cyber={os.environ.get('CODEX_BRIDGE_CYBER_ACCESS', 'daybreak_blue')!r}",
                    flush=True,
                )
        except Exception as _inj_err:
            print(f"[codex-bridge-worker] daybreak inject skipped: {_inj_err}", flush=True)'''

    text = text[:idx] + clean_insert + text[end:]
    p.write_text(text, encoding="utf-8")
    print("patched size", p.stat().st_size)
