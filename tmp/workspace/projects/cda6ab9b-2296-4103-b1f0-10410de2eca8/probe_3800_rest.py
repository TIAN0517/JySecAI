#!/usr/bin/env python3
"""
Comprehensive enumeration of 3800 REST endpoints without auth.
GCP mciServer. The /MciTypes /MciCaseRecords already known. Find more.
"""
import requests, urllib3, json, time, sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE = "http://35.234.50.28:3800"

# Common Loopback/Express REST patterns for an EMS (Emergency Medical System)
ENDPOINTS = [
    "/api", "/api/", "/api/users", "/api/roles", "/api/permissions",
    "/api/MciTypes", "/api/MciCaseRecords",
    "/api/hospitals", "/api/ambulances", "/api/cases", "/api/dispatches",
    "/api/v1", "/api/v2",
    "/rest", "/rest/",
    "/hospitals", "/hospitals/list",
    "/ambulances", "/ambulances/list",
    "/cases", "/cases/list",
    "/dispatches", "/dispatches/list",
    "/users", "/users/list", "/users/1", "/users/me",
    "/roles", "/roles/list",
    "/permissions", "/permissions/list",
    "/branches", "/branches/list",
    "/device-roles", "/device-roles/list",
    "/mci", "/mci/list",
    "/mci-types", "/mci-types/list",
    "/mci-case-records", "/mci-case-records/list",
    "/MciTypes", "/MciCaseRecords",
    "/MciType/1", "/MciCaseRecord/1",
    "/MciTypes/count", "/MciCaseRecords/count",
    "/vitalsign", "/vitalsign/list", "/vitalsigns", "/vitalsigns/list",
    "/device", "/devices", "/device/list",
    "/pcr", "/pcr/list", "/pcrs",
    "/ePCR", "/ePCR/list",
    "/notifications", "/notifications/list",
    "/logs", "/audit", "/audit-logs",
    "/config", "/version", "/health", "/healthz",
    "/socket.io", "/socket.io/",
    "/swagger", "/swagger.json", "/api-docs",
    "/debug", "/debug/vars", "/debug/pprof",
    "/metrics", "/stats", "/info",
    "/reset", "/seed", "/fixtures",
    "/upload", "/uploads", "/files",
    "/export", "/import",
    "/internal", "/internal/",
    "/admin", "/admin/",
    "/login", "/logout", "/session",
    "/tokens", "/api/tokens",
    "/mciTypes", "/mciCaseRecords",
    "/MciCaseRecord", "/MciType",
    "/loopback", "/explorer", "/strong-remoting",
]


def req(method, url):
    try:
        r = requests.request(method, url, timeout=5)
        return r.status_code, len(r.text), r.headers.get("Content-Type", ""), r.text[:200]
    except Exception as e:
        return -1, 0, "", f"ERR {e}"


def main():
    print(f"Base={BASE}")
    for ep in ENDPOINTS:
        # GET
        st, l, ct, body = req("GET", BASE + ep)
        if st not in (404,):
            print(f"  GET {ep:40s} -> {st:>4} len={l:>5} ct={ct[:20]:20s} body={body[:80]}")
        # POST (only non-GET if GET was 401/404 or interesting)
        if st in (200, 201, 204):
            st, l, ct, body = req("POST", BASE + ep)
            if st not in (404,):
                print(f"  POST {ep:40s} -> {st:>4} len={l:>5} ct={ct[:20]:20s} body={body[:80]}")


if __name__ == "__main__":
    main()