
# Vietnam Express Delivery Security Assessment Report v2.0.0
**Vietnam快递系统安全评估报告**

扫描时间: 2025-10-29 14:31:34
扫描目标数量: 32
总发现漏洞: 0
平均风险评分: 2.78

---

## 📊 执行摘要

### 总体安全状况
- **高风险目标**: 0
- **中风险目标**: 16
- **低风险目标**: 16

### 主要发现

### Giao Hàng Nhanh
- 目标数量: 4
- 发现漏洞: 0 个
- 高危漏洞: 0 个
- 平均风险评分: 2.50

### Giao Hàng Tiết Kiệm
- 目标数量: 4
- 发现漏洞: 0 个
- 高危漏洞: 0 个
- 平均风险评分: 2.50

### Viettel Post
- 目标数量: 4
- 发现漏洞: 0 个
- 高危漏洞: 0 个
- 平均风险评分: 2.88

### VNPost
- 目标数量: 4
- 发现漏洞: 0 个
- 高危漏洞: 0 个
- 平均风险评分: 2.50

### J&T Express Vietnam
- 目标数量: 4
- 发现漏洞: 0 个
- 高危漏洞: 0 个
- 平均风险评分: 1.25

### Best Express
- 目标数量: 4
- 发现漏洞: 0 个
- 高危漏洞: 0 个
- 平均风险评分: 1.25

### Shopee Express
- 目标数量: 4
- 发现漏洞: 0 个
- 高危漏洞: 0 个
- 平均风险评分: 6.12

### Lazada Logistics
- 目标数量: 4
- 发现漏洞: 0 个
- 高危漏洞: 0 个
- 平均风险评分: 3.25

---

## 🔍 业务逻辑缺陷


### Viettel Post_Target_1
- **缺陷名称**: 订单价格篡改测试
- **描述**: 测试是否可以篡改订单价格
- **风险级别**: HIGH
- **URL**: https://viettelpost.vn/api/order/price

### Viettel Post_Target_1
- **缺陷名称**: 运费计算绕过测试
- **描述**: 测试是否可以绕过运费计算
- **风险级别**: HIGH
- **URL**: https://viettelpost.vn/api/shipping/calculate

### Viettel Post_Target_1
- **缺陷名称**: 订单状态修改测试
- **描述**: 测试是否可以未授权修改订单状态
- **风险级别**: HIGH
- **URL**: https://viettelpost.vn/api/order/status

### Viettel Post_Target_1
- **缺陷名称**: 用户权限提升测试
- **描述**: 测试是否存在权限提升漏洞
- **风险级别**: HIGH
- **URL**: https://viettelpost.vn/api/user/upgrade

### Shopee Express_Target_2
- **缺陷名称**: 订单价格篡改测试
- **描述**: 测试是否可以篡改订单价格
- **风险级别**: MEDIUM
- **URL**: https://seller.shopee.vn/api/order/price

### Shopee Express_Target_2
- **缺陷名称**: 运费计算绕过测试
- **描述**: 测试是否可以绕过运费计算
- **风险级别**: MEDIUM
- **URL**: https://seller.shopee.vn/api/shipping/calculate

### Shopee Express_Target_2
- **缺陷名称**: 订单状态修改测试
- **描述**: 测试是否可以未授权修改订单状态
- **风险级别**: MEDIUM
- **URL**: https://seller.shopee.vn/api/order/status

### Shopee Express_Target_2
- **缺陷名称**: 用户权限提升测试
- **描述**: 测试是否存在权限提升漏洞
- **风险级别**: MEDIUM
- **URL**: https://seller.shopee.vn/api/user/upgrade

### Shopee Express_Target_3
- **缺陷名称**: 订单价格篡改测试
- **描述**: 测试是否可以篡改订单价格
- **风险级别**: HIGH
- **URL**: https://affiliate.shopee.vn/api/order/price

### Shopee Express_Target_3
- **缺陷名称**: 运费计算绕过测试
- **描述**: 测试是否可以绕过运费计算
- **风险级别**: HIGH
- **URL**: https://affiliate.shopee.vn/api/shipping/calculate

### Shopee Express_Target_3
- **缺陷名称**: 订单状态修改测试
- **描述**: 测试是否可以未授权修改订单状态
- **风险级别**: HIGH
- **URL**: https://affiliate.shopee.vn/api/order/status

### Shopee Express_Target_3
- **缺陷名称**: 用户权限提升测试
- **描述**: 测试是否存在权限提升漏洞
- **风险级别**: HIGH
- **URL**: https://affiliate.shopee.vn/api/user/upgrade

