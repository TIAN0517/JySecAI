# Taipei Real-Time Scene Address Verification

## Production flow

1. `login.py` signs in through `https://service119.tfd.gov.tw/service119/ews1821`
   and reads the authenticated `citizenCase/search` feed.
2. The daemon treats that feed as the canonical real-time incident source.
3. A record that already contains a complete doorplate keeps that source value.
4. A record without a complete doorplate must match a current public `caseList`
   row by time (through seconds), any shared case identifiers, and exact TWD97
   `csX/csY` coordinates within one metre.
5. Only a matched exact coordinate may be reverse-geocoded. `fuzzyX/fuzzyY` are
   excluded.

## Address acceptance rules

- Eligible statuses: `已出勤`, `到達現場`, and IPS `處理中`.
- Later lifecycle records such as `離開現場` and `到達醫院` are rejected.
- Fire stations, hospitals, clinics, police facilities, care institutions, and
  similar named locations are rejected in both source and geocoder metadata.
- A reverse result needs a doorplate, address-level feature type, non-approximate
  geometry, matching road when available, and a returned point within 35 metres.
- Ordinary and suspected-OHCA broadcasts use the same final address gate.

## Live verification on 2026-10-01

The authenticated and public endpoints each returned six current rows. Active
rows exposed only `fuzzyX/fuzzyY`; the only row exposing exact `csX/csY` had
already left the scene. Therefore zero coordinate-derived addresses were eligible
in that check. This is the expected fail-closed behavior: the daemon waits for a
new active record with exact coordinates instead of turning a fuzzy map point
into a false doorplate.

## OHCA and delivery

The Telegram message displays only `疑似 OHCA`. Internally, the alert still
requires an explicit cardiac-arrest signal or ambulance dispatches from at least
two distinct stations at the same accepted scene address. Enabled multi-bot
routes are sent independently; a case is marked delivered only after every route
succeeds.

## Validation

`python3 -m unittest -v test_scene_policy.py test_broadcast_safety.py` passes 12
tests covering source correlation, coordinate mismatch rejection, institution
blocking, reverse-distance checks, original-address preservation, OHCA text, and
nearby-but-different address separation.
