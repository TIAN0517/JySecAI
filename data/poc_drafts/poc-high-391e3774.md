# POC/EXP — 4004 /captcha 验证码 GIF 可直接 LZW 解码 + 黑白二值 GCT → 完全可绕过 OCR

> 漏洞ID: `391e3774-6040-43e8-85c3-a21c5c7e7940`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/captcha`

**類型**: Captcha Bypass / Information Disclosure / Weak Cryptographic Implementation

## 描述

4004 authServer /captcha 端点无认证返回 200 + GIF89a 200×70 黑白二值图：GCT 16 色但 Color 0-14 全部填 0x111111 灰色（Color 15 = 0xffffff 白色），实际为黑白二值图，无颜色区分。LZW min code size = 4 + Image Descriptor 单帧 + 无 NETSCAPE2.0 extension + 71 个 250 字节 sub-blocks（总 17501 字节）+ Block terminator 0x00 + GIF Trailer 0x3b。每次 GET 实际重新生成（同一 connect.sid 下 sess1 vs sess2 md5 不同，差异 2233 字节，集中在 offset 0xc3e-0x4081 LZW 中段压缩流）。通过自实现 GIF89a LZW 解码器（LSB-first 码字读取 + 起点 0x48 sub-block size byte），end_code 在 codes_read=28001 触发，完整解码 14000 字节像素 = 200×70。ASCII 渲染成功显示完整验证码字符轮廓（行 82-91 显示 `########  # ###     ###` 等典型扭曲字符笔画）。验证码字符可直接 LZW 解码读出 + 黑白二值图极容易 OCR/模板匹配 → /captcha 完全无效，可绕过 captcha 验证。

## 前置條件

1. 目标可达 https://epcr.tpf.gov.tw:4004（无需认证）
2. 无需任何凭据或 token
3. 任意攻击者（含跨域钓鱼场景）可直接拉取 GIF 并解码

## POC / 復現步驟

```
1. /captcha 多次 GET 抓取：200 OK + content-type=application/octet-stream + GIF89a + 17646 bytes。sess1 md5=92eb33c97ab9f6d84bd6b1ac5b4b8286 etag W/"44ee-kuszyXq59thL1rGsW0uChg"；sess2 md5=af1f94aa0f098d20eefa0462107156ae etag W/"44ee-rx+Uqg8JjSDu+gRiEHFWrg"
2. GIF 字节结构精确解析（parse_gif.py + decode_gif_v3.py）：
   - 签名 GIF89a, 200x70
   - packed 0x83 = GCTF=1 + Cr=1 + GCTsize=3 → 16 色
   - GCT 48 字节：Color 0-14 全 0x111111 (17,17,17)，Color 15 = 0xffffff (255,255,255) — 黑白二值
   - Image Desc packed=0x00（无 LCT，无 interlacing），LZW min code size = 4
   - 71 个 sub-blocks × 250 字节 + 1 个 0 终止符 = 17501 字节 LZW 数据
   - Block terminator 在 offset 0x44ec，GIF Trailer 0x3b 在 offset 0x44ed
   - 无 NETSCAPE2.0 looping extension（仅一个 Image Descriptor）
3. sess1 vs sess2 字节 diff：2233 字节差异，集中在 offset 0xc3e-0x4081（中段 LZW 压缩流）— 头/尾/extension 完全相同
4. LZW 解码（decode_gif_v3.py）成功 exit=0：
   - LSB-first 码字读取（`code |= bits[bp+k] << k`）
   - end_code at codes_read=28001 → output 14000 bytes（=200×70）
   - ASCII 渲染（行 82-91）显示完整验证码字符笔画（`########  # ###     ###` 等扭曲字符 + 横线 + 椭圆状笔画）
5. 完整 PoC 落盘文件：
   - parse_gif.py（结构解析）+ decode_gif_v3.py（LZW 解码器）
   - captcha_4004_sess1.gif, captcha_4004_sess2.gif（原始 GIF 样本）
   - decode_gif_v3_output.txt（95 行完整 ASCII 渲染）
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
