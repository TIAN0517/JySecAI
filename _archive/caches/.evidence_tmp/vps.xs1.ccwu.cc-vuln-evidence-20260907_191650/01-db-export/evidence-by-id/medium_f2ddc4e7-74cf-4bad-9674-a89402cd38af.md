# ofa377 member SPA: hardcoded AES-ECB key exposes "remember me" plaintext credentials

- ID: `f2ddc4e7-74cf-4bad-9674-a89402cd38af`
- Severity: **medium**
- Status: open
- Type: Insecure Client-Side Cryptography / Hardcoded Secret
- Target: `https://ofa1777.ofa377.net/ (member SPA bundle /assets/index-DKOcotyo.js) — ofa377.net / ofa1777 / ofa88kh / ofa168my build family`
- Conversation: `167240fc-493e-44b3-b0e2-9d5692aa1da1`
- Created: 2026-09-03 23:18:11.811843533+08:00

## Description

The member SPA JS bundle (https://ofa1777.ofa377.net/assets/index-DKOcotyo.js, and the same build family across ofa377.net / ofa1777 / ofa88kh / ofa168my) contains a client-side encryption helper Xf={encrypt(e,t){t=t||"absoietlj32fai12"; ... Bo.AES.encrypt(o,n,{mode:Bo.mode.ECB,padding:Bo.pad.Pkcs7,...}}. It uses AES-ECB with a HARDCODED DEFAULT KEY "absoietlj32fai12" embedded in client-visible code. The login flow stores localStorage.setItem("token",Xf.encrypt(s.data.token)) and the remember-me flow stores localStorage.setItem("account",Xf.encrypt(e)); localStorage.setItem("password",Xf.encrypt(t)) — i.e. the member's plaintext username and password are persisted client-side, "protected" only by this public-key ECB cipher.

## Reproduction

1. Download the member bundle: curl -sk https://ofa1777.ofa377.net/assets/index-DKOcotyo.js -o app.js. 2. grep for the helper: grep -oE 'Xf=\{encrypt[^}]{0,200}' app.js  -> shows t=t||"absoietlj32fai12" and mode:Bo.mode.ECB. 3. grep -oE 'localStorage.setItem\("password"[^)]*\)' app.js -> shows Xf.encrypt(t) storing the password. 4. Decrypt a captured remember-me password with node: require('crypto'); AES-128-ECB, key="absoietlj32fai12", PKCS7, over the Base64 localStorage value.

## Evidence

ofa1777_index.js (1,820,803 bytes, downloaded from /assets/index-DKOcotyo.js):
  Xf={encrypt(e,t){t=t||"absoietlj32fai12";const n=Bo.enc.Utf8.parse(t),o=Bo.enc.Utf8.parse(e);return Bo.AES.encrypt(o,n,{mode:Bo.mode.ECB,padding:Bo.pad.Pkcs7
  Ot.interceptors.request.use(e=>{const t=Xf.decrypt(localStorage.getItem("token")??"");return t&&(e.headers.Authorization=`Bearer $
  ...localStorage.setItem("token",Xf.encrypt(s.data.token)),localStorage.setItem("userId",s.data.user_id)...
  ...n?(localStorage.setItem("account",Xf.encrypt(e)),localStorage.setItem("password",Xf.encrypt(t)))...
The key string "absoietlj32fai12" appears literally in the shipped bundle; AES mode is ECB (deterministic).

## Impact

The remember-me feature persists the member's plaintext password in localStorage encrypted with a key that is publicly readable in the bundle. (1) Any client-side credential theft vector (XSS, session/CSRF token leak, malware, browser sync/profile export, shared kiosk device) can recover the user's actual username+password by decrypting with the known key. (2) For a betting/gambling platform where accounts hold balances, recovered credentials enable direct account takeover and fund withdrawal. (3) AES-ECB is a weak/deterministic mode (identical plaintext blocks produce identical ciphertext blocks), and using a hardcoded secret key in client code is an anti-pattern; it also defeats the purpose of the "encryption" (no confidentiality against anyone with the bundle).

## Recommendation

Do not rely on client-side crypto for secrecy: remove the hardcoded key from the bundle, or better, do not store the plaintext password at all (remember-me should use a server-side opaque, revocable, long-lived session cookie/token with Secure+HttpOnly+SameSite, not a re-encryptable password). If client-side storage is unavoidable, derive a per-user key from the password+salt (Argon2) so the stored value is not decryptable without the password, use an authenticated mode (AES-GCM / ChaCha20-Poly1305) rather than ECB, and treat any such value as sensitive (never expose the key to the client).
