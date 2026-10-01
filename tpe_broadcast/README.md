# TOCP 119 Broadcast Daemon

Real-time Taipei 119 emergency dispatch monitoring + Telegram broadcast.

## Quick Start

    # One-click: pass bot token, group auto-bound via getUpdates
    python3 broadcast_daemon.py --tg-bot-token <TOKEN> --interval 10 --city 01

    # With auto-restart wrapper
    ./start_daemon.sh --tg-bot-token <TOKEN> --interval 10 --city 01

    # Traffic routing: separate OHCA and dispatch groups
    python3 broadcast_daemon.py --tg-bot-token <TOKEN> --ohca-group-id -100XXX --dispatch-group-id -100YYY

    # Multi-city: run all configured cities concurrently
    python3 broadcast_daemon.py --tg-bot-token <TOKEN> --all-cities --interval 10

## GUI Control Panel

    python3 tpe_broadcast_gui.py

    Features:
    - Checkbox-based city selection (台北/桃園/高雄)
    - Bot health monitoring (green/red/灰 status indicators)
    - Multi-group routing configuration
    - Start/stop daemon + auto-start toggle
    - Polls daemon HTTP status server per-city (ports 58888 + 城市序號)
    - Multi-city support: 勾選 2+ 縣市 → 同時監控多個縣市 (each on own daemon thread)

## Data Sources

| Source          | Endpoint                                      | Auth    | Coords  |
|---------------|-------------------------------------------------------------------|---------|---------|
| IPS dispatch    | https://163.29.181.230:8443/... | CAPTCHA   | TWD97   |
| service119 API  | `https://service119.tfd.gov.tw/service119/citizenCase/search` | ews1821 session | TWD97 |
| caseList        | https://service119.119.gov.taipei/service119/citizenCase/caseList | NONE    | TWD97   |

`citizenCase/search` is the canonical incident source. `login.py` maintains the
`ews1821` login session. When a login record has no complete doorplate, the daemon
requires a current `caseList` record with the same second, compatible case ID, and
`csX/csY` within one metre. It then reverse-geocodes those exact coordinates.
`fuzzyX/fuzzyY` are never used to manufacture a doorplate.

Precise records are eligible at `已出勤` or `到達現場`. The persistent case key
prevents a second push when the same incident later changes to `到達現場`.
`離開現場`, hospital and return-to-station statuses are excluded.

## OHCA Classification

OHCA alerts display only the label `疑似 OHCA`.
They require either an explicit OHCA/cardiac-arrest phrase in the source case
type or two or more distinct stations dispatching ambulances to the same
incident address. Station names are deduplicated before counting.
`caseList.dpKdid` is a public-location classification and is never counted as
an ambulance. Same-address rows alone do not trigger an OHCA alert.

All alerts use real dispatch records; there are no simulated incidents in the
production daemon. `_ohca_addr_keys` prevents repeated alerts for one address.

## Process Safety

- File-based lock (/tmp/broadcast_daemon.lock) prevents multiple instances
- start_daemon.sh auto-restarts on crash with 5s delay
- Dedup state persisted in /tmp/broadcast_pushed_cases.json (survives restart)

## Scene-address policy

The sender accepts only active incident records (`已出勤`, `到達現場`, or IPS
`處理中`). Source addresses containing station, hospital, clinic, police,
long-term-care, or similar institution terms are rejected. Reverse results must
contain a doorplate, match the source road when present, be within 35 metres of
the query point, and identify an address-level feature. Address checks are shared
by regular and suspected-OHCA messages.

The production `--city 01` path is fail-closed to Taipei: the final accepted
address must explicitly contain `臺北市`. IPS mutual-aid incidents outside Taipei
are rejected before geocoding, and reverse-geocoded results outside Taipei are
rejected before Telegram delivery.

## CLI Args

    --tg-bot-token    Telegram bot token (one-click config)
    --group-id        Override group ID (auto-discovered from getUpdates if omitted)
    --ohca-group-id   Route OHCA alerts to separate group (comma-separated for multiple)
    --dispatch-group-id  Route regular dispatches to separate group (comma-separated)
    --interval       Polling interval seconds (default 60)
    --city           City code: 01=Taipei, 05=Taoyuan, 11=Kaohsiung
    --all-cities     Run daemon loops for ALL configured cities (each on own status port)
    --status-port    HTTP status server base port (default: 58888, +city_index for multi)
