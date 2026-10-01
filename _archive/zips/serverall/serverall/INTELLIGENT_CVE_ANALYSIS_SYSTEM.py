#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能CVE查询和分析系统
Intelligent CVE Query and Analysis System for Dragon-V Triple Bot v3.2.0

基于统一Schema标准化的CVE数据库，提供智能查询、分析和匹配功能
"""

import os
import sys
import yaml
import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from collections import defaultdict, Counter
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cve_analysis_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntelligentCVEAnalysisSystem:
    """智能CVE查询和分析系统"""

    def __init__(self):
        self.unified_dir = "vuln_unified/"
        self.db_path = "cve_analysis_database.db"

        # 初始化数据存储
        self.cve_database = {}
        self.category_index = defaultdict(list)
        self.severity_index = defaultdict(list)
        self.product_index = defaultdict(list)
        self.cwe_index = defaultdict(list)

        # 统计缓存
        self.statistics_cache = {}
        self.last_cache_update = None

        # 加载数据
        self._load_unified_cve_data()
        self._initialize_database()

    def _load_unified_cve_data(self):
        """加载统一格式的CVE数据"""
        logger.info("开始加载统一CVE数据...")

        if not os.path.exists(self.unified_dir):
            logger.error(f"统一CVE目录不存在: {self.unified_dir}")
            return

        yaml_files = list(Path(self.unified_dir).rglob("*.yaml"))
        logger.info(f"发现 {len(yaml_files)} 个CVE文件")

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if data and 'metadata' in data and 'vulnerability' in data:
                    cve_id = data['vulnerability']['cve_id']
                    self.cve_database[cve_id] = data

                    # 建立索引
                    self._build_indexes(cve_id, data)

            except Exception as e:
                logger.error(f"加载文件 {yaml_file} 时出错: {e}")

        logger.info(f"成功加载 {len(self.cve_database)} 个CVE条目")

    def _build_indexes(self, cve_id: str, data: Dict[str, Any]):
        """建立查询索引"""
        metadata = data['metadata']
        vulnerability = data['vulnerability']

        # 分类索引
        category = metadata.get('category', 'unknown')
        self.category_index[category].append(cve_id)

        # 严重程度索引
        severity = metadata.get('severity', 'info')
        self.severity_index[severity].append(cve_id)

        # 产品索引
        product = vulnerability.get('affected', {}).get('product', 'unknown')
        self.product_index[product.lower()].append(cve_id)

        # CWE索引
        cwe_id = vulnerability.get('cwe_id')
        if cwe_id:
            self.cwe_index[cwe_id].append(cve_id)

    def _initialize_database(self):
        """初始化SQLite数据库用于高级查询"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建CVE表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cve_table (
                cve_id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                severity TEXT,
                cwe_id TEXT,
                cvss_score REAL,
                product TEXT,
                vendor TEXT,
                description TEXT,
                metadata_json TEXT,
                vulnerability_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建全文搜索索引
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS cve_search USING fts5(
                cve_id, name, description, product, vendor, content=cve_table, content_rowid=rowid
            )
        ''')

        # 导入数据
        for cve_id, data in self.cve_database.items():
            metadata = data['metadata']
            vulnerability = data['vulnerability']

            cursor.execute('''
                INSERT OR REPLACE INTO cve_table
                (cve_id, name, category, severity, cwe_id, cvss_score, product, vendor, description, metadata_json, vulnerability_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cve_id,
                metadata.get('name', ''),
                metadata.get('category', ''),
                metadata.get('severity', ''),
                vulnerability.get('cwe_id', ''),
                vulnerability.get('cvss', {}).get('base_score', 0.0),
                vulnerability.get('affected', {}).get('product', ''),
                vulnerability.get('affected', {}).get('vendor', ''),
                vulnerability.get('description', ''),
                json.dumps(metadata, ensure_ascii=False),
                json.dumps(vulnerability, ensure_ascii=False)
            ))

        # 更新全文搜索索引
        cursor.execute('INSERT INTO cve_search(cve_search) VALUES("rebuild")')

        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")

    def query_by_cve_id(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """根据CVE ID查询"""
        return self.cve_database.get(cve_id)

    def query_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """根据严重程度查询"""
        cve_ids = self.severity_index.get(severity.lower(), [])
        return [self.cve_database[cve_id] for cve_id in cve_ids]

    def query_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根据分类查询"""
        cve_ids = self.category_index.get(category, [])
        return [self.cve_database[cve_id] for cve_id in cve_ids]

    def query_by_product(self, product_name: str) -> List[Dict[str, Any]]:
        """根据产品名称查询"""
        product_lower = product_name.lower()
        matching_cves = []

        for product, cve_ids in self.product_index.items():
            if product_lower in product:
                matching_cves.extend(cve_ids)

        return [self.cve_database[cve_id] for cve_id in matching_cves]

    def full_text_search(self, query: str) -> List[Dict[str, Any]]:
        """全文搜索"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT DISTINCT cve_id FROM cve_search
                WHERE cve_search MATCH ?
                ORDER BY rank
            ''', (query,))

            results = cursor.fetchall()
            cve_ids = [row[0] for row in results]

            return [self.cve_database[cve_id] for cve_id in cve_ids if cve_id in self.cve_database]

        except Exception as e:
            logger.error(f"全文搜索出错: {e}")
            return []
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if (self.last_cache_update and
            datetime.now() - self.last_cache_update < timedelta(hours=1)):
            return self.statistics_cache

        total_cves = len(self.cve_database)

        # 严重程度统计
        severity_stats = {}
        for severity, cve_ids in self.severity_index.items():
            severity_stats[severity] = len(cve_ids)

        # 分类统计
        category_stats = {}
        for category, cve_ids in self.category_index.items():
            category_stats[category] = len(cve_ids)

        # 产品统计（前10）
        product_stats = {}
        product_counts = Counter()
        for data in self.cve_database.values():
            product = data['vulnerability']['affected']['product']
            product_counts[product] += 1

        for product, count in product_counts.most_common(10):
            product_stats[product] = count

        # CVSS评分统计
        cvss_scores = []
        for data in self.cve_database.values():
            score = data['vulnerability']['cvss']['base_score']
            cvss_scores.append(score)

        cvss_stats = {
            'average': sum(cvss_scores) / len(cvss_scores) if cvss_scores else 0,
            'max': max(cvss_scores) if cvss_scores else 0,
            'min': min(cvss_scores) if cvss_scores else 0,
            'critical_count': len([s for s in cvss_scores if s >= 9.0]),
            'high_count': len([s for s in cvss_scores if 7.0 <= s < 9.0]),
            'medium_count': len([s for s in cvss_scores if 4.0 <= s < 7.0]),
            'low_count': len([s for s in cvss_scores if s < 4.0])
        }

        statistics = {
            'total_cves': total_cves,
            'severity_distribution': severity_stats,
            'category_distribution': category_stats,
            'top_products': product_stats,
            'cvss_statistics': cvss_stats,
            'last_updated': datetime.now().isoformat()
        }

        self.statistics_cache = statistics
        self.last_cache_update = datetime.now()

        return statistics

    def find_related_cves(self, cve_id: str, similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """查找相关的CVE"""
        target_cve = self.cve_database.get(cve_id)
        if not target_cve:
            return []

        target_product = target_cve['vulnerability']['affected']['product'].lower()
        target_cwe = target_cve['vulnerability']['cwe_id']
        target_severity = target_cve['metadata']['severity']

        related_cves = []

        for other_id, other_cve in self.cve_database.items():
            if other_id == cve_id:
                continue

            similarity_score = 0

            # 产品相似性
            other_product = other_cve['vulnerability']['affected']['product'].lower()
            if target_product in other_product or other_product in target_product:
                similarity_score += 0.4

            # CWE相同
            if target_cwe and target_cwe == other_cve['vulnerability']['cwe_id']:
                similarity_score += 0.3

            # 严重程度相同
            if target_severity == other_cve['metadata']['severity']:
                similarity_score += 0.2

            # 描述相似性（简单关键词匹配）
            target_desc = set(target_cve['metadata']['description'].lower().split())
            other_desc = set(other_cve['metadata']['description'].lower().split())
            if target_desc and other_desc:
                desc_similarity = len(target_desc & other_desc) / len(target_desc | other_desc)
                similarity_score += desc_similarity * 0.1

            if similarity_score >= similarity_threshold:
                other_cve['similarity_score'] = similarity_score
                related_cves.append(other_cve)

        # 按相似度排序
        related_cves.sort(key=lambda x: x['similarity_score'], reverse=True)

        return related_cves

    def generate_vulnerability_report(self, cve_ids: List[str], report_format: str = 'markdown') -> str:
        """生成漏洞报告"""
        report_data = []

        for cve_id in cve_ids:
            cve_data = self.cve_database.get(cve_id)
            if cve_data:
                report_data.append({
                    'cve_id': cve_id,
                    'name': cve_data['metadata']['name'],
                    'severity': cve_data['metadata']['severity'],
                    'cvss_score': cve_data['vulnerability']['cvss']['base_score'],
                    'description': cve_data['vulnerability']['description'],
                    'affected_product': cve_data['vulnerability']['affected']['product'],
                    'solution': cve_data['vulnerability']['solution']['description']
                })

        if report_format == 'markdown':
            return self._generate_markdown_report(report_data)
        elif report_format == 'json':
            return json.dumps(report_data, ensure_ascii=False, indent=2)
        else:
            return str(report_data)

    def _generate_markdown_report(self, report_data: List[Dict[str, Any]]) -> str:
        """生成Markdown格式报告"""
        report = f"""# 漏洞分析报告
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**数据来源**: Dragon-V Triple Bot 统一CVE数据库
**CVE数量**: {len(report_data)}

---

## 📊 统计摘要

"""

        # 统计信息
        severity_counts = Counter(item['severity'] for item in report_data)
        for severity, count in severity_counts.items():
            report += f"- **{severity.upper()}**: {count} 个\n"

        report += "\n---\n\n## 🚨 漏洞详情\n\n"

        # 漏洞详情
        for i, item in enumerate(report_data, 1):
            report += f"""### {i}. {item['cve_id']}

**产品**: {item['affected_product']}
**严重程度**: {item['severity'].upper()}
**CVSS评分**: {item['cvss_score']}

**描述**:
{item['description']}

**修复建议**:
{item['solution']}

---

"""

        return report

    def recommend_priorities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """推荐修复优先级"""
        prioritized_cves = []

        for cve_id, cve_data in self.cve_database.items():
            metadata = cve_data['metadata']
            vulnerability = cve_data['vulnerability']

            # 计算优先级分数
            score = 0

            # CVSS评分权重 (40%)
            cvss_score = vulnerability['cvss']['base_score']
            score += cvss_score * 0.4

            # 严重程度权重 (30%)
            severity_weights = {
                'critical': 10,
                'high': 7,
                'medium': 4,
                'low': 1,
                'info': 0.5
            }
            score += severity_weights.get(metadata['severity'], 0) * 0.3

            # 产品流行度权重 (20%)
            product = vulnerability['affected']['product'].lower()
            popular_products = ['nginx', 'apache', 'mysql', 'postgresql', 'redis', 'docker', 'kubernetes']
            if any(pop in product for pop in popular_products):
                score += 5 * 0.2

            # 是否有可利用代码权重 (10%)
            if vulnerability.get('exploit_available', False):
                score += 10 * 0.1

            prioritized_cves.append({
                'cve_id': cve_id,
                'priority_score': score,
                'severity': metadata['severity'],
                'cvss_score': cvss_score,
                'product': vulnerability['affected']['product'],
                'name': metadata['name']
            })

        # 按优先级排序
        prioritized_cves.sort(key=lambda x: x['priority_score'], reverse=True)

        return prioritized_cves[:limit]

    def export_data(self, format: str = 'json', filters: Optional[Dict[str, Any]] = None) -> str:
        """导出数据"""
        filtered_data = []

        for cve_id, cve_data in self.cve_database.items():
            # 应用过滤器
            if filters:
                if 'severity' in filters and cve_data['metadata']['severity'] != filters['severity']:
                    continue
                if 'category' in filters and cve_data['metadata']['category'] != filters['category']:
                    continue
                if 'min_cvss' in filters and cve_data['vulnerability']['cvss']['base_score'] < filters['min_cvss']:
                    continue

            filtered_data.append(cve_data)

        if format == 'json':
            return json.dumps(filtered_data, ensure_ascii=False, indent=2)
        elif format == 'csv':
            return self._export_to_csv(filtered_data)
        elif format == 'yaml':
            return yaml.dump(filtered_data, allow_unicode=True, default_flow_style=False)
        else:
            return str(filtered_data)

    def _export_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """导出为CSV格式"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # CSV头部
        writer.writerow([
            'CVE_ID', 'Name', 'Severity', 'CVSS_Score', 'Product',
            'CWE_ID', 'Description', 'Solution'
        ])

        # 数据行
        for item in data:
            writer.writerow([
                item['vulnerability']['cve_id'],
                item['metadata']['name'],
                item['metadata']['severity'],
                item['vulnerability']['cvss']['base_score'],
                item['vulnerability']['affected']['product'],
                item['vulnerability']['cwe_id'],
                item['vulnerability']['description'][:100] + '...',
                item['vulnerability']['solution']['description'][:100] + '...'
            ])

        return output.getvalue()

def main():
    """主函数 - 演示系统功能"""
    system = IntelligentCVEAnalysisSystem()

    print("=" * 80)
    print("Dragon-V Triple Bot 智能CVE查询和分析系统")
    print("=" * 80)

    # 显示统计信息
    print("\n数据库统计信息:")
    stats = system.get_statistics()
    print(f"- 总CVE数量: {stats['total_cves']}")
    print(f"- 严重程度分布: {stats['severity_distribution']}")
    print(f"- 分类分布: {stats['category_distribution']}")
    print(f"- 平均CVSS评分: {stats['cvss_statistics']['average']:.2f}")

    # 演示查询功能
    print("\n查询演示:")

    # 1. 查询高危漏洞
    critical_cves = system.query_by_severity('critical')
    print(f"- 发现 {len(critical_cves)} 个严重漏洞")

    # 2. 全文搜索
    search_results = system.full_text_search('injection')
    print(f"- 全文搜索 'injection' 找到 {len(search_results)} 个结果")

    # 3. 产品查询
    nginx_cves = system.query_by_product('nginx')
    print(f"- Nginx相关漏洞: {len(nginx_cves)} 个")

    # 推荐修复优先级
    print("\n修复优先级推荐:")
    priorities = system.recommend_priorities(5)
    for i, item in enumerate(priorities, 1):
        print(f"{i}. {item['cve_id']} - 优先级分数: {item['priority_score']:.2f}")
        print(f"   产品: {item['product']} | 严重程度: {item['severity']}")

    # 查找相关CVE
    if critical_cves:
        sample_cve = critical_cves[0]['vulnerability']['cve_id']
        related = system.find_related_cves(sample_cve)
        print(f"\n与 {sample_cve} 相关的漏洞: {len(related)} 个")

    # 生成报告
    if critical_cves:
        top_5_cves = [cve['vulnerability']['cve_id'] for cve in critical_cves[:5]]
        report = system.generate_vulnerability_report(top_5_cves)
        report_file = f"cve_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n分析报告已生成: {report_file}")

    print("\n智能CVE分析系统演示完成！")
    print("提示: 可以通过编程接口调用更多高级功能")

if __name__ == "__main__":
    main()