# POC/EXP 草稿 - Subresource Integrity (SRI) Not Implemented

> 自動生成時間: 2026-09-09 11:33:04  |  狀態: **草稿（未驗證）**  |  文件: `a28e9af5-5c98-4656-867e-760d30add8c2-subresource-integrity-sri-not-implemente.md`

## 漏洞信息

- **漏洞ID**: a28e9af5-5c98-4656-867e-760d30add8c2
- **嚴重程度**: info
- **狀態**: open
- **類型**: CWE-830
- **目標**: https://www.letsmakeaplan.org/
- **發現時間**: 2026-09-09 11:32:45

## 漏洞描述

Subresource Integrity (SRI) is a security feature that enables browsers to verify that third-party resources they fetch (for example, from a CDN) are delivered without unexpected manipulation. It works by allowing developers to provide a cryptographic hash that a fetched file must match. <br/><br/>
Third-party resources (such as scripts and stylesheets) can be manipulated. An attacker that has access or has hacked the hosting CDN can manipulate or replace the files. SRI allows developers to specify a base64-encoded cryptographic hash of the resource to be loaded. The integrity attribute containing the hash is then added to the &lt;script&gt; HTML element tag. The integrity string consists of a base64-encoded hash, followed by a prefix that depends on the hash algorithm. This prefix can either be sha256, sha384 or sha512. <br/><br/>

The script loaded from the external URL specified in the Details section doesn't implement Subresource Integrity (SRI). It's recommended to implement Subresource Integrity (SRI) for all the scripts loaded from external hosts.

## 前置條件

AWVS 掃描目標: https://www.letsmakeaplan.org/

## POC / EXP 驗證指南

### 復現步驟（來自漏洞記錄）

1. 發送 HTTP 請求至目標：
2. ```http
3. GET /-/media/images/lmap/photos/full-width/topics/401k-retirement-plans/ HTTP/1.1
4. Referer: https://www.letsmakeaplan.org/
5. Cookie: ARRAffinity=71c746970952c4d88dbe871088053471e06f0f5d164d64396e95af3ec50bd22f; ARRAffinitySameSite=71c746970952c4d88dbe871088053471e06f0f5d164d64396e95af3ec50bd22f; ASP.NET_SessionId=q1pxnzsvasbzje5vgxjdmkmd; __RequestVerificationToken=iPfqXUgbINNvhiKXNEs5Uh71q0BibdFYtXidsdFqmF5Lqa3stUU1B0jQjHJ8ijh6F5VdLKMPMAjNQEcGL-C27nJcbpLMd1SfQvcEKAuxNho1; __cflb=02DiuCyj6qPfbvjVUwCRpFL9qJYciVRjjHeLJRY1hzneg; shell#lang=en
6. Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
7. Accept-Encoding: gzip,deflate,br
8. User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
9. Host: www.letsmakeaplan.org
10. Connection: Keep-alive
11. ```
12. 2. 觀察回應確認漏洞存在


### 驗證要點與安全基準

- [ ] 確認目標屬於合法授權測試範圍，非授權測試屬於違法行為
- [ ] 交叉校驗目標版本、已知 CVE/公開情資庫（可聯動 cve-poc-emerging-intel / vuln-intel）
- [ ] 使用最小化無害 payload / HTTP 請求逐步探測，記錄原始請求與回應報文
- [ ] 驗證失敗時記錄負結果，避免誤報；未經真實環境驗證不得標記為 confirmed

### 既有證據 / 原始報文

```http
GET /-/media/images/lmap/photos/full-width/topics/401k-retirement-plans/ HTTP/1.1
Referer: https://www.letsmakeaplan.org/
Cookie: ARRAffinity=71c746970952c4d88dbe871088053471e06f0f5d164d64396e95af3ec50bd22f; ARRAffinitySameSite=71c746970952c4d88dbe871088053471e06f0f5d164d64396e95af3ec50bd22f; ASP.NET_SessionId=q1pxnzsvasbzje5vgxjdmkmd; __RequestVerificationToken=iPfqXUgbINNvhiKXNEs5Uh71q0BibdFYtXidsdFqmF5Lqa3stUU1B0jQjHJ8ijh6F5VdLKMPMAjNQEcGL-C27nJcbpLMd1SfQvcEKAuxNho1; __cflb=02DiuCyj6qPfbvjVUwCRpFL9qJYciVRjjHeLJRY1hzneg; shell#lang=en
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Encoding: gzip,deflate,br
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
Host: www.letsmakeaplan.org
Connection: Keep-alive

```

## 安全影響

An attacker that has access or has hacked the hosting CDN can manipulate or replace the files.

## 修復建議

Use the SRI Hash Generator link (from the References section) to generate a &lt;script&gt; element that implements Subresource Integrity (SRI). <br/><br/>

For example, you can use the following &lt;script&gt; element to tell a browser that before executing the https://example.com/example-framework.js script, the browser must first compare the script to the expected hash, and verify that there's a match.

<pre><code>
&lt;script src=&quot;https://example.com/example-framework.js&quot;
        integrity=&quot;sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC&quot;
        crossorigin=&quot;anonymous&quot;&gt;&lt;/script&gt;
</code></pre>

## 複測驗證方法

使用 AWVS 或 JySecAI 自動生成 POC 進行複測

## 免責聲明

本文件由 JySecAI 自動生成，僅供安全研究與合法授權滲透測試使用。未經授權對目標進行攻擊測試屬於違法行為。
