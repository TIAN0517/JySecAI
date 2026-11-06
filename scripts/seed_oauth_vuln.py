#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「Chailease Member-Center OAuth 無認證密碼學預言機」漏洞寫入平台 vulnerabilities 表。

為什麼要獨立一支：
  漏洞是在機構內網／本機完成驗證後取得的證據鏈（raw logs 10 份），
  平台正式庫在 /var/lib/jysecai/core/ 底下，只有 root 能寫。
  這支腳本讓部署流程（sudo 執行）能「一次把證據連同 raw log 一起落庫」，
  而不必手動開 sqlite3 拼 SQL。

設計原則
  * 冪等：以 vuln id 為準，已存在就更新內容，不會重複插入。
  * 不製造資料：raw log 的 sha256 逐檔現算後寫進 evidence 欄位，
    寫入後可重算比對（跟貸款案件同一套「來源可覆核」標準）。
  * 誠實標註邊界：無法證實「forged token 能通過 ValidateToken」，
    就不寫成已證實；confidence 與描述都保留這條邊界。

用法
  python3 scripts/seed_oauth_vuln.py \
      --db /var/lib/jysecai/core/data/conversations.db \
      --evidence-dir /mnt/c/Users/Administrator/Desktop/chailease_membercenter_oauth_crypto_evidence \
      --copy-evidence-to /var/lib/jysecai/core/evidence/oauth_crypto
"""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time

VULN_ID = "4c74bfbf-e298-4471-bb13-f8fa64ca187c"
TARGET = "member-center-oauth-service.chailease.com.tw"

TITLE = ("Unauthenticated AES-CBC static-IV crypto oracle (encrypt + decrypt) "
         "on Chailease Member-Center OAuth API")

DESCRIPTION = """目標 https://member-center-oauth-service.chailease.com.tw 的四個端點
（POST /Account/TokenEncode、POST /Account/TokenDecode、GET /Account/MemberSHA、POST /Account/ValidateToken）
實作上**完全沒有執行認證**（無 Bearer / JWT / Cookie / CSRF），但 /swagger/v1/swagger.json
宣稱全域需 Bearer(JWT) —— spec 與實作脫節。

TokenEncode(accessToken, refreshToken) 對任意輸入回傳加密後的 tokenValue；
TokenDecode(tokenValue) 無認證地把密文還原成 accessToken(JWT) + refreshToken。
兩者構成一組**無認證的 encrypt-oracle + decrypt-oracle**，且使用
**單把靜態密鑰、靜態 IV、無 MAC/AEAD 的 AES-CBC**。

### 演算法判定：三管齊驗推翻「AES-ECB」
1. 無重複密文塊（Exp I2）：明文 R*48 及 32 種對齉 k=0..31 全程無重複 16-byte block — ECB 必產生重複。
2. 交換密文 block → 500 而非乾淨重排（Exp I4 / H4）：ECB 的 cut-paste 會回乾淨可讀明文。
3. bit-flip 傳播（Exp K / L2）：翻一次 ciphertext byte → 前一 plaintext block 全亂 + 指定 byte 被 precision XOR — 這是 CBC 的 signature，ECB 不可能。
4. 報告自稱的 172-char token 拆 8 塊全不同（Exp I1）——「首塊出現兩次」未再現。

