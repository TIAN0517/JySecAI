# Hermes Handoff: Taipei 119 Broadcast

## Required behavior

- Broadcast only newly observed, real-time Taipei incident-scene addresses.
- Send every accepted message through both enabled Telegram Bot routes.
- Exclude fire stations, hospitals, clinics, police facilities, institutions,
  departed-scene records, hospital arrivals, and other non-scene locations.
- Treat OHCA as suspected when explicit cardiac-arrest text exists or ambulances
  from at least two distinct stations are dispatched to the same accepted address.
- Telegram OHCA messages display only `疑似 OHCA`; do not display the internal
  classification reason.
- Never use `fuzzyX/fuzzyY` to manufacture a complete doorplate.

## Active architecture

- Canonical feed: authenticated
  `https://service119.tfd.gov.tw/service119/citizenCase/search`.
- Login/session entry: `https://service119.tfd.gov.tw/service119/ews1821`,
  maintained by `login.py`.
- Corroboration feed:
  `https://service119.119.gov.taipei/service119/citizenCase/caseList`.
- A coordinate-derived address requires matching time through seconds, matching
  any shared case identifiers, and `csX/csY` within one metre in both feeds.
- Production unit: `tpe-broadcast-multibot.service`, 10-second interval,
  `--skip-existing-on-start` enabled.
- Legacy `tpe119-push.service` must remain inactive.

## Current blocker observed on 2026-10-01

The authorized one-time backfill fetched 10 authenticated rows, one active public
row with exact coordinates, and one successful cross-feed correlation. Zero
records passed the final address gate:

- authenticated rows without a source doorplate lacked corroborated exact
  coordinates;
- the single reverse result was not classified as an address-level feature;
- the IPS record was outside Taipei.

No incident message was sent by the backfill. Do not report Bot failure: both
routes pass `getMe`, `getChat`, and `getChatMember`; each Bot is an administrator
of its configured supergroup. A one-time service-status message was successfully
sent to both groups. Earlier production deliveries logged `2/2 routes delivered`.

## Files and validation

- Address policy: `scene_policy.py`
- Source integration and sender: `broadcast_daemon.py`
- Reverse geocoding: `geocoding.py`
- Multi-Bot transport: `multi_dispatcher.py`
- Tests: `test_scene_policy.py`, `test_broadcast_safety.py`
- Detailed report: `data/reports/tpe_scene_address_verification_20261001.md`

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  test_scene_policy.py test_broadcast_safety.py
```

Thirteen tests currently pass. The latest floor/doorplate normalization converts
reverse-geocoder artifacts such as `30號二樓號` to `30號二樓` and
`132樓2號` to `132號2樓`.

## Next investigation

Find a source-supported way to obtain an address-level result for exact
`csX/csY` without accepting fuzzy coordinates or nearby POIs. Keep the
authenticated search row as the canonical incident. Any relaxation must still
prove the returned doorplate belongs to the incident coordinate and must not
turn a nearby building into the reported scene.
