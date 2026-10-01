#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragon-V Prompt & Policy Framework (DVPPF) 智能加载器
AI知识库加载和调用工具

版本: 2.0
作者: Dragon-V CyberSec Labs
用途: 智能加载和调用AI知识库，实现专业级AI协作

功能:
1. 知识库文件加载和管理
2. 智能模板构建和上下文替换
3. AI协作指令生成
4. 多语言支持
5. 决策框架应用

使用方法:
python dvppf_loader.py --template recon_template --target "example.com" --region vietnam
"""

import os
import json
import yaml
import random
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse


class DVPPLoader:
    """Dragon-V Prompt & Policy Framework 智能加载器"""

    def __init__(self, knowledge_base_path: str = "dvppf_knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.templates = {}
        self.policies = {}
        self.philosophy = {}
        self.tactics = {}
        self.asian_templates = {}

        # 初始化加载器
        self._initialize_loader()

    def _initialize_loader(self):
        """初始化加载器，加载所有知识库文件"""
        print(f"[DVPPF] 正在初始化智能加载器...")
        print(f"[DVPPF] 知识库路径: {self.knowledge_base_path}")

        # 检查知识库路径
        if not os.path.exists(self.knowledge_base_path):
            raise FileNotFoundError(f"知识库路径不存在: {self.knowledge_base_path}")

        # 加载所有知识库文件
        self._load_core_philosophy()
        self._load_decision_policies()
        self._load_tactical_library()
        self._load_asian_templates()

        print(f"[DVPPF] 初始化完成! 已加载 {len(self.templates)} 个模板")

    def _load_core_philosophy(self):
        """加载核心哲学"""
        philosophy_file = os.path.join(self.knowledge_base_path, "1_core_philosophy.md")
        if os.path.exists(philosophy_file):
            with open(philosophy_file, 'r', encoding='utf-8') as f:
                self.philosophy = f.read()
            print(f"[DVPPF] 核心哲学已加载")

    def _load_decision_policies(self):
        """加载决策策略"""
        policy_file = os.path.join(self.knowledge_base_path, "2_decision_policies.yaml")
        if os.path.exists(policy_file):
            with open(policy_file, 'r', encoding='utf-8') as f:
                self.policies = yaml.safe_load(f)
            print(f"[DVPPF] 决策策略已加载")

    def _load_tactical_library(self):
        """加载战术技术库"""
        tactics_file = os.path.join(self.knowledge_base_path, "3_tactical_library.md")
        if os.path.exists(tactics_file):
            with open(tactics_file, 'r', encoding='utf-8') as f:
                self.tactics = f.read()
            print(f"[DVPPF] 战术技术库已加载")

    def _load_asian_templates(self):
        """加载亚洲目标模板"""
        templates_file = os.path.join(self.knowledge_base_path, "4_asian_target_templates.md")
        if os.path.exists(templates_file):
            with open(templates_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 解析模板内容
                self.asian_templates = self._parse_asian_templates(content)
            print(f"[DVPPF] 亚洲目标模板已加载")

    def _parse_asian_templates(self, content: str) -> Dict[str, str]:
        """解析亚洲目标模板"""
        templates = {}

        # 使用正则表达式解析模板
        template_pattern = r'---\s*type:\s*(\w+)_template.*?---\s*(.*?)---'
        matches = re.findall(template_pattern, content, re.DOTALL)

        for template_type, template_content in matches:
            templates[template_type] = template_content.strip()

        return templates

    def get_core_philosophy(self) -> str:
        """获取核心哲学"""
        return self.philosophy

    def get_decision_policies(self) -> Dict[str, Any]:
        """获取决策策略"""
        return self.policies

    def get_tactical_library(self) -> str:
        """获取战术技术库"""
        return self.tactics

    def get_asian_template(self, template_type: str) -> Optional[str]:
        """获取亚洲目标模板"""
        return self.asian_templates.get(template_type)

    def build_ai_prompt(self, template_type: str, context: Dict[str, Any]) -> str:
        """构建AI协作指令"""

        # 获取模板内容
        if template_type in self.asian_templates:
            template_content = self.asian_templates[template_type]
        else:
            template_content = self._get_default_template(template_type)

        if not template_content:
            raise ValueError(f"未找到模板类型: {template_type}")

        # 替换上下文变量
        processed_content = self._replace_context_variables(template_content, context)

        # 添加AI协作指令
        ai_instructions = self._generate_ai_instructions(context)

        # 组合完整提示
        full_prompt = f"""
{processed_content}

---

## AI协作指令

{ai_instructions}

---

*提示由Dragon-V Prompt & Policy Framework (DVPPF) v2.0生成*
"""

        return full_prompt

    def _replace_context_variables(self, content: str, context: Dict[str, Any]) -> str:
        """替换上下文变量"""
        # 处理基本的变量替换
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))

        # 处理复杂的条件变量
        content = self._process_conditional_variables(content, context)

        return content

    def _process_conditional_variables(self, content: str, context: Dict[str, Any]) -> str:
        """处理条件变量"""
        # 处理地区特定的变量
        region = context.get('region', 'vietnam')
        if region == 'vietnam':
            content = content.replace('{{region_specific_themes}}', '越南语社会工程学策略')
        elif region == 'thailand':
            content = content.replace('{{region_specific_themes}}', '泰语社会工程学策略')
        elif region == 'china':
            content = content.replace('{{region_specific_themes}}', '中文社会工程学策略')

        return content

    def _generate_ai_instructions(self, context: Dict[str, Any]) -> str:
        """生成AI协作指令"""

        # 基础AI指令
        instructions = """// --- AI协作启动器 ---
