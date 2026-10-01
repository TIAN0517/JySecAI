# 越南Google Hacking批量扫描工具总结

## 🎯 项目概述

本项目创建了一个专门针对越南物流快递电商系统的Google Hacking批量扫描和验证工具集，包含以下核心组件：

## 📁 已创建的文件

### 1. 核心工具
- **`vietnam_google_hacking_scanner.py`** - 批量扫描和验证工具
- **`vietnam_google_dorks_generator.py`** - Google Dorks查询生成器
- **`simple_vietnam_dorks.py`** - 简化版查询生成器

### 2. 生成的查询文件
- **`vietnam_dorks_20251029_040653.txt`** - 113个越南系统查询

## 🔍 Google Hacking语法和越南语关键字

### 核心语法
```sql
site:.vn inurl:admin              # 越南管理后台
site:.vn intitle:"dashboard"       # 越南仪表板
site:.vn inurl:api               # 越南API端点
site:.vn filetype:json           # 越南JSON文件
site:.com.vn "thanh toán"        # 越南支付系统
```

### 越南语关键字库

#### 物流快递 (Logistics & Delivery)
- **越南语**: vận chuyển, giao hàng, chuyển phát, vận tải
- **英文**: shipping, delivery, logistics, courier

#### 电商平台 (E-commerce)
- **越南语**: thương mại điện tử, mua sắm online, sản phẩm, giỏ hàng
- **英文**: shopping, e-commerce, products, cart

#### 支付系统 (Payment Systems)
- **越南语**: thanh toán, ví điện tử, chuyển khoản, cổng thanh toán
- **英文**: payment, e-wallet, transfer, gateway

#### 订单管理 (Order Management)
- **越南语**: đơn hàng, đặt hàng, theo dõi, trạng thái
- **英文**: order, tracking, status, management

#### 管理后台 (Admin Panels)
- **越南语**: quản trị, quản lý, trang quản trị
- **英文**: admin, dashboard, backend, control panel

## 🎯 支持的越南系统

### 物流快递公司
1. **VNPost** (vnpost.vn) - 越南邮政
2. **Viettel Post** (viettelpost.vn) - 军队电信快递
3. **Giao Hang Nhanh** (giaohangnhanh.vn) - 快速配送
4. **Giao Hang Tiet Kiem** (ghtk.vn) - 经济配送

### 电商平台
1. **Shopee Vietnam** (shopee.vn)
2. **Lazada Vietnam** (lazada.vn)
3. **Tiki** (tiki.vn)
4. **Sendo** (sendo.vn)

### 支付系统
1. **MoMo** (momo.vn) - 电子钱包
2. **ZaloPay** (zalopay.vn) - Zalo支付
3. **VNPay** (vnpay.vn) - 支付网关

## 📊 查询统计

生成的113个查询分类统计：
- **物流快递**: 26个查询
- **电商平台**: 18个查询
- **支付系统**: 12个查询
- **管理后台**: 14个查询
- **API端点**: 6个查询
- **越南品牌**: 5个查询
- **漏洞指示器**: 5个查询

## 🔍 查询示例

### 1. 物流系统查询
```sql
site:.vn inurl:vận chuyển
site:.vn "giao hàng nhanh"
site:.vn inurl:tracking shipment
site:.com.vn "chuyển phát"
```

### 2. 电商系统查询
```sql
site:.vn inurl:sản phẩm
site:.vn "thương mại điện tử"
site:.vn inurl:giỏ hàng
site:.vn intitle:"mua sắm online"
```

### 3. 支付系统查询
```sql
site:.vn inurl:thanh toán
site:.vn "ví điện tử"
site:.vn "cổng thanh toán"
site:.vn intitle:payment
```

### 4. 管理后台查询
```sql
site:.vn inurl:admin
site:.vn intitle:"admin panel"
site:.vn inurl:dashboard
site:.vn "trang quản trị"
```

### 5. API端点查询
```sql
site:.vn inurl:api
site:.vn inurl:api/v1
site:.vn filetype:json api
site:.com.vn inurl:webhook
```

### 6. 漏洞指示器查询
```sql
site:.vn "error establishing database connection"
site:.vn "warning mysql"
site:.vn "fatal error"
site:.vn intitle:"index of"
```

## 🚀 使用方法

### 1. Google搜索
直接复制查询到Google搜索框：
```
site:.vn inurl:admin "giao hàng"
```

### 2. 安全工具集成
与Nuclei、Nmap等工具结合使用：
```bash
nuclei -l vietnam_targets.txt -t vietnam-templates/
```

### 3. 批量验证
使用扫描器自动验证发现的目标：
```python
scanner = VietnamGoogleHackingScanner()
targets = await scanner.bulk_scan(max_queries=20)
```

## 📈 批量验证功能

### 验证流程
1. **目标识别** - 基于URL和内容识别系统类型
2. **置信度评估** - 计算目标可信度
3. **漏洞检测** - 识别潜在漏洞指示器
4. **结果导出** - 生成CSV和JSON格式报告

### 检测指标
- **系统类型识别** (物流、电商、支付、管理)
- **越南内容检测** (越南语字符识别)
- **技术栈识别** (平台、框架、服务器)
- **漏洞指示器** (错误信息、敏感文件)

## 🛡️ 安全建议

### 合法使用
- ⚠️ **仅用于授权的安全测试**
- ⚠️ **遵守越南网络安全法律**
- ⚠️ **不得用于未授权的扫描**
- ⚠️ **遵循负责任披露原则**

### 最佳实践
- 🔒 使用代理保护身份
- 📝 记录所有测试活动
- 🚫 避免对生产系统造成影响
- 📊 定期检查和更新查询

## 🎯 应用场景

### 1. 渗透测试
- 识别测试目标
- 发现攻击面
- 验证漏洞存在

### 2. 威胁情报
- 监控新兴威胁
- 分析攻击趋势
- 收集目标信息

### 3. 安全研究
- 研究越南系统特点
- 分析常见漏洞
- 开发检测规则

### 4. 合规检查
- 评估安全状况
- 发现配置问题
- 生成合规报告

## 📈 成果总结

✅ **成功创建**了完整的越南Google Hacking工具集
✅ **生成113个**针对越南系统的专门查询
✅ **支持7大类**越南系统识别和扫描
✅ **包含批量验证**和自动报告功能
✅ **提供详细文档**和使用指南

这个工具集为越南地区的网络安全研究和授权测试提供了强大的支持，能够有效发现和验证越南物流、电商、支付系统的潜在安全风险。