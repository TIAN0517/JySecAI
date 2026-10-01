# 🇻🇳 越南零日漏洞挖掘MCP服务器

## 概述

这是一个专门针对越南快递、物流、电商、订单系统的零日漏洞挖掘MCP服务器，为Claude Code提供专业的越南地区渗透测试工具。

## 🎯 主要功能

### 1. 越南系统指纹识别
- **支持系统**: VNPost, Viettel Post, Giao Hang Nhanh, Shopee VN, Lazada VN, Tiki, MoMo, ZaloPay等
- **识别精度**: 基于URL模式、HTML签名、JavaScript文件、API端点
- **越南特色**: 专门针对越南本地化系统设计

### 2. 零日漏洞扫描
- **SQL注入**: 包括越南语参数注入
- **XSS攻击**: 支持越南字符编码
- **认证绕过**: 针对越南管理后台
- **API漏洞**: 未授权访问检测

### 3. 业务逻辑漏洞检测
- **价格操纵**: 订单价格篡改检测
- **运费绕过**: 配送费用免除测试
- **优惠券滥用**: 堆叠使用检测
- **库存绕过**: 超量购买测试
- **支付绕过**: 支付流程漏洞
- **会员特权**: 身份伪造检测

### 4. 越南化载荷生成
- **本地化参数**: 使用越南语变量名
- **地区特定**: 针对越南地区业务
- **文化适配**: 符合越南用户习惯

## 📁 文件结构

```
vietnam_zero_day_mcp/
├── VIETNAM_ZERO_DAY_MCP_SERVER.py      # 核心零日漏洞挖掘服务器
├── vietnam_fingerprint_recognizer.py   # 越南系统指纹识别器
├── vietnam_business_logic_detector.py  # 业务逻辑漏洞检测器
├── vietnam_zero_day_mcp_integration.py # MCP集成模块
├── vietnam_zero_day_config.yaml        # 配置文件
├── VIETNAM_ZERO_DAY_MCP_README.md      # 使用文档
└── reports/                             # 报告输出目录
```

## 🚀 快速开始

### 1. 环境要求

```bash
Python 3.8+
pip install aiohttp beautifulsoup4 requests
```

### 2. 基本使用

```python
# 导入集成模块
from vietnam_zero_day_mcp_integration import VietnamZeroDayMCPIntegration

# 初始化
integration = VietnamZeroDayMCPIntegration()
await integration.initialize()

# 识别越南目标
result = await integration.mcp_vietnam_identify_target("https://shopee.vn")

# 综合扫描
scan_result = await integration.mcp_vietnam_comprehensive_scan(
    "https://shopee.vn",
    scan_type="full"
)

# 生成载荷
payload = await integration.mcp_vietnam_generate_payload(
    "ecommerce",
    "sql_injection"
)
```

### 3. MCP工具调用

```python
# 目标识别
await integration.mcp_vietnam_identify_target("https://vnpost.vn")

# 综合扫描
await integration.mcp_vietnam_comprehensive_scan(
    "https://lazada.vn",
    "full"  # full, zero_day, business_logic
)

# 载荷生成
await integration.mcp_vietnam_generate_payload(
    "express_delivery",
    "price_manipulation"
)

# 利用链生成
await integration.mcp_vietnam_generate_exploitation_chain({
    "system_name": "Shopee Vietnam",
    "system_type": "ecommerce"
})

# 获取报告
await integration.mcp_vietnam_get_scan_report("VN-SCAN-1698624000")

# 支持系统列表
await integration.mcp_vietnam_list_supported_systems()
```

## 🎯 支持的越南系统

### 快递配送系统
- **VNPost** (vietnam-post.vn) - 越南邮政
- **Viettel Post** (viettelpost.vn) - 军队电信快递
- **Giao Hang Nhanh** (giaohangnhanh.vn) - 快速配送
- **Giao Hang Tiet Kiem** (ghtk.vn) - 经济配送

### 电商平台
- **Shopee Vietnam** (shopee.vn) - 东南亚电商
- **Lazada Vietnam** (lazada.vn) - 阿里电商
- **Tiki** (tiki.vn) - 越南本土电商
- **Sendo** (sendo.vn) - 越南电商平台

### 支付系统
- **MoMo** (momo.vn) - 电子钱包
- **ZaloPay** (zalopay.vn) - Zalo支付
- **VNPay** (vnpay.vn) - 支付网关

## 🔍 漏洞类型

### 技术漏洞
- **SQL注入**: 包括越南语注入
- **XSS**: 跨站脚本攻击
- **CSRF**: 跨站请求伪造
- **RCE**: 远程代码执行
- **文件上传**: 任意文件上传

