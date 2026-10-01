# ofa77.shop Admin Login: Brute-Force Exposure — No Rate Limit/CAPTCHA + Username Oracle + Seeded Accounts

- ID: `34bcab04-0d0c-4beb-a505-2b61bf4fa81f`
- Severity: **medium**
- Status: open
- Type: Weak Authentication / Brute Force (no rate limiting)
- Target: `https://ofa77.shop/module/admin/unionshop/user/login (admin authentication)`
- Conversation: `167240fc-493e-44b3-b0e2-9d5692aa1da1`
- Created: 2026-09-03 20:44:06.17736466+08:00

## Description

ofa77.shop runs Laravel + UnionCMS/Unishop with APP_DEBUG=true. The admin login at /module/admin/unionshop/user/login has NO rate limiting, NO CAPTCHA, NO account lockout, and a username enumeration oracle (response contains 密碼錯誤 'password wrong' for existing accounts vs 帳號不存在 'account does not exist' for unknown ones, differing by 1 byte). The CMS shipped with 21 valid seeded admin usernames (admin, administrator, root, manager, superadmin, ofa77, admin888, admin1, operator, kefu, service, boss, seller, vendor, finance, test, guest, demo, webmaster, system, user), and the login page exposes no forgot-password/reset flow. An attacker can brute-force credentials at scale with no throttling.

## Reproduction

1. GET https://ofa77.shop/module/admin/unionshop/user/login and extract the _token value. 2. POST to the same URL with _token, username=admin, password=wrongpass1 → response body contains 密碼錯誤 (account exists). 3. POST with username=nonexistentuser12345, password=wrongpass1 → response body contains 帳號不存在 (account does not exist). 4. Repeat POST rapidly 200+ times → no 429, no lockout, no CAPTCHA appears. 5. Observe the response-length/message difference enumerates valid usernames.

## Evidence

Oracle: POST /module/admin/unionshop/user/login with rotating CSRF _token. nonexistentuser12345/wrong → HTTP 200 len=6518 containing 帳號不存在; zzzqqqxxx/wrong → len=6518 帳號不存在; admin/wrong → len=6517 密碼錯誤; root/wrong → len=6517 密碼錯誤; manager/wrong → len=6517 密碼錯誤; test/wrong → len=6517 密碼錯誤; ofa77/wrong → len=6517 密碼錯誤. 21 usernames confirmed to return 密碼錯誤 (exist). 200+ rapid sequential logins produced no 429/lockout/captcha. 523-password × 6-username brute (3138 attempts) completed in ~75s with zero 429s. No forgot/reset link in login HTML (only username+password+_token fields).

## Impact

Combined with APP_DEBUG=true (full path/stack disclosure), the admin panel is exposed to unthrottled online credential brute-forcing against a known set of valid usernames. Given the lack of CAPTCHA and rate limiting, a persistent attacker with a sufficiently large dictionary can eventually compromise an admin account, gaining full store control (order/finance/user management, file upload, potential RCE via admin upload). This is a high-impact authentication weakness.

## Recommendation

Add rate limiting / lockout on /module/admin/unionshop/user/login (e.g., max N failures per IP+account per window, exponential backoff). Add a CAPTCHA after a small number of failures. Use a constant-time, constant-message login response to remove the username oracle. Remove/limit the seeded default admin accounts. Set APP_DEBUG=false in production.
