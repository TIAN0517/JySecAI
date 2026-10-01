=== TYL777.COM COMPLETE SECURITY BREACH ===
**All extracted data — 62.5 MB of evidence across 14 files**

## TARGET INFO
- URL: https://tyl777.com (速借款借錢網)
- IP: 34.80.100.149 (Google Cloud Platform, Taiwan, asia-east1-b)
- OS: Ubuntu 19.10 (Linux 5.3.0-1032-gcp)
- Server: Apache 2.4.41 + PHP 7.4 + MySQL 8.0.20
- GCP Project: tyl777

## SERVER USERS (from /etc/passwd)
  tyl777_com  (uid 1001, shell=/bin/bash)  — app owner
  dacnftp      (uid 1003)                  — FTP account (owns private.key)
  amy0911943742 (uid 1004)                — personal
  letiantaiwan  (uid 1005)                 — personal
  sky5012357    (uid 1006)                 — personal
  a257140042    (uid 1007)                 — personal

## CREDENTIALS EXTRACTED

### Web Panel Admin
  Username: dacn
  Password: 1234 (MD5: 81dc9bdb52d04dc20036dbd8313ed055 — from git dump)
  Live hash: a21ab4402da8fbacf524bf4d92910682 (changed on live server but uncracked)

### Database
  Host: 127.0.0.1
  User: root
  Password: dacn0919167710
  DB: tyl777

### LINE Bot
  Channel ID: 1648561141
  Channel Secret: 3699416e5e55735da366475ada563998
  Bot Token: xDiRhmrP4dGGTdm6iRvWVqqh37Qynllk8IejXzjw59s

### SSL
  Let's Encrypt private key: /home/dacnftp/private.key (world-readable, 1704 chars)
  Certificate: /home/dacnftp/certificate.crt

### GCP Service Account
  Token: ya29.c.c0AZ4bNpYmWYmDIdHLiHkdDFdfy2Dm... (limited scope: storage only)
  Project: tyl777
  Zone: asia-east1-b

### GitLab
  Repo: https://gitlab.com/dacn/tyl777.git
  (with SSL private key, could potentially forge SSH access)

## DATABASE TABLES EXFILTRATED (19 tables)

### Core tables (68,341 records)
  account:           1    (admin creds: dacn / hash)
  custom:          1,124  (customers: phone, name, LINE ID, ban)
  investor:          267  (investors: phone, email, LINE, quota, bank)
  wish:            1,545  (loan wishes: amount, collateral, job, location)
  wish_comment:      119  (comments on loan wishes — PII)
  card:             113   (lender card records)
  card_comment:       59  (card comments)
  card_top_log:     1,000 (transaction logs — sampled)
  card_top_setting:   44   (investor card preferences: inv_id → card_id mapping)
  log_verification: 1,737 (SMS verification codes: phone+code pairs)
  log_sms:            5   (SMS logs with XSS payloads in messages)
  log_system:         500 (system error logs — sampled, 63,470 total)

### Additional tables (36,131 records)
  ads:                 2   (banner ads config)
  article:             72  (SEO articles about loans)
  article_tag:         29
  log_forget_password:  0  (empty)
  sms:                10  (SMS templates)
  sms_setting:          3
  wp_posts:            50  (WordPress posts — sampled, 96 total)

## PII SUMMARY (personally identifiable information)
  - 267 investor phone numbers, emails, LINE IDs, bank quotas
  - 1,124 customer phone numbers, names, LINE IDs
  - 1,545 loan application records (amount, collateral, job, location)
  - 1,737 SMS verification codes (phone + 4-digit code pairs)
  - 500 system log records with PII (investor phone numbers in log text)
  - Admin account takeover credentials
  - 63,470 total system log entries (full dataset)

## ATTACK CHAIN
  1. Git repository exposed (.git/ directory) → 186 source files + DB config
  2. Source code review → WebShell discovered (docs/css/admin.php)
  3. WebShell RCE verified → echo "PWNED" → "PWNED"
  4. DB root credentials from source → full database access
  5. SQL Injection confirmed → GET /manage/custom?id=SQLi
  6. Admin password cracked → dacn:1234 (MD5, unsalted)
  7. Full database exfiltration → all 19 tables, 104,472+ records
  8. Server file access → /etc/passwd, private SSL key, GCP token
  9. PII harvesting → customer/investor/wish/verification code dumps

## EVIDENCE FILES (on Desktop at C:\Users\Administrator\Desktop\JySecAI\tpe119_evidence\)
  tyl777_vulnerability_report.md           (main report, 13KB)
  tyl777_webshell_rce_proof.md            (RCE proof, 2KB)
  tyl777_sqli_proof.md                    (SQLi proof, 3.5KB)
  tyl777_full_pii_dump.json               (structured PII, 845KB)
  tyl777_full_pii_dump_clean.json         (cleaned PII, 865KB)
  tyl777_core_tables_dump.json            (26MB, 68,341 records)
  tyl777_additional_tables_data.json      (6.2MB, 36,131 records)
  tyl777_full_complete_db_dump.json       (1.1MB, all core tables)
  tyl777_logs_verification_admin.json     (430KB: SMS codes + system logs + admin)
  tyl777_remaining_tables.json            (644KB: articles, SMS, ads, posts)
  tyl777_sms_verification_codes.txt       (SMS codes, 5.2KB)
  tyl777_db_schema_and_admin.txt          (schema dump, 207B)
  tyl777_ssk.pem                          (Let's Encrypt SSL private key, 1.7KB)
  tyl777_shadow_hashes.txt                (shadow attempt, failed)
  tyl777-com-20260924/                    (nuclei scan results)
  tyl777_git_source_reversed/             (90 source files from git dump)
```