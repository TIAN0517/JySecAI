#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一CVE文件验证工具
Unified CVE Files Validator for Dragon-V Triple Bot v3.2.0

专门验证vuln_unified/目录下的统一格式CVE文件
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class UnifiedCVEValidator:
    """统一CVE文件验证器"""

    def __init__(self):
        self.unified_dir = "vuln_unified/"
        self.valid_files = 0
        self.invalid_files = 0
        self.total_files = 0
        self.errors = []
        self.warnings = []

        # 必需的metadata字段
        self.required_metadata_fields = [
            'id', 'name', 'title', 'description', 'category', 'severity',
            'author', 'maintainer', 'version', 'created_at', 'updated_at',
            'status', 'verified', 'verified_by', 'verified_at', 'license', 'copyright'
        ]

        # 必需的vulnerability字段
        self.required_vulnerability_fields = [
            'cve_id', 'cvss', 'affected', 'description', 'solution', 'timeline'
        ]

    def validate_unified_files(self) -> Dict[str, Any]:
        """验证所有统一格式CVE文件"""
        print(f"开始验证统一CVE文件...")
        print(f"目标目录: {self.unified_dir}")

        if not os.path.exists(self.unified_dir):
            print(f"错误: 目录 {self.unified_dir} 不存在")
            return {}

        # 递归查找所有YAML文件
        yaml_files = list(Path(self.unified_dir).rglob("*.yaml"))
        self.total_files = len(yaml_files)

        print(f"找到 {self.total_files} 个CVE文件")

        for yaml_file in yaml_files:
            try:
                self._validate_single_file(yaml_file)
            except Exception as e:
                error_msg = f"验证文件 {yaml_file} 时出错: {str(e)}"
                self.errors.append(error_msg)
                self.invalid_files += 1

        # 生成验证结果
        result = {
            'total_files': self.total_files,
            'valid_files': self.valid_files,
            'invalid_files': self.invalid_files,
            'success_rate': (self.valid_files / self.total_files * 100) if self.total_files > 0 else 0,
            'errors': self.errors,
            'warnings': self.warnings
        }

        return result

    def _validate_single_file(self, file_path: Path):
        """验证单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # 验证基本结构
            if not isinstance(data, dict):
                self.errors.append(f"{file_path}: 文件根节点必须是字典")
                self.invalid_files += 1
                return

            # 验证metadata字段
            metadata = data.get('metadata')
            if not metadata:
                self.errors.append(f"{file_path}: 缺少metadata字段")
                self.invalid_files += 1
                return

            # 检查必需的metadata字段
            missing_fields = []
            for field in self.required_metadata_fields:
                if field not in metadata:
                    missing_fields.append(field)

            if missing_fields:
                self.errors.append(f"{file_path}: 缺少必需的metadata字段: {', '.join(missing_fields)}")
                self.invalid_files += 1
                return

            # 验证vulnerability字段
            vulnerability = data.get('vulnerability')
            if not vulnerability:
                self.errors.append(f"{file_path}: 缺少vulnerability字段")
                self.invalid_files += 1
                return

            # 检查必需的vulnerability字段
            missing_vuln_fields = []
            for field in self.required_vulnerability_fields:
                if field not in vulnerability:
                    missing_vuln_fields.append(field)

            if missing_vuln_fields:
                self.errors.append(f"{file_path}: 缺少必需的vulnerability字段: {', '.join(missing_vuln_fields)}")
                self.invalid_files += 1
                return

            # 验证数据类型
            self._validate_data_types(file_path, metadata, vulnerability)

            # 如果没有错误，则文件有效
            self.valid_files += 1
            if self.valid_files % 50 == 0:
                print(f"已验证 {self.valid_files} 个有效文件")

        except yaml.YAMLError as e:
            self.errors.append(f"{file_path}: YAML解析错误 - {str(e)}")
            self.invalid_files += 1
        except Exception as e:
            self.errors.append(f"{file_path}: 验证失败 - {str(e)}")
            self.invalid_files += 1

    def _validate_data_types(self, file_path: Path, metadata: Dict, vulnerability: Dict):
        """验证数据类型"""
        # 验证metadata数据类型
        if not isinstance(metadata.get('tags'), list):
            self.warnings.append(f"{file_path}: metadata.tags应该是列表类型")

        if not isinstance(metadata.get('source'), list):
            self.warnings.append(f"{file_path}: metadata.source应该是列表类型")

        if not isinstance(metadata.get('references'), list):
            self.warnings.append(f"{file_path}: metadata.references应该是列表类型")

        # 验证vulnerability数据类型
        cvss = vulnerability.get('cvss')
        if not isinstance(cvss, dict):
            self.errors.append(f"{file_path}: vulnerability.cvss必须是字典类型")
            self.invalid_files += 1
            return

        affected = vulnerability.get('affected')
        if not isinstance(affected, dict):
            self.errors.append(f"{file_path}: vulnerability.affected必须是字典类型")
            self.invalid_files += 1
            return

        solution = vulnerability.get('solution')
        if not isinstance(solution, dict):
            self.errors.append(f"{file_path}: vulnerability.solution必须是字典类型")
            self.invalid_files += 1
            return

        timeline = vulnerability.get('timeline')
        if not isinstance(timeline, dict):
            self.errors.append(f"{file_path}: vulnerability.timeline必须是字典类型")
            self.invalid_files += 1
            return

    def generate_report(self, result: Dict[str, Any]) -> str:
        """生成验证报告"""
        report = f"""# 统一CVE文件验证报告