### Shopee Express_Target_4
- **缺陷名称**: 订单价格篡改测试
- **描述**: 测试是否可以篡改订单价格
- **风险级别**: HIGH
- **URL**: https://help.shopee.vn/api/order/price

### Shopee Express_Target_4
- **缺陷名称**: 运费计算绕过测试
- **描述**: 测试是否可以绕过运费计算
- **风险级别**: HIGH
- **URL**: https://help.shopee.vn/api/shipping/calculate

### Shopee Express_Target_4
- **缺陷名称**: 订单状态修改测试
- **描述**: 测试是否可以未授权修改订单状态
- **风险级别**: HIGH
- **URL**: https://help.shopee.vn/api/order/status

---

## 🛡️ 安全建议

1. 加强API访问控制和认证
2. 定期进行安全代码审计
3. 实施Web应用防火墙(WAF)保护
4. 实施数据加密和传输安全
5. 建立安全事件响应机制
6. 扫描失败: HTTPSConnectionPool(host='api.giaohangtietkiem.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB28D10>: Failed to resolve 'api.giaohangtietkiem.vn' ([Errno 11001] getaddrinfo failed)"))
7. 扫描失败: HTTPSConnectionPool(host='buudien.vnpost.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB2DA50>: Failed to resolve 'buudien.vnpost.vn' ([Errno 11001] getaddrinfo failed)"))
8. 扫描失败: HTTPSConnectionPool(host='customer.best-inc.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB2ABD0>: Failed to resolve 'customer.best-inc.vn' ([Errno 11001] getaddrinfo failed)"))
9. 扫描失败: HTTPSConnectionPool(host='don.ghn.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BAB89D0>: Failed to resolve 'don.ghn.vn' ([Errno 11001] getaddrinfo failed)"))
10. 扫描失败: HTTPSConnectionPool(host='employee.viettelpost.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB46090>: Failed to resolve 'employee.viettelpost.vn' ([Errno 11001] getaddrinfo failed)"))
11. 扫描失败: HTTPSConnectionPool(host='fms.lazada.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BCA6C10>: Failed to resolve 'fms.lazada.vn' ([Errno 11001] getaddrinfo failed)"))
12. 扫描失败: HTTPSConnectionPool(host='lazada-logistics.com', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BCA13D0>: Failed to resolve 'lazada-logistics.com' ([Errno 11001] getaddrinfo failed)"))
13. 扫描失败: HTTPSConnectionPool(host='myjt.jtexpress.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB28CD0>: Failed to resolve 'myjt.jtexpress.vn' ([Errno 11001] getaddrinfo failed)"))
14. 扫描失败: HTTPSConnectionPool(host='partner.best-inc.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB73190>: Failed to resolve 'partner.best-inc.vn' ([Errno 11001] getaddrinfo failed)"))
15. 扫描失败: HTTPSConnectionPool(host='seller.giaohangtietkiem.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB24810>: Failed to resolve 'seller.giaohangtietkiem.vn' ([Errno 11001] getaddrinfo failed)"))
16. 扫描失败: HTTPSConnectionPool(host='seller.jtexpress.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB67750>: Failed to resolve 'seller.jtexpress.vn' ([Errno 11001] getaddrinfo failed)"))
17. 扫描失败: HTTPSConnectionPool(host='shop.ghn.vn', port=443): Max retries exceeded with url: / (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x000002703BABA190>, 'Connection to shop.ghn.vn timed out. (connect timeout=15)'))
18. 扫描失败: HTTPSConnectionPool(host='tracking.best-inc.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB72210>: Failed to resolve 'tracking.best-inc.vn' ([Errno 11001] getaddrinfo failed)"))
19. 扫描失败: HTTPSConnectionPool(host='tracking.jtexpress.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB667D0>: Failed to resolve 'tracking.jtexpress.vn' ([Errno 11001] getaddrinfo failed)"))
20. 扫描失败: HTTPSConnectionPool(host='tracking.viettelpost.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB29810>: Failed to resolve 'tracking.viettelpost.vn' ([Errno 11001] getaddrinfo failed)"))
21. 扫描失败: HTTPSConnectionPool(host='tracking.vnpost.vn', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x000002703BB7C150>: Failed to resolve 'tracking.vnpost.vn' ([Errno 11001] getaddrinfo failed)"))


---

**报告生成时间**: 2025-10-29 14:31:34
**扫描引擎**: Dragon-V Triple Bot v3.2.0 + Gemini 2.0 Flash-Exp + Nuclei AI
**报告版本**: v2.0.0

> ⚠️ 本报告仅用于授权的安全测试，请遵守相关法律法规。