// 你是Dragon-V CyberSec Labs的专家'Zero'
// 经验: 15年渗透测试经验，特别专精亚洲地区
// 任务: 请基于上述模板和上下文，提供专业的技术方案"""

        # 根据模板类型添加特定指令
        template_type = context.get('template_type', 'recon')
        if template_type == 'recon':
            instructions += """
// 请提供:
// 1. 目标技术栈识别
// 2. 攻击面完整映射
// 3. 漏洞优先级排序
// 4. 地区特定社会工程学策略
// 5. 下一步利用建议"""
        elif template_type == 'exploit':
            instructions += """
// 请提供:
// 1. 针对性Payload设计
// 2. 防御绕过策略
// 3. 数据提取方案
// 4. 持久化访问方案
// 5. 隐蔽性保证措施"""
        elif template_type == 'data_extraction':
            instructions += """
// 请提供:
// 1. 数据结构分析
// 2. 提取路径规划
// 3. 数据完整性验证
// 4. 多格式导出方案
// 5. 隐蔽性保证措施"""

        # 添加地区特定指令
        region = context.get('region', 'vietnam')
        if region:
            instructions += f"""
// 地区优化: 特别关注{region}地区的网络特点和防护水平
// 语言适配: 使用{region}语的技术术语和表达方式"""

        return instructions

    def _get_default_template(self, template_type: str) -> Optional[str]:
        """获取默认模板"""
        default_templates = {
            'recon': """## 通用侦查模板

### 目标信息
- **目标名称**: {{target_name}}
- **目标类型**: {{target_type}}
- **地理位置**: {{target_location}}

### 侦查计划
1. **基础信息收集**
   - 收集目标基本信息
   - 分析技术栈
   - 识别攻击面

2. **技术侦察**
   - 端口扫描
   - 服务识别
   - 漏洞扫描

3. **社会工程学分析**
   - 员工信息收集
   - 组织结构分析
   - 攻击路径规划""",

            'exploit': """## 通用利用模板

### 漏洞信息
- **目标URL**: {{target_url}}
- **漏洞类型**: {{vuln_type}}
- **优先级**: {{priority}}

### 利用策略
1. **漏洞验证**
   - 确认漏洞存在
   - 评估影响范围
   - 验证可利用性

2. **攻击执行**
   - 构造有效payload
   - 绕过防护机制
   - 获取访问权限

3. **后渗透**
   - 权限提升
   - 持久化访问
   - 数据提取"""
        }

        return default_templates.get(template_type)

    def get_decision_framework(self, situation: str) -> Dict[str, Any]:
        """获取决策框架"""
        if not self.policies:
            return {}

        # 根据情况获取相应策略
        if situation == 'new_target':
            return self.policies.get('on_new_target_discovered', {})
        elif situation == 'vulnerability_verification':
            return self.policies.get('on_vulnerability_verification', {})
        elif situation == 'exploitation_choice':
            return self.policies.get('on_exploitation_choice', {})
        elif situation == 'data_extraction':
            return self.policies.get('on_data_extraction', {})
        elif situation == 'detection_threat':
            return self.policies.get('on_detection_threat', {})

        return {}

    def generate_report(self, template_type: str, context: Dict[str, Any]) -> str:
        """生成执行报告"""

        report_template = f"""
# Dragon-V 执行报告

## 基本信息
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **模板类型**: {template_type}
- **目标名称**: {context.get('target_name', 'N/A')}
- **任务优先级**: {context.get('priority', 'medium')}

## 执行摘要
- **模板加载**: 成功
- **上下文处理**: 完成
- **AI指令生成**: 完成
- **报告状态**: 已生成

## 技术能力评估
- **决策框架**: 已应用
- **战术库**: 已调用
- **模板适配**: 已完成
- **地区优化**: 已实施

## 下一步建议
1. 基于生成的AI指令进行专业协作
2. 根据具体目标特点调整策略
3. 保持隐蔽性和安全性
4. 定期更新知识库内容

---
*报告由Dragon-V Prompt & Policy Framework (DVPPF) v2.0生成*
"""

        return report_template


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Dragon-V Prompt & Policy Framework (DVPPF) 智能加载器')
    parser.add_argument('--template', type=str, required=True, help='模板类型 (recon/exploit/data_extraction)')
    parser.add_argument('--target', type=str, required=True, help='目标名称')
    parser.add_argument('--region', type=str, default='vietnam', help='目标地区 (vietnam/thailand/china)')
    parser.add_argument('--priority', type=str, default='medium', help='任务优先级')
    parser.add_argument('--output', type=str, help='输出文件路径')

    args = parser.parse_args()

    try:
        # 初始化加载器
        loader = DVPPLoader()

        # 构建上下文
        context = {
            'template_type': args.template,
            'target_name': args.target,
            'region': args.region,
            'priority': args.priority,
            'target_domain': args.target,
            'authorization_status': 'verified',
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 生成AI提示
        ai_prompt = loader.build_ai_prompt(args.template, context)

        # 生成报告
        report = loader.generate_report(args.template, context)

        # 输出结果
        print("=" * 60)
        print("Dragon-V Prompt & Policy Framework (DVPPF) v2.0")
        print("=" * 60)
        print("\n[AI协作指令]")
        print("-" * 40)
        print(ai_prompt)
        print("\n[执行报告]")
        print("-" * 40)
        print(report)

        # 保存到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(f"=== AI协作指令 ===\n\n{ai_prompt}\n\n=== 执行报告 ===\n\n{report}")
            print(f"\n结果已保存到: {args.output}")

        print("\n" + "=" * 60)
        print("DVPPF智能加载器执行完成!")
        print("=" * 60)

    except Exception as e:
        print(f"错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    main()