### 业务逻辑漏洞
- **价格操纵**: 订单价格篡改
- **运费绕过**: 免配送费获取
- **优惠券滥用**: 多优惠券堆叠
- **库存绕过**: 超量购买商品
- **支付绕过**: 0元支付漏洞
- **订单状态**: 配送状态篡改
- **会员特权**: 身份等级伪造

## 🛠️ 配置说明

### 主要配置项

```yaml
# 扫描配置
scanning:
  concurrency:
    max_concurrent_scans: 5
    max_concurrent_requests: 20
    request_timeout: 30

# 越南本地化
localization:
  language: "vi_VN"
  currency:
    code: "VND"
    symbol: "₫"
  regions:
    - name: "Hà Nội"
    - name: "TP. Hồ Chí Minh"

# 检测规则
detection_rules:
  price_validation:
    min_price: 1000  # VND
    max_discount: 70  # %
  shipping_validation:
    base_fee: 15000  # VND
    max_free_shipping_threshold: 300000  # VND
```

## 📊 报告格式

### 扫描报告结构

```json
{
  "scan_info": {
    "scan_id": "VN-SCAN-1698624000",
    "scan_time": "2025-10-29T10:00:00Z",
    "total_vulnerabilities": 5,
    "critical_count": 2,
    "high_count": 2
  },
  "target_info": {
    "url": "https://shopee.vn",
    "system_name": "Shopee Vietnam",
    "system_type": "ecommerce",
    "confidence": "96%"
  },
  "vulnerabilities": [
    {
      "type": "business_logic",
      "category": "price_manipulation",
      "severity": "Critical",
      "description": "发现价格操纵漏洞",
      "vietnam_context": "越南电商系统价格验证不足",
      "test_payload": {"price": 0, "quantity": 1},
      "exploitation_steps": [...]
    }
  ]
}
```

## 🔧 MCP工具参考

### 工具列表

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `vietnam_identify_target` | 识别越南目标系统 | url |
| `vietnam_comprehensive_scan` | 综合扫描 | url, scan_type |
| `vietnam_generate_payload` | 生成专用载荷 | system_type, vuln_type, context |
| `vietnam_generate_exploitation_chain` | 生成利用链 | target_info |
| `vietnam_get_scan_report` | 获取扫描报告 | scan_id |
| `vietnam_list_supported_systems` | 列出支持系统 | 无 |

### 使用示例

```python
# 识别Shopee Vietnam
await mcp_vietnam_identify_target("https://shopee.vn")

# 完整扫描
await mcp_vietnam_comprehensive_scan(
    "https://shopee.vn",
    "full"
)

# 生成SQL注入载荷
await mcp_vietnam_generate_payload(
    "ecommerce",
    "sql_injection",
    "针对Shopee越南站"
)
```

## 🚨 重要提醒

### 合法使用
- ⚠️ **仅用于授权的安全测试**
- ⚠️ **遵守越南网络安全法律**
- ⚠️ **不得用于恶意攻击**
- ⚠️ **负责任披露原则**

### 安全建议
- 🔒 在隔离环境中运行
- 🛡️ 使用代理保护身份
- 📝 记录所有测试活动
- 📊 定期备份扫描结果

## 📈 性能优化

### 并发设置
- 最大并发扫描: 5个
- 最大并发请求: 20个
- 请求超时: 30秒

### 内存管理
- 最大内存使用: 512MB
- 缓存TTL: 3600秒
- 清理间隔: 5分钟

## 🔄 更新日志

### v1.0.0 (2025-10-29)
- ✨ 初始版本发布
- 🎯 支持主要越南系统
- 🔍 零日漏洞挖掘引擎
- 🛒 业务逻辑检测器
- 🔗 MCP集成接口

## 🤝 贡献指南

### 提交新系统支持
1. 添加系统指纹识别规则
2. 创建特定的载荷模板
3. 测试业务逻辑漏洞
4. 更新配置文件

### 报告漏洞
- 使用GitHub Issues
- 提供详细复现步骤
- 包含系统信息
- 遵循负责任披露

## 📞 技术支持

- 📧 Email: security@dragon-v.com
- 🐛 Bug报告: GitHub Issues
- 📖 文档: 项目Wiki
- 💬 讨论: Discord服务器

## 📄 许可证

本项目仅供学习和授权的安全测试使用。使用者需确保遵守当地法律法规。

---

**⚠️ 免责声明**: 本工具仅用于授权的安全测试和教育目的。未经授权的使用可能违反法律。开发者不承担任何滥用责任。