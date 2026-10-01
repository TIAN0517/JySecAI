# TOCP Broadcast Core — GUI Package

## Core Files (in /core/)
- `broadcast_daemon.py`        — Main daemon: polling loop, scene dispatch + IPS extraction orchestration
- `ips_dispatch_handler.py`    — IPS (Taipei FD) extraction: login via OCR, CaseUnitMgt fetch, proxy rotation
- `login.py`                   — Login daemon: OCR captcha solve + JWT token auto-renewal (3h lifetime)
- `scene_policy.py`            — Scene dispatch filtering & push policy
- `geocoding.py`               — Address geocoding (WGS84 ↔ TWD97, reverse geocode)
- `multi_dispatcher.py`        — Multi-city dispatch routing
- `tocp_tpe_broadcast.py`      — TOCP broadcast: JWT forge (TOCP_JWT_SECRET), Telegram push
- `start_daemon.sh`            — Auto-restart wrapper script

## Config + Env (in /config/)
- `tpe_service119_live.env`    — **ENV KEYS**: proxy creds, TOCP JWT secret, TPE 119 credentials, API endpoints
- `bot_routes.json`            — Telegram bot token routing (per-city bots)
- `headers.txt`               — HTTP headers for Service119 requests
- `gui_branding.py`           — Branding constants for GUI

## Runtime (in /runtime/)
- `tpe119_token.json`         — Current JWT token + session cookie
- `ips_cookies.json`          — IPS session cookies (ScraperProxy-authed)

## Key Architecture
- IPS extraction uses SCRAPER_PROXY (ScraperProxy HTTP, Taiwan residential rotation) — see PROXY_LIST in ips_dispatch_handler.py
- Scene dispatch uses direct connection (no proxy)
- Daemon polls every 60s, auto-restarts via start_daemon.sh

## Dependencies
```
pip install ddddocr requests urllib3
```

## GUI Development
- Import from core/: `broadcast_daemon`, `ips_dispatch_handler`, `tocp_tpe_broadcast`
- Bot config: `bot_routes.json` + `tocp_tpe_broadcast.TELEGRAM_BOTS`
- Status port: 58888 (HTTP JSON status for monitoring)
