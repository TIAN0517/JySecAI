#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced JSON Processor v1.0.0
增强JSON格式处理器

专门用于处理Nuclei AI工具和其他安全工具的JSON输出
提供格式验证、错误修复、数据提取和报告生成功能
"""

import os
import sys
import json
import re
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_json_processor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JSONProcessingResult:
    """JSON处理结果"""
    file_path: str
    original_size: int
    processed_size: int
    status: str
    errors_found: List[str]
    errors_fixed: List[str]
    data_extracted: Dict
    processing_time: float

class EnhancedJSONProcessor:
    """增强JSON处理器"""

    def __init__(self):
        self.supported_formats = ['json', 'jsonl', 'ndjson']
        self.processed_files = 0
        self.total_errors = 0
        self.total_fixes = 0

    def validate_json_format(self, json_str: str) -> Tuple[bool, Optional[str]]:
        """验证JSON格式"""
        try:
            json.loads(json_str)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)
        except Exception as e:
            return False, f"未知错误: {str(e)}"

    def fix_common_json_errors(self, json_str: str) -> Tuple[str, List[str]]:
        """修复常见JSON错误"""
        fixed_json = json_str
        fixes_applied = []

        # 1. 修复多余的逗号
        if ',]' in fixed_json or ',}' in fixed_json:
            fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
            fixes_applied.append("移除多余的逗号")

        # 2. 修复缺少引号的键名
        # 简单的正则匹配，实际使用中可能需要更复杂的逻辑
        fixed_json = re.sub(r'(\w+)\s*:', r'"\1":', fixed_json)
        fixes_applied.append("为键名添加引号")

        # 3. 修复单引号为双引号
        if "'" in fixed_json and '"' not in fixed_json:
            fixed_json = fixed_json.replace("'", '"')
            fixes_applied.append("将单引号转换为双引号")

        # 4. 修复注释（移除JSON中的注释）
        fixed_json = re.sub(r'//.*?\n', '\n', fixed_json)
        fixed_json = re.sub(r'/\*.*?\*/', '', fixed_json, flags=re.DOTALL)
        if '//' in json_str or '/*' in json_str:
            fixes_applied.append("移除JSON注释")

        # 5. 修复尾随逗号后的换行符问题
        fixed_json = re.sub(r',(\s*\n\s*[}\]])', r'\1', fixed_json)

        # 6. 修复Unicode转义问题
        try:
            # 尝试编码解码来处理Unicode问题
            fixed_json.encode('utf-8').decode('utf-8')
        except UnicodeError:
            # 如果有Unicode错误，尝试修复
            fixed_json = re.sub(r'\\u[0-9a-fA-F]{0,3}', '', fixed_json)
            fixes_applied.append("修复Unicode转义字符")

        return fixed_json, fixes_applied

    def process_nuclei_json_file(self, file_path: str) -> JSONProcessingResult:
        """处理Nuclei JSON文件"""
        start_time = time.time()
        original_size = os.path.getsize(file_path)

        errors_found = []
        errors_fixed = []
        data_extracted = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查文件是否为空
            if not content.strip():
                return JSONProcessingResult(
                    file_path=file_path,
                    original_size=original_size,
                    processed_size=0,
                    status="empty_file",
                    errors_found=["文件为空"],
                    errors_fixed=[],
                    data_extracted={},
                    processing_time=time.time() - start_time
                )

            # 尝试直接解析JSON
            is_valid, error = self.validate_json_format(content)

            if not is_valid:
                errors_found.append(f"JSON格式错误: {error}")

                # 尝试修复JSON错误
                fixed_content, fixes = self.fix_common_json_errors(content)
                errors_fixed.extend(fixes)

                # 再次验证
                is_valid, error = self.validate_json_format(fixed_content)

                if not is_valid:
                    # 如果还是无效，尝试按行处理（JSONL格式）
                    lines = content.strip().split('\n')
                    valid_lines = []
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if line:
                            line_valid, line_error = self.validate_json_format(line)
                            if line_valid:
                                valid_lines.append(line)
                            else:
                                # 尝试修复单行
                                fixed_line, line_fixes = self.fix_common_json_errors(line)
                                line_valid, _ = self.validate_json_format(fixed_line)
                                if line_valid:
                                    valid_lines.append(fixed_line)
                                    errors_fixed.extend([f"第{i+1}行: {fix}" for fix in line_fixes])
                                else:
                                    errors_found.append(f"第{i+1}行无法修复: {line_error}")

                    if valid_lines:
                        fixed_content = '\n'.join(valid_lines)
                        is_valid = True
                        errors_fixed.append(f"处理为JSONL格式，保留{len(valid_lines)}/{len(lines)}行")

            if is_valid:
                # 解析JSON数据
                try:
                    if '\n' in fixed_content and not fixed_content.strip().startswith('['):
                        # JSONL格式
                        data = [json.loads(line) for line in fixed_content.strip().split('\n') if line.strip()]
                        data_type = "jsonl"
                    else:
                        # 标准JSON格式
                        data = json.loads(fixed_content)
                        data_type = "json"

                    # 提取关键信息
                    data_extracted = self.extract_nuclei_data(data, data_type)

                    # 保存修复后的文件
                    if errors_fixed:
                        backup_path = file_path + '.backup'
                        if not os.path.exists(backup_path):
                            os.rename(file_path, backup_path)

                        with open(file_path, 'w', encoding='utf-8') as f:
                            if data_type == "jsonl":
                                for item in data:
                                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
                            else:
                                f.write(json.dumps(data, ensure_ascii=False, indent=2))

                    processed_size = os.path.getsize(file_path)

                    return JSONProcessingResult(
                        file_path=file_path,
                        original_size=original_size,
                        processed_size=processed_size,
                        status="success",
                        errors_found=errors_found,
                        errors_fixed=errors_fixed,
                        data_extracted=data_extracted,
                        processing_time=time.time() - start_time
                    )

                except Exception as e:
                    errors_found.append(f"数据处理错误: {str(e)}")
                    return JSONProcessingResult(
                        file_path=file_path,
                        original_size=original_size,
                        processed_size=0,
                        status="processing_error",
                        errors_found=errors_found,
                        errors_fixed=errors_fixed,
                        data_extracted={},
                        processing_time=time.time() - start_time
                    )
            else:
                return JSONProcessingResult(
                    file_path=file_path,
                    original_size=original_size,
                    processed_size=0,
                    status="invalid_json",
                    errors_found=errors_found + ["无法修复JSON格式"],
                    errors_fixed=errors_fixed,
                    data_extracted={},
                    processing_time=time.time() - start_time
                )

        except Exception as e:
            logger.error(f"处理文件异常 {file_path}: {e}")
            return JSONProcessingResult(
                file_path=file_path,
                original_size=original_size,
                processed_size=0,
                status="file_error",
                errors_found=[f"文件处理异常: {str(e)}"],
                errors_fixed=errors_fixed,
                data_extracted={},
                processing_time=time.time() - start_time
            )

    def extract_nuclei_data(self, data: Any, data_type: str) -> Dict:
        """提取Nuclei数据"""
        extracted = {
            "total_items": 0,
            "vulnerabilities": [],
            "severity_distribution": {},
            "template_ids": [],
            "target_hosts": [],
            "scan_info": {}
        }

        try:
            if data_type == "jsonl":
                items = data if isinstance(data, list) else [data]
            else:
                items = data if isinstance(data, list) else [data]

            extracted["total_items"] = len(items)

            for item in items:
                if not isinstance(item, dict):
                    continue

                # 提取漏洞信息
                if 'info' in item:
                    vuln_info = item['info']
                    vulnerability = {
                        "name": vuln_info.get('name', 'Unknown'),
                        "severity": vuln_info.get('severity', 'unknown'),
                        "description": vuln_info.get('description', ''),
                        "template_id": item.get('template-id', ''),
                        "matched_at": item.get('matched-at', ''),
                        "tags": vuln_info.get('tags', [])
                    }
                    extracted["vulnerabilities"].append(vulnerability)

                    # 统计严重性分布
                    severity = vuln_info.get('severity', 'unknown')
                    extracted["severity_distribution"][severity] = extracted["severity_distribution"].get(severity, 0) + 1

                    # 收集模板ID
                    template_id = item.get('template-id', '')
                    if template_id and template_id not in extracted["template_ids"]:
                        extracted["template_ids"].append(template_id)

                # 提取目标主机
                if 'matched-at' in item:
                    matched_at = item['matched-at']
                    if matched_at:
                        # 提取主机名
                        from urllib.parse import urlparse
                        parsed = urlparse(matched_at)
                        host = parsed.netloc
                        if host and host not in extracted["target_hosts"]:
                            extracted["target_hosts"].append(host)

            # 扫描信息汇总
            extracted["scan_info"] = {
                "unique_hosts": len(extracted["target_hosts"]),
                "unique_templates": len(extracted["template_ids"]),
                "high_severity": extracted["severity_distribution"].get("high", 0),
                "critical_severity": extracted["severity_distribution"].get("critical", 0),
                "medium_severity": extracted["severity_distribution"].get("medium", 0),
                "low_severity": extracted["severity_distribution"].get("low", 0),
                "info_severity": extracted["severity_distribution"].get("info", 0)
            }

        except Exception as e:
            logger.error(f"数据提取错误: {e}")
            extracted["extraction_error"] = str(e)

        return extracted

    def process_directory(self, directory: str, pattern: str = "*.json") -> List[JSONProcessingResult]:
        """处理目录中的JSON文件"""
        results = []
        directory_path = Path(directory)

        if not directory_path.exists():
            logger.error(f"目录不存在: {directory}")
            return results

        # 查找匹配的文件
        json_files = list(directory_path.glob(pattern))
        logger.info(f"找到 {len(json_files)} 个JSON文件")

        for file_path in json_files:
            logger.info(f"处理文件: {file_path}")
            result = self.process_nuclei_json_file(str(file_path))
            results.append(result)

            self.processed_files += 1
            self.total_errors += len(result.errors_found)
            self.total_fixes += len(result.errors_fixed)

        return results

    def generate_processing_report(self, results: List[JSONProcessingResult]) -> str:
        """生成处理报告"""
        report = f"""