結論：C_i = E(P_i XOR C_{i-1})，IV 固定 → AES-CBC + static IV + no integrity。"""

REPRODUCTION = """Step 0 — 探活：GET /swagger/v1/swagger.json → 200（title: Chailease.MemberCenter.Oauth.API），spec 宣告需 Bearer。
Step 1 — 無認證加密預言機：POST /Account/TokenEncode，body {"jwtToken":"<JWT>","refreshToken":"<RT>"}，不帶任何認證頭 → 200 {"rtnCode":0,"msg":"success","data":{"tokenValue":"..."}}。
Step 2 — 無認證解密預言機：POST /Account/TokenDecode，body {"jwtToken":"<step1 tokenValue>"} → 200 {"rtnCode":0,"data":{"tokenValue":"<明文 JWT>","refreshToken":"<明文 RT>"}}（roundtrip 逐字還原）。
Step 3 — 確定性：同明文再打 TokenEncode → tokenValue byte-identical（Exp A / H1）→ 證明靜態 key/IV。
Step 4 — 長度分析：明文 1/15/16/17/31/32 字元 → 密文 16/32/32/48/48/64 bytes → 16-byte block + PKCS#7。
Step 5 — 無完整性：翻轉任一 ciphertext byte → 仍回 200 且明文被改（不是統一拒絕）→ 無 MAC。
  受控證明：明文 accessToken="A"*48，翻轉 C_0 byte 0，mask 0x03 → plaintext byte[16] 恰為 'B'；mask 0x02 → 恰為 'C'。同一位、不同值、預期命中 → 無 key 即可受控篡改（malleable）。
Step 6 — 憑證外洩 → session 接管（Demo1）：僅持有截獲的 tokenValue，POST /Account/TokenDecode → 200，取回完整 accessToken(JWT) 與 refreshToken。"""

PRECONDITIONS = ("無需認證、無需任何前置條件，僅需網路可達目標主機 "
                 "（前置為 Kong 3.4.3 + Cloudflare）。全程僅使用 canary 字符串，"
                 "未觸碰任何真實會員資料。")

IMPACT = """1. **Decrypt-oracle 會員外洩**：TokenDecode 無認證 → 任何人只要截獲一個 tokenValue 即可還原 victim 的 accessToken(JWT) 與 refreshToken → 重放即得 victim session（完整帳號接管）。Demo1 已證。
2. **CBC bit-flip 無完整性**：翻轉密文位元可受控改寫明文內容，伺服器不驗 → 可在不知 key 的情況下竄改 tokenValue（malleable）。L2 受控 A→B / A→C 已證。
3. **Encrypt-oracle**：TokenEncode 接受任意 (accessToken, refreshToken)，但 accessToken 須為合法簽名 JWT 才能被 ValidateToken 接受 → 單憑加密預言機不能直接 forge 出可通過驗證的 session。
4. **MemberSHA**：deterministic、輸出固定 64 bytes、輸入長度不影響輸出 → 屬 keyed hash（HMAC-SHA512 可能性）而非加密；可作 memberNo→digest mapper 的枚舉輔助。

