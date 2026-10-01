#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据Schema验证工具
Unified Data Schema Validator for Dragon-V Triple Bot v3.2.0

基于统一Schema标准验证所有数据文件的格式正确性
"""

import os
import sys
import json
import yaml
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schema_validation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SchemaValidator:
    """统一数据Schema验证器"""

    def __init__(self):
        self.schema_file = "schema_unified.yaml"
        self.validation_rules = self._load_validation_rules()
        self.validation_results = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'errors': [],
            'warnings': [],
            'file_results': {}
        }

    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            # 必需字段定义
            'required_fields': {
                'vulnerability': ['metadata.id', 'metadata.name', 'metadata.category', 'vulnerability.cve_id'],
                'fingerprint': ['metadata.id', 'metadata.name', 'metadata.category', 'fingerprint.product.name'],
                'mcp_module': ['metadata.id', 'metadata.name', 'metadata.category', 'mcp_module.module.id'],
                'dataset': ['metadata.id', 'metadata.name', 'metadata.category', 'dataset.dataset.name']
            },

            # 枚举值验证
            'enum_values': {
                'metadata.category': ['vulnerability', 'fingerprint', 'mcp_module', 'dataset'],
                'metadata.severity': ['critical', 'high', 'medium', 'low', 'info'],
                'metadata.status': ['active', 'deprecated', 'experimental'],
                'vulnerability.cvss.severity': ['critical', 'high', 'medium', 'low'],
                'fingerprint.confidence.level': ['high', 'medium', 'low'],
                'dataset.dataset.type': ['jailbreak', 'prompt_injection', 'toxicity', 'bias', 'safety']
            },

            # 格式验证正则表达式
            'format_patterns': {
                'cve_id': r'^CVE-\d{4}-\d{4,}$',
                'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                'semantic_version': r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$',
                'datetime_iso': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$',
                'url': r'^https?://[^\s/$.?#].[^\s]*$'
            },

            # 最大长度限制
            'max_lengths': {
                'metadata.name': 100,
                'metadata.description': 1000,
                'metadata.description_zh': 1000,
                'metadata.title': 200,
                'vulnerability.description': 5000,
                'vulnerability.details': 10000
            }
        }

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """验证单个文件"""
        logger.info(f"验证文件: {file_path}")

        result = {
            'file_path': file_path,
            'valid': False,
            'errors': [],
            'warnings': [],
            'category': self._detect_file_category(file_path),
            'validation_time': datetime.now().isoformat()
        }

        try:
            # 读取文件
            data = self._read_file(file_path)
            if data is None:
                result['errors'].append("无法读取文件或文件为空")
                return result

            # 检测文件类型并验证
            category = result['category']
            if category == 'unknown':
                result['warnings'].append("无法检测文件类型，跳过详细验证")
                result['valid'] = True  # 未知文件视为有效
                return result

            # 执行分类验证
            validation_method = getattr(self, f'_validate_{category}')
            category_result = validation_method(data)

            result.update(category_result)
            result['valid'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"验证过程中发生错误: {str(e)}")
            logger.error(f"验证文件 {file_path} 时出错: {e}")

        return result

    def _read_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    return json.load(f)
                elif file_path.endswith(('.yaml', '.yml')):
                    return yaml.safe_load(f)
                else:
                    return None
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {e}")
            return None

    def _detect_file_category(self, file_path: str) -> str:
        """检测文件类型"""
        path_parts = Path(file_path).parts

        if 'vuln' in path_parts or 'vuln_en' in path_parts:
            return 'vulnerability'
        elif 'fingerprints' in path_parts:
            return 'fingerprint'
        elif 'mcp' in path_parts:
            return 'mcp_module'
        elif 'eval' in path_parts:
            return 'dataset'
        else:
            return 'unknown'

    def _validate_vulnerability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证漏洞数据格式"""
        result = {'errors': [], 'warnings': []}

        # 验证通用元数据
        self._validate_metadata(data, 'vulnerability', result)

        # 验证漏洞特定字段
        if 'vulnerability' in data:
            vuln = data['vulnerability']

            # 验证CVE ID
            if 'cve_id' in vuln:
                self._validate_format(vuln['cve_id'], 'cve_id', 'vulnerability.cve_id', result)

            # 验证CVSS评分
            if 'cvss' in vuln:
                self._validate_cvss(vuln['cvss'], result)

            # 验证影响范围
            if 'affected' in vuln:
                self._validate_affected(vuln['affected'], result)

            # 验证解决方案
            if 'solution' in vuln:
                self._validate_solution(vuln['solution'], result)

        return result

    def _validate_fingerprint(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证指纹数据格式"""
        result = {'errors': [], 'warnings': []}

        # 验证通用元数据
        self._validate_metadata(data, 'fingerprint', result)

        # 验证指纹特定字段
        if 'fingerprint' in data:
            fp = data['fingerprint']

            # 验证产品信息
            if 'product' in fp:
                self._validate_product(fp['product'], result)

            # 验证技术信息
            if 'technology' in fp:
                self._validate_technology(fp['technology'], result)

            # 验证检测规则
            if 'detection' in fp:
                self._validate_detection(fp['detection'], result)

            # 验证置信度
            if 'confidence' in fp:
                self._validate_confidence(fp['confidence'], result)

        return result

    def _validate_mcp_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证MCP模块数据格式"""
        result = {'errors': [], 'warnings': []}

        # 验证通用元数据
        self._validate_metadata(data, 'mcp_module', result)

        # 验证MCP模块特定字段
        if 'mcp_module' in data:
            mcp = data['mcp_module']

            # 验证模块信息
            if 'module' in mcp:
                self._validate_module_info(mcp['module'], result)

            # 验证功能描述
            if 'functionality' in mcp:
                self._validate_functionality(mcp['functionality'], result)

            # 验证配置参数
            if 'configuration' in mcp:
                self._validate_configuration(mcp['configuration'], result)

            # 验证检测规则
            if 'detection_rules' in mcp:
                self._validate_detection_rules(mcp['detection_rules'], result)

        return result

    def _validate_dataset(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据集格式"""
        result = {'errors': [], 'warnings': []}

        # 验证通用元数据
        self._validate_metadata(data, 'dataset', result)

        # 验证数据集特定字段
        if 'dataset' in data:
            ds = data['dataset']

            # 验证数据集信息
            if 'dataset' in ds:
                self._validate_dataset_info(ds['dataset'], result)

            # 验证统计数据
            if 'statistics' in ds:
                self._validate_statistics(ds['statistics'], result)

            # 验证样本数据
            if 'samples' in ds:
                self._validate_samples(ds['samples'], result)

            # 验证评估指标
            if 'evaluation' in ds:
                self._validate_evaluation(ds['evaluation'], result)

        return result

    def _validate_metadata(self, data: Dict[str, Any], category: str, result: Dict[str, Any]):
        """验证通用元数据"""
        if 'metadata' not in data:
            result['errors'].append("缺少必需的metadata字段")
            return

        metadata = data['metadata']

        # 验证必需字段
        required_fields = self.validation_rules['required_fields'].get(category, [])
        for field in required_fields:
            if not self._get_nested_value(data, field):
                result['errors'].append(f"缺少必需字段: {field}")

        # 验证ID格式
        if 'id' in metadata:
            id_value = metadata['id']
            if not self._validate_format(id_value, 'uuid', 'metadata.id', result):
                # 如果不是UUID格式，尝试生成UUID
                if isinstance(id_value, str) and len(id_value) > 0:
                    result['warnings'].append(f"建议使用UUID格式的ID: {id_value}")

        # 验证枚举值
        for field, allowed_values in self.validation_rules['enum_values'].items():
            value = self._get_nested_value(metadata, field)
            if value and value not in allowed_values:
                result['errors'].append(f"无效的枚举值: {field} = {value}, 允许值: {allowed_values}")

        # 验证时间格式
        for time_field in ['created_at', 'updated_at', 'verified_at']:
            value = self._get_nested_value(metadata, time_field)
            if value and not self._validate_format(value, 'datetime_iso', f'metadata.{time_field}', result):
                result['warnings'].append(f"建议使用ISO 8601格式的时间: {time_field}")

        # 验证字段长度
        for field, max_len in self.validation_rules['max_lengths'].items():
            value = self._get_nested_value(metadata, field)
            if value and isinstance(value, str) and len(value) > max_len:
                result['warnings'].append(f"字段长度超过限制: {field} ({len(value)} > {max_len})")

        # 验证URL格式
        if 'source' in metadata:
            if isinstance(metadata['source'], list):
                for i, url in enumerate(metadata['source']):
                    if url and not self._validate_format(url, 'url', f'metadata.source[{i}]', result):
                        result['warnings'].append(f"可能的无效URL: {url}")

    def _validate_cvss(self, cvss: Dict[str, Any], result: Dict[str, Any]):
        """验证CVSS评分"""
        # 验证CVSS版本
        if 'version' in cvss and cvss['version'] not in ['2.0', '3.0', '3.1']:
            result['warnings'].append(f"不常见的CVSS版本: {cvss['version']}")

        # 验证基础评分范围
        if 'base_score' in cvss:
            score = cvss['base_score']
            if not isinstance(score, (int, float)) or not (0 <= score <= 10):
                result['errors'].append(f"无效的CVSS基础评分: {score}")

        # 验证严重程度一致性
        if 'severity' in cvss and 'base_score' in cvss:
            severity = cvss['severity'].lower()
            score = cvss['base_score']
            expected_severity = self._get_cvss_severity(score)
            if severity != expected_severity:
                result['warnings'].append(f"CVSS严重程度不一致: 评分{score}应为{expected_severity}，实际为{severity}")

    def _validate_affected(self, affected: Dict[str, Any], result: Dict[str, Any]):
        """验证影响范围"""
        required_affected_fields = ['vendor', 'product']
        for field in required_affected_fields:
            if field not in affected or not affected[field]:
                result['errors'].append(f"affected字段缺少必需的{field}")

    def _validate_solution(self, solution: Dict[str, Any], result: Dict[str, Any]):
        """验证解决方案"""
        if 'patched_versions' in solution and not isinstance(solution['patched_versions'], list):
            result['errors'].append("patched_versions必须是数组类型")

    def _validate_product(self, product: Dict[str, Any], result: Dict[str, Any]):
        """验证产品信息"""
        if 'name' not in product or not product['name']:
            result['errors'].append("产品缺少name字段")

    def _validate_technology(self, technology: Dict[str, Any], result: Dict[str, Any]):
        """验证技术信息"""
        tech_fields = ['language', 'framework', 'database', 'server']
        for field in tech_fields:
            if field in technology and not isinstance(technology[field], list):
                result['warnings'].append(f"{field}字段建议使用数组类型")

    def _validate_detection(self, detection: Dict[str, Any], result: Dict[str, Any]):
        """验证检测规则"""
        detection_types = ['http', 'dns', 'port', 'file']
        has_valid_detection = False

        for det_type in detection_types:
            if det_type in detection and detection[det_type]:
                has_valid_detection = True
                for rule in detection[det_type]:
                    if isinstance(rule, dict):
                        self._validate_detection_rule(rule, det_type, result)

        if not has_valid_detection:
            result['warnings'].append("未找到有效的检测规则")

    def _validate_detection_rule(self, rule: Dict[str, Any], rule_type: str, result: Dict[str, Any]):
        """验证单个检测规则"""
        if rule_type == 'http':
            if 'path' not in rule:
                result['errors'].append("HTTP检测规则缺少path字段")
            if 'matchers' not in rule and 'body' not in rule and 'status_code' not in rule:
                result['warnings'].append("HTTP检测规则缺少匹配条件")

    def _validate_confidence(self, confidence: Dict[str, Any], result: Dict[str, Any]):
        """验证置信度"""
        if 'level' in confidence:
            level = confidence['level']
            if level not in ['high', 'medium', 'low']:
                result['errors'].append(f"无效的置信度等级: {level}")

        if 'score' in confidence:
            score = confidence['score']
            if not isinstance(score, (int, float)) or not (0 <= score <= 1):
                result['errors'].append(f"置信度分数必须在0-1之间: {score}")

    def _validate_module_info(self, module: Dict[str, Any], result: Dict[str, Any]):
        """验证模块信息"""
        if 'id' not in module:
            result['errors'].append("模块缺少id字段")
        if 'name' not in module:
            result['errors'].append("模块缺少name字段")

    def _validate_functionality(self, functionality: Dict[str, Any], result: Dict[str, Any]):
        """验证功能描述"""
        if 'capabilities' in functionality and not isinstance(functionality['capabilities'], list):
            result['warnings'].append("capabilities字段建议使用数组类型")

    def _validate_configuration(self, configuration: Dict[str, Any], result: Dict[str, Any]):
        """验证配置参数"""
        if 'parameters' in configuration:
            for param in configuration['parameters']:
                if isinstance(param, dict):
                    if 'name' not in param:
                        result['errors'].append("配置参数缺少name字段")
                    if 'type' not in param:
                        result['warnings'].append("配置参数缺少type字段")

    def _validate_detection_rules(self, rules: List[Dict[str, Any]], result: Dict[str, Any]):
        """验证检测规则列表"""
        if not isinstance(rules, list):
            result['errors'].append("detection_rules必须是数组类型")
            return

        for i, rule in enumerate(rules):
            if isinstance(rule, dict):
                if 'id' not in rule:
                    result['errors'].append(f"检测规则[{i}]缺少id字段")
                if 'pattern' not in rule and not rule.get('pattern'):  # 允许空字符串
                    result['warnings'].append(f"检测规则[{i}]缺少pattern字段")

    def _validate_dataset_info(self, dataset_info: Dict[str, Any], result: Dict[str, Any]):
        """验证数据集信息"""
        if 'name' not in dataset_info:
            result['errors'].append("数据集缺少name字段")

    def _validate_statistics(self, statistics: Dict[str, Any], result: Dict[str, Any]):
        """验证统计数据"""
        numeric_fields = ['total_samples', 'quality_score', 'diversity_score']
        for field in numeric_fields:
            if field in statistics:
                value = statistics[field]
                if not isinstance(value, (int, float)):
                    result['errors'].append(f"{field}必须是数字类型")

    def _validate_samples(self, samples: List[Dict[str, Any]], result: Dict[str, Any]):
        """验证样本数据"""
        if not isinstance(samples, list):
            result['errors'].append("samples必须是数组类型")
            return

        for i, sample in enumerate(samples):
            if isinstance(sample, dict):
                if 'prompt' not in sample:
                    result['warnings'].append(f"样本[{i}]缺少prompt字段")

    def _validate_evaluation(self, evaluation: Dict[str, Any], result: Dict[str, Any]):
        """验证评估指标"""
        if 'metrics' in evaluation:
            for metric in evaluation['metrics']:
                if isinstance(metric, dict):
                    if 'name' not in metric:
                        result['errors'].append("评估指标缺少name字段")

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典的值"""
        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _validate_format(self, value: str, pattern_name: str, field_path: str, result: Dict[str, Any]) -> bool:
        """验证格式"""
        if not isinstance(value, str):
            return False

        pattern = self.validation_rules['format_patterns'].get(pattern_name)
        if not pattern:
            return True

        if not re.match(pattern, value):
            result['errors'].append(f"格式验证失败: {field_path} = {value} (应为{pattern_name}格式)")
            return False

        return True

    def _get_cvss_severity(self, score: float) -> str:
        """根据CVSS评分获取严重程度"""
        if score >= 9.0:
            return 'critical'
        elif score >= 7.0:
            return 'high'
        elif score >= 4.0:
            return 'medium'
        else:
            return 'low'

    def validate_directory(self, directory: str, file_pattern: str = "*") -> Dict[str, Any]:
        """验证目录中的所有文件"""
        logger.info(f"开始验证目录: {directory}")

        directory_path = Path(directory)
        if not directory_path.exists():
            result = {'error': f"目录不存在: {directory}"}
            return result

        # 查找所有符合条件的文件
        files = list(directory_path.rglob(file_pattern))
        self.validation_results['total_files'] = len(files)

        logger.info(f"找到 {len(files)} 个文件")

        # 逐个验证文件
        for file_path in files:
            if file_path.is_file() and file_path.suffix in ['.json', '.yaml', '.yml']:
                file_result = self.validate_file(str(file_path))
                self.validation_results['file_results'][str(file_path)] = file_result

                if file_result['valid']:
                    self.validation_results['valid_files'] += 1
                else:
                    self.validation_results['invalid_files'] += 1
                    self.validation_results['errors'].extend([
                        f"{file_path}: {error}" for error in file_result['errors']
                    ])

                self.validation_results['warnings'].extend([
                    f"{file_path}: {warning}" for warning in file_result['warnings']
                ])

        return self.validation_results

    def generate_report(self, output_file: str = None) -> str:
        """生成验证报告"""
        report = f"""
# 数据Schema验证报告
**生成时间**: {datetime.now().isoformat()}
**验证工具**: Dragon-V Triple Bot Schema Validator v1.0

## 📊 验证统计

- **总文件数**: {self.validation_results['total_files']}
- **有效文件**: {self.validation_results['valid_files']}
- **无效文件**: {self.validation_results['invalid_files']}
- **成功率**: {self.validation_results['valid_files']/max(self.validation_results['total_files'], 1)*.1:.1%}

## 🚨 错误列表

"""

        if self.validation_results['errors']:
            for error in self.validation_results['errors'][:20]:  # 限制显示数量
                report += f"- [错误] {error}\n"
        else:
            report += "- 无错误\n"

        report += "\n## 警告列表\n"

        if self.validation_results['warnings']:
            for warning in self.validation_results['warnings'][:20]:  # 限制显示数量
                report += f"- [警告] {warning}\n"
        else:
            report += "- 无警告\n"

        report += "\n## 📋 详细结果\n"

        # 按文件类型统计
        category_stats = {}
        for file_path, result in self.validation_results['file_results'].items():
            category = result['category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'valid': 0, 'invalid': 0}

            category_stats[category]['total'] += 1
            if result['valid']:
                category_stats[category]['valid'] += 1
            else:
                category_stats[category]['invalid'] += 1

        for category, stats in category_stats.items():
            success_rate = stats['valid']/stats['total']*100 if stats['total'] > 0 else 0
            report += f"- **{category}**: {stats['valid']}/{stats['total']} ({success_rate:.1f}%)\n"

        # 保存报告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


def main():
    """主函数"""
    validator = SchemaValidator()

    print("Dragon-V Triple Bot 数据Schema验证工具")
    print("=" * 50)

    # 验证各个目录
    directories = ['eval/', 'fingerprints/', 'mcp/', 'vuln/', 'vuln_en/']

    for directory in directories:
        if os.path.exists(directory):
            print(f"\n验证目录: {directory}")
            result = validator.validate_directory(directory)

            if 'error' in result:
                print(f"错误: {result['error']}")
            else:
                print(f"完成: {result['valid_files']}/{result['total_files']} 文件有效")

    # 生成报告
    print(f"\n生成验证报告...")
    report = validator.generate_report('schema_validation_report.md')
    print(report)

    print(f"\n详细报告已保存到: schema_validation_report.md")


if __name__ == "__main__":
    main()