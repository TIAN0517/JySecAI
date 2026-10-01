# 🐉 Dragon-V Triple Bot API 参考文档

## 概述

Dragon-V Triple Bot 是一个专业的渗透测试框架，提供完整的API接口用于安全测试和漏洞扫描。

## 核心模块

### 1. 统一管理器 (DragonTripleBotUnifiedManager)

#### 类定义
```python
class DragonTripleBotUnifiedManager:
    def __init__(self, config_path: str = "config_unified.yaml") -> None

    def start_all_bots(self) -> Dict[str, bool]
    def stop_all_bots(self) -> Dict[str, bool]
    def get_system_status(self) -> Dict[str, Any]
    def create_task(self, task_type: str, target: str, **kwargs) -> str
    def get_task_status(self, task_id: str) -> Dict[str, Any]
    def get_task_results(self, task_id: str) -> Dict[str, Any]
```

#### 使用示例
```python
from dragon_triple_bot_unified_manager import DragonTripleBotUnifiedManager

# 初始化管理器
manager = DragonTripleBotUnifiedManager()

# 启动所有bot
status = manager.start_all_bots()
print(f"启动状态: {status}")

# 创建扫描任务
task_id = manager.create_task(
    task_type="web_scan",
    target="https://example.com",
    scan_types=["sqli", "xss", "idor"]
)

# 获取任务状态
task_status = manager.get_task_status(task_id)
print(f"任务状态: {task_status}")
```

### 2. 功能模块 (DragonTripleBotFunctionalModule)

#### 类定义
```python
class DragonTripleBotFunctionalModule:
    def __init__(self, bot_type: str = "enterprise") -> None

    def enterprise_management(self, command: str, **kwargs) -> Dict[str, Any]
    def professional_scanning(self, target: str, scan_type: str) -> Dict[str, Any]
    def security_tools(self, tool_name: str, **kwargs) -> Dict[str, Any]
    def create_task(self, function_type: str, task_type: str, target: str) -> str
    def get_task_result(self, task_id: str) -> Dict[str, Any]
```

#### 使用示例
```python
from dragon_triple_bot_functional_module import DragonTripleBotFunctionalModule

# 初始化功能模块
module = DragonTripleBotFunctionalModule(bot_type="enterprise")

# 执行企业级管理
result = module.enterprise_management(
    command="user_management",
    action="add_user",
    username="admin",
    role="administrator"
)

# 执行专业扫描
scan_result = module.professional_scanning(
    target="https://example.com",
    scan_type="comprehensive"
)

print(f"扫描结果: {scan_result}")
```

### 3. Telegram Bot (DragonTripleTelegramBot)

#### 类定义
```python
class DragonTripleTelegramBot:
    def __init__(self, token: str, config_path: str = "configs/settings.yaml") -> None

    def start_bot(self) -> None
    def send_message(self, chat_id: int, message: str, **kwargs) -> bool
    def get_user_permissions(self, user_id: int) -> Dict[str, Any]
    def create_scan_task(self, user_id: int, target: str, scan_type: str) -> str
    def get_scan_results(self, task_id: str) -> Dict[str, Any]
```

#### 使用示例
```python
from dragon_triple_telegram_bot import DragonTripleTelegramBot

# 初始化Telegram Bot
bot = DragonTripleTelegramBot(token="YOUR_TELEGRAM_BOT_TOKEN")

# 启动bot
bot.start_bot()

# 发送消息
bot.send_message(
    chat_id=123456789,
    message="🐉 Dragon-V 安全扫描完成！",
    parse_mode="Markdown"
)
```

## 安全扫描API

### 漏洞扫描

```python
from security_stability_enhancer import SecurityStabilityEnhancer

# 初始化安全扫描器
scanner = SecurityStabilityEnhancer()

# 执行SQL注入扫描
sqli_results = scanner.scan_sql_injection("https://example.com/login")

# 执行XSS扫描
xss_results = scanner.scan_xss("https://example.com/search")

# 执行综合扫描
comprehensive_results = scanner.comprehensive_scan("https://example.com")
```

### WAF绕过

```python
from enhanced_waf_bypass_ultimate import EnhancedWAFBypassUltimate

# 初始化WAF绕过工具
waf_bypass = EnhancedWAFBypassUltimate()

# 生成绕过payload
bypass_payloads = waf_bypass.generate_bypass_payloads(
    original_payload="' OR '1'='1",
    waf_type="cloudflare"
)

# 测试绕过效果
bypass_result = waf_bypass.test_bypass_effectiveness(
    target="https://example.com",
    payloads=bypass_payloads
)
```

## 数据模型

### 漏洞信息
```python
@dataclass
class Vulnerability:
    type: str                    # 漏洞类型
    severity: str               # 严重程度
    confidence: float           # 置信度
    target: str                 # 目标URL
    payload: str                # 攻击载荷
    evidence: str               # 证据
    timestamp: datetime         # 时间戳
    cve_id: Optional[str]       # CVE编号
    cvss_score: Optional[float] # CVSS评分
    impact: Optional[str]       # 影响
    remediation: Optional[str]  # 修复建议
```

### 扫描结果
```python
@dataclass
class ScanResult:
    target: str                     # 目标
    vulnerabilities: List[Vulnerability]  # 漏洞列表
    scan_time: float                # 扫描时间
    total_requests: int             # 总请求数
    success_rate: float             # 成功率
```

## 配置API

### 读取配置
```python
import yaml

with open("config_unified.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 获取数据库配置
db_config = config["database"]

# 获取安全配置
security_config = config["security"]
```

### 更新配置
```python
config["logging"]["level"] = "DEBUG"

with open("config_unified.yaml", "w", encoding="utf-8") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
```

## 错误处理

### 自定义异常
```python
class DragonVError(Exception):
    """Dragon-V 基础异常"""
    pass

class ScanError(DragonVError):
    """扫描错误"""
    pass

class ConfigError(DragonVError):
    """配置错误"""
    pass
```

### 错误处理示例
```python
try:
    result = manager.create_task("web_scan", "invalid_url")
except ScanError as e:
    print(f"扫描错误: {e}")
except ConfigError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 性能优化

### 异步操作
```python
import asyncio

async def async_scan(target: str):
    """异步扫描"""
    scanner = SecurityStabilityEnhancer()
    return await scanner.async_comprehensive_scan(target)

# 执行异步扫描
async def main():
    results = await async_scan("https://example.com")
    print(f"扫描结果: {results}")

# 运行异步任务
asyncio.run(main())
```

## 扩展开发

### 自定义扫描模块
```python
from security_stability_enhancer import SecurityStabilityEnhancer

class CustomScanner(SecurityStabilityEnhancer):
    """自定义扫描器"""

    def scan_custom_vulnerability(self, target: str) -> List[Vulnerability]:
        """扫描自定义漏洞"""
        # 实现自定义扫描逻辑
        vulnerabilities = []

        # 添加漏洞检测逻辑
        if self._detect_custom_vuln(target):
            vulnerabilities.append(Vulnerability(
                type="Custom Vulnerability",
                severity="medium",
                confidence=0.8,
                target=target,
                payload="custom_payload",
                evidence="Custom detection",
                timestamp=datetime.now()
            ))

        return vulnerabilities

    def _detect_custom_vuln(self, target: str) -> bool:
        """检测自定义漏洞"""
        # 实现检测逻辑
        return False
```

---

**文档版本**: 1.0
**最后更新**: 2025-10-26
**技术支持**: support@dragon-v.com