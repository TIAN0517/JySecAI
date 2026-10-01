# Dragon-V Triple Bot - iFlow CLI Context

## 项目概述

Dragon-V Triple Bot 是一个企业级渗透测试框架，专为亚洲地区（越南、中国、泰国）的物流、快递、邮政系统设计。系统采用三层统一架构，通过Telegram Bot提供AI驱动的自动化漏洞扫描服务。

**核心架构:**
- **用户层**: Telegram Bot接口 (3个专用Bot)
- **功能层**: 统一管理器 + 功能模块 + 任务调度器
- **执行层**: Dragon-V Hunter核心引擎 + 目标系统 + 数据库操作

**技术栈:**
- **后端**: Python 3.11+, SQLite, AsyncIO, Telegram Bot API
- **安全工具**: Metasploit, sqlmap, Nuclei, WAF绕过工具, MCP服务器
- **数据资源**: 414个CVE漏洞定义, 42个应用指纹, 21个MCP安全测试模块

## 快速开始

### 环境启动
```bash
# 一键启动系统（推荐）
python 🚀_一键启动.py

# 启动测试环境（Docker）
docker-compose up -d

# 启动统一管理器
python dragon_triple_bot_unified_manager.py

# 启动Dragon-V Hunter核心引擎
python dragon_v_hunter/main.py
```

### 系统检查
```bash
# 环境检查
python CHECK_SYSTEM.py

# 故障诊断
python 🔍_故障诊断.py

# 系统工具集
python 🔧_系统工具集.py
```

## 核心组件

### 主要Python文件
- **dragon_triple_bot_unified_manager.py**: 统一管理器，负责Bot实例管理和任务调度
- **dragon_triple_bot_functional_module.py**: 功能模块，提供企业级管理、专业扫描、安全工具功能
- **dragon_triple_telegram_bot.py**: Telegram Bot接口，提供统一的用户交互界面
- **mcp_penetration_server.py**: MCP渗透测试服务器，集成21个安全测试模块
- **advanced_loan_penetration.py**: 高级渗透测试工具
- **thai_loan_penetration.py**: 泰国贷款系统渗透测试
- **waf_bypass_advanced.py**: WAF绕过工具

### 数据库架构
1. **dragon_triple_bot_unified.db**: 主任务数据库
2. **dragon_triple_telegram_bot.db**: Telegram用户数据
3. **dragon_triple_functional.db**: 功能配置数据

### 配置文件
- **config_unified.yaml**: 统一YAML配置文件
- **docker-compose.yml**: Docker测试环境配置
- **.env.example**: 环境变量模板

## 开发规范

### 代码风格
- 使用异步编程(async/await模式)
- 完善的异常处理和日志记录
- 参数化查询防止SQL注入
- 遵循PEP 8编码规范

### 性能优化
- 并发控制：最多3个并发任务
- 内存管理：256MB内存限制
- 缓存机制：1800秒TTL缓存
- 请求限制：每分钟最多60个请求

### 安全合规
- 仅授权测试：只对有明确授权的系统进行测试
- 数据保护：处理敏感数据时注意隐私保护
- 法律合规：遵守当地网络安全法律法规

## 常用命令

### 渗透测试
```bash
# 漏洞扫描测试
python simple_test.py

# SQL注入测试
python direct_sql_injection.py

# WAF绕过测试
python waf_bypass_test.py

# 高级四目标渗透测试
python advanced_quad_target_pentest.py
```

### MCP服务器使用
```bash
# 启动MCP渗透测试服务器
python mcp_penetration_server.py

# 漏洞数据库查询
python mcp_exploit_database.py

# 载荷数据库管理
python mcp_payloads_database.py
```

### Bot管理
```bash
# 测试单个bot
python bot_1_working.py

# 重置Bot
python reset_bot.py

# 启动三个Bot
python START_THREE_BOTS.py
```

## 目录结构

### 核心目录
- **dragon_v_hunter/**: Dragon-V Hunter核心渗透测试引擎
- **mcp/**: MCP服务器配置文件(21个模块)
- **vuln/**: 中文版本漏洞定义(414个CVE)
- **vuln_en/**: 英文版本漏洞定义(414个CVE)
- **fingerprints/**: 应用指纹识别库(42种应用)
- **eval/**: AI安全评估数据集(5个专业数据集)

### 输出目录
- **reports/**: 生成的安全测试报告
- **logs/**: 系统日志文件
- **exploitation_results/**: 漏洞利用结果
- **sqlmap_results/**: SQL注入测试结果
- **batch_test_reports/**: 批量测试报告

### 测试环境
- **Dast-Xray/**: Java漏洞扫描工具
- **Dast-Xray-web/**: Web界面版本
- **web_dashboard/**: Web管理面板
- **tests/**: 单元测试文件

## 故障排除

### 常见问题
1. **Telegram Bot无响应**: 检查token有效性
2. **数据库锁定**: 增加连接超时到30秒
3. **内存使用过高**: 重启Bot实例

### 调试模式
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python dragon_triple_bot_unified_manager.py

# 系统诊断
python 🔍_故障诊断.py
```

## 扩展开发

### 添加新扫描模块
1. 在`dragon_v_hunter/exploitation/`创建新模块
2. 更新`config_unified.yaml`配置
3. 在`dragon_v_hunter/main.py`集成
4. 创建对应测试文件

### 添加新漏洞定义
1. 在`vuln/`或`vuln_en/`创建YAML文件
2. 按照现有模板格式编写
3. 在`fingerprints/`添加应用指纹
4. 测试漏洞检测功能

### 集成新绕过技术
1. 在`waf_bypass_advanced.py`添加新技术
2. 更新配置文件中的WAF绕过策略
3. 创建测试验证脚本

## 注意事项

**重要提醒**: 本系统仅用于授权的安全测试，使用前请确保获得明确的测试授权并遵守相关法律法规。

**资源限制**: 
- 内存使用不超过256MB
- 并发任务不超过3个
- 每分钟请求不超过60个
- AI功能默认禁用外部API调用

**数据安全**:
- 定期备份3个数据库文件
- 敏感数据加密存储
- 日志文件定期清理
- 用户权限严格管理