# Enhanced JSON Processor 处理报告

**处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**处理文件数**: {len(results)}

---

## 📊 处理统计

### 总体统计
- **成功处理**: {len([r for r in results if r.status == 'success'])} 个文件
- **处理失败**: {len([r for r in results if r.status != 'success'])} 个文件
- **发现错误**: {sum(len(r.errors_found) for r in results)} 个
- **修复错误**: {sum(len(r.errors_fixed) for r in results)} 个

### 文件状态分布
"""

        status_count = {}
        for result in results:
            status = result.status
            status_count[status] = status_count.get(status, 0) + 1

        for status, count in status_count.items():
            report += f"- **{status}**: {count} 个文件\n"

        # 成功处理的文件详情
        successful_results = [r for r in results if r.status == 'success']
        if successful_results:
            report += "\n---\n\n## ✅ 成功处理的文件\n\n"

            total_vulnerabilities = 0
            total_hosts = 0
            severity_totals = {}

            for result in successful_results[:10]:  # 限制显示数量
                data = result.data_extracted
                vulns = len(data.get('vulnerabilities', []))
                hosts = len(data.get('target_hosts', []))

                total_vulnerabilities += vulns
                total_hosts += hosts

                report += f"""
### {os.path.basename(result.file_path)}
- **发现漏洞**: {vulns} 个
- **目标主机**: {hosts} 个
- **处理时间**: {result.processing_time:.2f}秒
- **文件大小**: {result.original_size} → {result.processed_size} 字节
"""

                # 统计严重性分布
                severity_dist = data.get('severity_distribution', {})
                for severity, count in severity_dist.items():
                    severity_totals[severity] = severity_totals.get(severity, 0) + count

            report += f"""