**生成时间**: {datetime.now().isoformat()}
**验证工具**: Dragon-V Triple Bot Unified CVE Validator v1.0

## 验证统计

- **总文件数**: {result['total_files']}
- **有效文件**: {result['valid_files']}
- **无效文件**: {result['invalid_files']}
- **成功率**: {result['success_rate']:.1f}%

## 验证结果

验证通过率: {result['success_rate']:.1f}% ({result['valid_files']}/{result['total_files']})

"""

        if result['errors']:
            report += "## 错误列表\n\n"
            for i, error in enumerate(result['errors'][:20], 1):  # 只显示前20个错误
                report += f"{i}. {error}\n"

            if len(result['errors']) > 20:
                report += f"... 还有 {len(result['errors']) - 20} 个错误\n"

        if result['warnings']:
            report += "\n## 警告列表\n\n"
            for i, warning in enumerate(result['warnings'][:10], 1):  # 只显示前10个警告
                report += f"{i}. {warning}\n"

            if len(result['warnings']) > 10:
                report += f"... 还有 {len(result['warnings']) - 10} 个警告\n"

        report += f"""

## 质量评估

- **优秀**: {result['success_rate'] >= 95:.1f}% - 文件格式完全符合统一Schema标准
- **良好**: {80 <= result['success_rate'] < 95:.1f}% - 大部分文件符合标准，少量需要调整
- **一般**: {60 <= result['success_rate'] < 80:.1f}% - 部分文件需要进一步标准化
- **需改进**: {result['success_rate'] < 60:.1f}% - 需要大量标准化工作

## 下一步建议

1. **修复错误**: 优先解决所有验证错误，确保文件结构完整
2. **完善字段**: 补充缺失的必需字段
3. **统一格式**: 确保所有字段的数据类型正确
4. **质量提升**: 持续优化文件质量和一致性

---

**备注**: 统一CVE文件已经按照新的Schema标准进行了格式化，大幅提升了数据质量和一致性。
"""

        return report

def main():
    """主函数"""
    validator = UnifiedCVEValidator()

    print("=" * 60)
    print("Dragon-V Triple Bot 统一CVE文件验证工具")
    print("=" * 60)

    # 执行验证
    result = validator.validate_unified_files()

    if not result:
        print("验证失败：无法读取文件")
        return

    # 显示简要结果
    print(f"\n验证完成！")
    print(f"总文件数: {result['total_files']}")
    print(f"有效文件: {result['valid_files']}")
    print(f"无效文件: {result['invalid_files']}")
    print(f"成功率: {result['success_rate']:.1f}%")

    # 生成详细报告
    report = validator.generate_report(result)

    # 保存报告
    report_file = f"unified_cve_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n详细报告已保存到: {report_file}")

    if result['success_rate'] >= 95:
        print("质量评估: 优秀 - 统一CVE文件高度标准化！")
    elif result['success_rate'] >= 80:
        print("质量评估: 良好 - 大部分文件符合标准")
    else:
        print("质量评估: 需要改进 - 建议进一步标准化")

if __name__ == "__main__":
    main()