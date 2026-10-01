# 安全评估报告

## 报告标题: {{title}}

**生成时间**: {{timestamp}}
**评估人员**: {{analyst}}
**目标范围**: {{target_scope}}
**风险等级**: {{risk_level}}
**报告版本**: {{version}}

---

## 📋 执行摘要

### 总体风险评估
- **风险等级**: {{risk_level}}
- **发现漏洞总数**: {{total_vulnerabilities}}
- **严重漏洞数量**: {{critical_vulnerabilities}}
- **高危漏洞数量**: {{high_vulnerabilities}}
- **中危漏洞数量**: {{medium_vulnerabilities}}
- **低危漏洞数量**: {{low_vulnerabilities}}

### 影响分析
{{impact_analysis}}

---

## 🎯 评估范围

### 目标信息
- **评估目标**: {{targets}}
- **评估范围**: {{scope}}
- **排除范围**: {{exclusions}}
- **评估方法**: {{methodology}}

### 技术栈识别
{{technology_stack}}

---

## 🚨 发现的漏洞

### 按严重程度分类

#### 🔴 严重 (Critical) - {{critical_count}}个
{{critical_vulnerabilities}}

#### 🟠 高危 (High) - {{high_count}}个
{{high_vulnerabilities}}

#### 🟡 中危 (Medium) - {{medium_count}}个
{{medium_vulnerabilities}}

#### 🟢 低危 (Low) - {{low_count}}个
{{low_vulnerabilities}}

---

## 📊 详细漏洞信息

### 漏洞详情模板

#### {{vulnerability_title}}
- **CVE编号**: {{cve_id}}
- **严重程度**: {{severity}}
- **CVSS评分**: {{cvss_score}}
- **影响范围**: {{affected_scope}}
- **发现时间**: {{discovered_date}}

**漏洞描述**:
{{description}}

**技术细节**:
{{technical_details}}

**利用条件**:
{{exploitation_conditions}}

**影响评估**:
{{impact_assessment}}

---

## 🔧 修复建议

### 优先修复建议

#### 1. 立即修复 (24小时内)
{{immediate_fixes}}

#### 2. 高优先级修复 (1周内)
{{high_priority_fixes}}

#### 3. 中优先级修复 (1个月内)
{{medium_priority_fixes}}

#### 4. 低优先级修复 (3个月内)
{{low_priority_fixes}}

### 通用修复建议

#### 安全加固措施
{{security_hardening}}

#### 最佳实践建议
{{best_practices}}

#### 监控和检测建议
{{monitoring_recommendations}}

---

## ✅ 验证步骤

### 修复验证流程

#### 1. 验证准备
- [ ] 确认修复措施已实施
- [ ] 准备测试环境
- [ ] 准备验证工具

#### 2. 验证执行
- [ ] 执行漏洞复现测试
- [ ] 验证修复效果
- [ ] 测试系统功能完整性

#### 3. 验证结果
- [ ] 记录验证结果
- [ ] 更新漏洞状态
- [ ] 生成验证报告

### 具体验证步骤

#### 对于每个严重漏洞:
{{verification_steps_per_vuln}}

#### 对于整体系统:
{{overall_system_verification}}

---

## 📈 统计分析

### 漏洞分布统计
{{vulnerability_distribution}}

### 风险趋势分析
{{risk_trend_analysis}}

### 合规性评估
{{compliance_assessment}}

---

## 📚 附录

### 工具和方法
{{tools_and_methods}}

### 参考资料
{{references}}

### 术语定义
{{glossary}}

---

## 📞 联系信息

**安全团队**: {{security_team}}
**联系方式**: {{contact_info}}
**报告反馈**: {{feedback_channel}}

---

**免责声明**: 本报告仅用于授权的安全评估目的，未经授权不得用于其他用途。所有测试活动均在获得明确授权的情况下进行。

**保密声明**: 本报告内容包含敏感信息，仅供授权人员查阅，请妥善保管，不得外传。

---
*报告生成工具: 内网安全助手 v{{version}}*
*生成时间: {{timestamp}}*