### 汇总统计
- **总漏洞数**: {total_vulnerabilities}
- **总目标主机**: {total_hosts}
"""

            if severity_totals:
                report += "### 严重性分布\n"
                for severity, count in sorted(severity_totals.items()):
                    report += f"- **{severity}**: {count} 个\n"

        # 处理失败的文件
        failed_results = [r for r in results if r.status != 'success']
        if failed_results:
            report += "\n---\n\n## ❌ 处理失败的文件\n\n"

            for result in failed_results[:10]:  # 限制显示数量
                report += f"""
### {os.path.basename(result.file_path)}
- **状态**: {result.status}
- **错误数量**: {len(result.errors_found)}
- **主要错误**: {result.errors_found[0] if result.errors_found else 'N/A'}
"""

        # 错误修复统计
        total_fixes = sum(len(r.errors_fixed) for r in results)
        if total_fixes > 0:
            report += "\n---\n\n## 🔧 错误修复统计\n\n"
            report += f"**总修复数**: {total_fixes} 个\n"

            # 统计常见修复类型
            fix_types = {}
            for result in results:
                for fix in result.errors_fixed:
                    fix_type = fix.split(':')[0] if ':' in fix else fix
                    fix_types[fix_type] = fix_types.get(fix_type, 0) + 1

            if fix_types:
                report += "### 修复类型分布\n"
                for fix_type, count in sorted(fix_types.items(), key=lambda x: x[1], reverse=True):
                    report += f"- **{fix_type}**: {count} 次\n"

        report += f"""

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**处理器版本**: Enhanced JSON Processor v1.0.0

