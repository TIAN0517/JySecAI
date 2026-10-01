#!/bin/bash
B="https://epcr.tpf.gov.tw:4004/ssoLogin"
curl -sk -H "Content-Type: application/json" --max-time 10 -d '{}' "$B" -w ' [%{http_code} %{size_download}]\n'
curl -sk -H "Content-Type: application/json" --max-time 10 -d '{"a":"b"}' "$B" -w ' [%{http_code} %{size_download}]\n'
curl -sk -H "Content-Type: application/json" --max-time 10 -d '{"sessionId":"abc123"}' "$B" -w ' [%{http_code} %{size_download}]\n'
curl -sk -H "Content-Type: application/json" --max-time 10 -d '{"sessionId":"8f14e45f-ceea-467f-8f0e-1b4d9c8a5f2a"}' "$B" -w ' [%{http_code} %{size_download}]\n'
curl -sk -H "Content-Type: application/json" --max-time 10 -d '{"sessionId":""}' "$B" -w ' [%{http_code} %{size_download}]\n'
curl -sk -H "Content-Type: application/json" --max-time 10 -d '{"sessionId":"1"}' "$B" -w ' [%{http_code} %{size_download}]\n'
