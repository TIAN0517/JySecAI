# POC/EXP 草稿 - Subresource Integrity (SRI) Not Implemented

> 自动生成时间: 2026-09-10 23:33:06  |  状态: **草稿（未验证）**  |  文件: `edba4044-4768-4210-a0de-33863919a9f5-subresource-integrity-sri-not-implemented.md`

## 漏洞信息

- **漏洞ID**: edba4044-4768-4210-a0de-33863919a9f5
- **严重程度**: info
- **状态**: open
- **类型**: CWE-830
- **目标**: https://www.letsmakeaplan.org/
- **发现时间**: 2026-09-09 11:32:45

## 漏洞描述

Subresource Integrity (SRI) is a security feature that enables browsers to verify that third-party resources they fetch (for example, from a CDN) are delivered without unexpected manipulation. It works by allowing developers to provide a cryptographic hash that a fetched file must match. <br/><br/>
Third-party resources (such as scripts and stylesheets) can be manipulated. An attacker that has access or has hacked the hosting CDN can manipulate or replace the files. SRI allows developers to specify a base64-encoded cryptographic hash of the resource to be loaded. The integrity attribute containing the hash is then added to the &lt;script&gt; HTML element tag. The integrity string consists of a base64-encoded hash, followed by a prefix that depends on the hash algorithm. This prefix can either be sha256, sha384 or sha512. <br/><br/>

The script loaded from the external URL specified in the Details section doesn't implement Subresource Integrity (SRI). It's recommended to implement Subresource Integrity (SRI) for all the scripts loaded from external hosts.

## 前置条件

AWVS 掃描目標: https://www.letsmakeaplan.org/

## POC / EXP 验证指南

### 复现步骤（来自漏洞记录）

1. 發送 HTTP 請求至目標：
2. ```http
3. GET /find-a-cfp-professional/favorites HTTP/1.1
4. Referer: https://www.letsmakeaplan.org/find-a-cfp-professional/favorites
5. Cookie: ARRAffinity=71c746970952c4d88dbe871088053471e06f0f5d164d64396e95af3ec50bd22f; ARRAffinitySameSite=71c746970952c4d88dbe871088053471e06f0f5d164d64396e95af3ec50bd22f; ASP.NET_SessionId=5gw0z1hcupcydkz4bbgteaj1; __RequestVerificationToken=jqDIeAveA0N7bwzs6zQb1EYZ9vj6MShph_qY-387xMVs5JweujVzQBoDpZy2LvBUu3S7t9uJddO0B2BDeJBUtOXFoyT4dRouzaQ_XnxpL8o1; __cflb=02DiuCyj6qPfbvjVUwCRpFL9qJYciVRjhoL9r6Tk35SNY; shell#lang=en
6. Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
7. Accept-Encoding: gzip,deflate,br
8. User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
9. Host: www.letsmakeaplan.org
10. Connection: Keep-alive
11. ```
12. 2. 觀察回應確認漏洞存在


### 验证要点与安全基线

- [ ] 确认目标属于合法授权测试范围，非授权测试属于违法行为
- [ ] 交叉校验目标版本、已知 CVE/公开情报库（可联动 cve-poc-emerging-intel / vuln-intel）
- [ ] 使用最小化无害 payload / HTTP 请求逐步探测，记录原始请求与响应报文
- [ ] 验证失败时记录负结果，避免误报；未经真实环境验证不得标记为 confirmed

### 既有证据 / 原始报文

```http
GET /find-a-cfp-professional/favorites HTTP/1.1
Referer: https://www.letsmakeaplan.org/find-a-cfp-professional/favorites
Cookie: ARRAffinity=71c746970952c4d88dbe871088053471e06f0f5d164d64396e95af3ec50bd22f; ARRAffinitySameSite=71c746970952c4d88dbe871088053471e06f0f5d164d64396e95af3ec50bd22f; ASP.NET_SessionId=5gw0z1hcupcydkz4bbgteaj1; __RequestVerificationToken=jqDIeAveA0N7bwzs6zQb1EYZ9vj6MShph_qY-387xMVs5JweujVzQBoDpZy2LvBUu3S7t9uJddO0B2BDeJBUtOXFoyT4dRouzaQ_XnxpL8o1; __cflb=02DiuCyj6qPfbvjVUwCRpFL9qJYciVRjhoL9r6Tk35SNY; shell#lang=en
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Encoding: gzip,deflate,br
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
Host: www.letsmakeaplan.org
Connection: Keep-alive


> [自動生成 POC/EXP 草稿] poc_drafts/edba4044-4768-4210-a0de-33863919a9f5-subresource-integrity-sri-not-implemente.md
```

## 安全影响

An attacker that has access or has hacked the hosting CDN can manipulate or replace the files.

## 修复建议

Use the SRI Hash Generator link (from the References section) to generate a &lt;script&gt; element that implements Subresource Integrity (SRI). <br/><br/>

For example, you can use the following &lt;script&gt; element to tell a browser that before executing the https://example.com/example-framework.js script, the browser must first compare the script to the expected hash, and verify that there's a match.

<pre><code>
&lt;script src=&quot;https://example.com/example-framework.js&quot;
        integrity=&quot;sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC&quot;
        crossorigin=&quot;anonymous&quot;&gt;&lt;/script&gt;
</code></pre>

## 复测验证方法

使用 AWVS 或 JySecAI 自動生成 POC 進行複測

## 免责声明

本文件由 JySecAI 自动生成，仅供安全研究与合法授权渗透测试使用。未经授权对目标进行攻击测试属于违法行为。