> 💡 此报告由Enhanced JSON Processor自动生成
"""

        return report

    def run_processing(self, directory: str = ".", pattern: str = "*.json") -> List[JSONProcessingResult]:
        """运行JSON处理"""
        logger.info(f"开始处理目录: {directory}, 模式: {pattern}")

        results = self.process_directory(directory, pattern)

        # 生成报告
        report = self.generate_processing_report(results)

        # 保存报告
        report_filename = f"json_processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)

        # 保存详细结果
        results_filename = f"json_processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_data = {
            'processing_info': {
                'time': datetime.now().isoformat(),
                'directory': directory,
                'pattern': pattern,
                'total_files': len(results),
                'processor_version': 'v1.0.0'
            },
            'summary': {
                'processed_files': self.processed_files,
                'total_errors': self.total_errors,
                'total_fixes': self.total_fixes,
                'success_rate': (len([r for r in results if r.status == 'success']) / max(1, len(results))) * 100
            },
            'results': [r.__dict__ for r in results]
        }

        with open(results_filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"处理完成！报告已保存: {report_filename}")
        logger.info(f"详细结果已保存: {results_filename}")

        return results

def main():
    """主函数"""
    print("Enhanced JSON Processor v1.0.0")
    print("=" * 80)

    processor = EnhancedJSONProcessor()

    # 处理当前目录的JSON文件
    print("开始处理Nuclei AI工具的JSON文件...")
    results = processor.run_processing(".", "*.json")

    print(f"\n处理完成！")
    print(f"处理文件数: {len(results)}")
    print(f"成功处理: {len([r for r in results if r.status == 'success'])}")
    print(f"发现错误: {processor.total_errors}")
    print(f"修复错误: {processor.total_fixes}")

    # 显示一些统计信息
    successful_results = [r for r in results if r.status == 'success']
    if successful_results:
        total_vulns = sum(len(r.data_extracted.get('vulnerabilities', [])) for r in successful_results)
        total_hosts = sum(len(r.data_extracted.get('target_hosts', [])) for r in successful_results)

        print(f"\n提取的数据统计:")
        print(f"  - 总漏洞数: {total_vulns}")
        print(f"  - 总目标主机: {total_hosts}")

if __name__ == "__main__":
    main()