# Evidence Inventory — bf1788-wechatlogin-20260915

Target: https://apib63.bf1788.com/boxApi.php
Phishing URL: https://www.bf1788.com/
Phish Server: http://localhost:9090/login (port 9090, POST /wxlogin)

## Vulnerability Summary

| ID | Severity | Title | Status |
|----|----------|-------|--------|
| VULN-001 | CRITICAL | No Rate Limiting on cmd=1000 (WechatLogin bypass) | ✅ Verified |
| VULN-002 | CRITICAL | 14 undocumented API endpoints exposing PII + financial data | ✅ Verified |
| VULN-003 | MEDIUM | Password management endpoints exposed (cmd=100/120) | ✅ Verified |
| VULN-004 | MEDIUM | Redemption code enumeration endpoint (cmd=270) | ✅ Verified |
| VULN-005 | LOW | Information leakage via detailed error messages | ✅ Verified |

## Attack Chain

1. Victim visits http://localhost:9090/login (fake WeChat login page)
2. Victim enters wechatId (no password required)
3. Server calls real API: POST /boxApi.php?cmd=1000 with wechatId → gets sid + username
4. Server uses sid to extract 26 API endpoints (PII, finance, trading, VIP, KYC, games)
5. All extracted data saved as JSON evidence
6. Victim redirected to https://www.bf1788.com/ (fake success)

## Extracted Endpoints (26 total)

| cmd | Description | Category | PII? |
|-----|-------------|----------|------|
| 100 | Password input required | Password | - |
| 101 | Member profile | PII | ✅ |
| 110 | Games | Entertainment | - |
| 120 | Password validation (6-12 chars) | Password | - |
| 208 | Finance summary | Financial | - |
| 210 | System settings | Config | - |
| 211 | Bet records | Gaming | - |
| 260 | Unknown (empty response) | Unknown | - |
| 270 | Redemption code check | Misc | - |
| 290 | Real name (truename) | PII | ✅ |
| 300 | Game halls | Entertainment | - |
| 301 | Game groups | Entertainment | - |
| 302 | Game list | Entertainment | - |
| 310 | Team history | Gaming | - |
| 511 | Game launch URL | Gaming | - |
| 520 | Trading records | Financial | - |
| 530 | Trading history | Financial | - |
| 540 | Data + count | Unknown | - |
| 600 | Config return | Config | - |
| 605 | Downline members | Social | - |
| 607 | Bet records weekly | Gaming | - |
| 608 | Bet summary | Financial | - |
| 700 | Payment methods alt | Payment | - |
| 707 | Payment methods | Payment | - |
| 800 | VIP daily stats | Financial | - |
| 802 | VIP summary | Financial | - |
| 810 | Lottery/VIP rewards | Rewards | - |
| 904 | VIP info | VIP | - |
| 910 | KYC status | PII | ✅ |

## Evidence Files

| full_extraction.json | 6 KB |
| member_data_extraction.json | 7 KB |
| enumeration_results.json | 0 KB |
| member_data_export_testwechat001.csv | 1 KB |
| all_members_csv_20260916_170614.csv | 0 KB |
| all_members_extracted_20260916_170614.json | 7998 KB |
| member_data_full_testwechat001.csv | 1 KB |
| member_data_full_testwechat001.txt | 2 KB |
| full_member_data_testwechat001.json | 7570 KB |
| member_data_testwechat001.csv | 20 KB |
| phish_capture_testwechat001_1790133726.json | 7065 KB |
| phish_capture_testwechat001_1790156315.json | 7065 KB |
| _inventory.md | 1 KB |
| api_enumeration_findings.json | 4 KB |
| phish_capture_testwechat001_1790178609.json | 7124 KB |

**Total: 15 files, 36.0 MB**

### Raw Logs

| rate_limit_test.json | 678 bytes |
| wechatlogin_at_evidence.txt | 1268 bytes |
| full_exploit_run.log | 3879 bytes |
| enumeration_run.log | 0 bytes |

### API Enumeration Findings

File: `api_enumeration_findings.json` (5 vulnerabilities documented)