**誠實邊界**（不列為已證實）：/Account/ValidateToken 對 alg:none JWT、HS256 dummy、AES-CBC tokenValue 與垃圾字串一律回 403 SYS.UnknowError（spec 僅定義 200/400/401/500），推測來自 CF/Kong 前置攔截，app 端驗證邏輯對試者不可達 → **未證明 forged token 能通過 ValidateToken 當作有效 session**。影響以「解密外洩憑證」與「可控篡改」為主。"""

RECOMMENDATION = """1. **立即**：對 /Account/TokenEncode、/Account/TokenDecode、/Account/MemberSHA 實施認證 —— spec 已宣告 Bearer 但實作未執行，屬可直接修補的落差。
2. **密碼學**：棄用 CBC + static IV + 無 MAC；改用 AEAD（AES-GCM 或 AES-SIV）並採 per-message nonce。勿自行發明 token 格式。
3. **金鑰管理**：靜態 key 應自 key vault 管理並支援滴水更新；對 decrypt-oracle 加上速率限制與來源限制，避免被拿來當批次解密機。
4. **ValidateToken**：把 spec 實作為 app-level 驗證（回 401 而非 403），並明確分離 tokenValue 與 accessToken(JWT) 兩條驗證路徑。"""

CONFIDENCE = 90  # 多腳位驗證支持「無認證 + AES-CBC static IV + 無 MAC」；未能證實 forged token 可通過 ValidateToken。


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_evidence(evidence_dir):
    """回傳 (evidence_text, manifest_rows)。manifest_rows 給 JSON 檔用。"""
    rows = []
    raw = os.path.join(evidence_dir, "raw")
    for name in sorted(os.listdir(raw)) if os.path.isdir(raw) else []:
        p = os.path.join(raw, name)
        if os.path.isfile(p):
            rows.append({"file": "raw/" + name, "bytes": os.path.getsize(p),
                         "sha256": sha256_of(p)})
    report = os.path.join(evidence_dir, "REPORT.md")
    if os.path.isfile(report):
        rows.insert(0, {"file": "REPORT.md", "bytes": os.path.getsize(report),
                        "sha256": sha256_of(report)})
    lines = ["證據來源目錄：%s" % evidence_dir,
             "全部驗證僅使用 canary 字符串（jysecai-canary-* / CANARY0001 / CANARY0505test），未觸碰真實會員資料。",
             "",
             "逐檔 sha256（可重算比對）："]
    for r in rows:
        lines.append("  %s  %8d B  %s" % (r["sha256"], r["bytes"], r["file"]))
    lines += ["",
              "關鍵驗證對照：",
              "  確定性 (static key/IV)      → raw/chailease_probe.log Exp A",
              "  16-byte block + PKCS#7      → raw/chailease_probe.log Exp B",
              "  ECB 前綴匹配                → raw/chailease_probe.log Exp C",
              "  ECB 棄位證據 (Exp I1/I2)    → raw/chailease_I.log",
              "  CBC block swap → 500        → raw/chailease_I.log Exp I4 / raw/chailease_H.log",
              "  roundtrip 還原              → raw/chailease_probe.log Exp E / raw/chailease_H.log",
              "  Flip → 200 mutated (no MAC) → raw/chailease_K.log、raw/chailease_L2.log (16/16)",
              "  受控 bit-flip A→B / A→C     → raw/chailease_L2.log Demo2",
              "  憑證外洩 Demo1              → raw/chailease_Demo1_leak.log",
              "  ValidateToken 行為          → raw/chailease_validate.log、raw/chailease_J.log、raw/chailease_val_empty.log",
              "  MemberSHA 身份              → raw/chailease_L2.log Demo3、raw/chailease_authmap.log",
              "  Swagger 面向                → raw/chailease_swagger.json (67 KB)",
              "",
              "註：報告已自我更正 —— 演算法為 AES-CBC (static IV, no MAC)，"
              "非原報告所稱之 AES-ECB；推翻依據見 Exp I2 / I4 / K / L2。"]
    return "\n".join(lines), rows


def copy_evidence(evidence_dir, dest):
    """把證據（REPORT.md + raw/）複製到平台可讀的位置，回傳目標路徑。"""
    os.makedirs(dest, exist_ok=True)
    for name in ("REPORT.md",):
        src = os.path.join(evidence_dir, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(dest, name))
    raw_src = os.path.join(evidence_dir, "raw")
    raw_dst = os.path.join(dest, "raw")
    if os.path.isdir(raw_src):
        os.makedirs(raw_dst, exist_ok=True)
        for name in os.listdir(raw_src):
            s = os.path.join(raw_src, name)
            if os.path.isfile(s):
                shutil.copy2(s, os.path.join(raw_dst, name))
    scripts_src = os.path.join(evidence_dir, "scripts")
    scripts_dst = os.path.join(dest, "scripts")
    if os.path.isdir(scripts_src):
        os.makedirs(scripts_dst, exist_ok=True)
        for name in os.listdir(scripts_src):
            s = os.path.join(scripts_src, name)
            if os.path.isfile(s):
                shutil.copy2(s, os.path.join(scripts_dst, name))
    return dest


def main():
    ap = argparse.ArgumentParser(description="把 OAuth 密碼學預言機漏洞落庫到平台 vulnerabilities 表")
    ap.add_argument("--db", default="data/conversations.db")
    ap.add_argument("--evidence-dir",
                    default="/mnt/c/Users/Administrator/Desktop/chailease_membercenter_oauth_crypto_evidence")
    ap.add_argument("--copy-evidence-to", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.db):
        print("[abort] 找不到資料庫：%s" % args.db, file=sys.stderr)
        return 2
    if not os.path.isdir(args.evidence_dir):
        print("[abort] 找不到證據目錄：%s" % args.evidence_dir, file=sys.stderr)
        return 2

    evidence_text, rows = collect_evidence(args.evidence_dir)
    if len(rows) < 10:
        print("[abort] 證據檔少於 10 份（實得 %d），拒絕落庫以免證據鏈殘缺" % len(rows),
              file=sys.stderr)
        return 2

    ev_path = ""
    if args.copy_evidence_to:
        ev_path = copy_evidence(args.evidence_dir, args.copy_evidence_to)
        evidence_text = ("落地副本：%s\n\n" % ev_path) + evidence_text

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "id": VULN_ID,
        "conversation_id": None,
        "conversation_tag": "chailease-membercenter-oauth",
        "task_tag": "crypto-oracle",
        "title": TITLE,
        "description": DESCRIPTION,
        "severity": "Critical",
        "status": "open",
        "confidence": CONFIDENCE,
        "vulnerability_type": "Missing Authentication + Broken Cryptography (AES-CBC static IV, no MAC/AEAD)",
        "target": TARGET,
        "preconditions": PRECONDITIONS,
        "reproduction_steps": REPRODUCTION,
        "evidence": evidence_text,
        "impact": IMPACT,
        "recommendation": RECOMMENDATION,
        "retest_notes": ("2026-10-27 落庫。重新驗證時請重跑 scripts/ 下對應腳本並更新 raw log 的 sha256；"
                         "特別注意 ValidateToken 目前受 CF/Kong 403 遮斷，"
                         "『forged token 能否通過』仍屬未證實，勿在未取得新證據前升級結論。"),
        "created_at": now,
        "updated_at": now,
        "project_id": None,
        "owner_user_id": None,
        "vulnerability_type_code": "BROKEN_CRYPTO",
        "vulnerability_type_raw": "Missing Authentication + Broken Cryptography",
    }

    if args.dry_run:
        print("[dry-run] 將寫入 %s" % args.db)
        print(json.dumps({k: (v[:80] if isinstance(v, str) else v)
                          for k, v in payload.items()}, ensure_ascii=False, indent=2))
        print("[dry-run] 證據檔 %d 份" % len(rows))
        return 0

    conn = sqlite3.connect(args.db, timeout=30)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        cols = [r[1] for r in conn.execute("PRAGMA table_info(vulnerabilities)")]
        if not cols:
            print("[abort] %s 沒有 vulnerabilities 表" % args.db, file=sys.stderr)
            return 2
        data = {k: v for k, v in payload.items() if k in cols}
        existed = conn.execute("SELECT 1 FROM vulnerabilities WHERE id=?", (VULN_ID,)).fetchone()
        ph = ",".join("?" for _ in data)
        conn.execute("INSERT OR REPLACE INTO vulnerabilities (%s) VALUES (%s)"
                     % (",".join(data.keys()), ph), list(data.values()))
        conn.commit()
        n = conn.execute("SELECT count(*) FROM vulnerabilities WHERE id=?", (VULN_ID,)).fetchone()[0]
        act = "更新" if existed else "新增"
        print("[OK] 漏洞已%s：id=%s severity=Critical confidence=%d" % (act, VULN_ID, CONFIDENCE))
        print("[OK] 資料庫 %s（vulnerabilities 現有 %d 列含本筆）" % (args.db, n))
        if ev_path:
            print("[OK] 證據落地：%s" % ev_path)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
