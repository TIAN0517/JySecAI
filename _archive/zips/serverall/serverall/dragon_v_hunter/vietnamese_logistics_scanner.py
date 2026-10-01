#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragon-V Vietnamese Logistics System Scanner
越南物流系统批量扫描器

专业级越南快递和物流系统漏洞扫描工具
专注于越南本地化特征和业务逻辑检测

作者: Dragon-V CyberSec Labs
版本: 1.0
日期: 2025-01-25
"""

import sys
import os
import json
import time
import concurrent.futures
import threading
from urllib.parse import urljoin, urlparse
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 确保 UTF-8 编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

class VietnameseLogisticsScanner:
    """越南物流系统扫描器"""

    def __init__(self, config_path: str = "config/vietnam_logistics_targets.json"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.session.timeout = 15

        # 加载越南物流配置
        self.vietnam_logistics_config = {
            'time_zone': 'GMT+7',
            'business_hours': {'start': 8, 'end': 17},
            'language': 'vi',
            'encoding': 'utf-8',
            'company_patterns': {
                'vnpost': ['vnpost.vn', 'bưu điện', 'buu dien', 'bưu điện việt nam'],
                'ghn': ['ghn.vn', 'giao hàng nhanh', 'giaohangnhanh'],
                'ghtk': ['ghtk.net', 'giao hàng tiết kiệm', 'giaohangtiekiem'],
                'j&t': ['j&t.vn', 'j&t express', 'J&T Express Việt Nam'],
                'ninja_van': ['ninja-van.com', 'ninja van', 'ninja express'],
                'viettel_post': ['viettel-post.vn', 'viettel post', 'viettel logistics']
            }
        }

        # 加载目标列表
        self.targets = self._load_targets(config_path)
        self.results = []
        self.lock = threading.Lock()
        self.targets_count = len(self.targets)
        self.scanned_count = 0

    def _load_targets(self, config_path: str) -> list:
        """加载扫描目标"""
        try:
            if not os.path.exists(config_path):
                # 如果配置文件不存在，创建默认目标
                return self._create_default_targets()

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('targets', self._create_default_targets())
        except Exception as e:
            print(f"[WARNING] 配置文件加载失败: {e}")
            return self._create_default_targets()

    def _create_default_targets(self) -> list:
        """创建默认的越南物流目标列表"""
        return [
            {
                'name': 'Vietnam Post (VNPost)',
                'url': 'https://vnpost.vn',
                'company_type': 'vnpost',
                'priority': 'high',
                'description': '越南邮政官方网站'
            },
            {
                'name': 'Giao Hang Nhanh (GHN)',
                'url': 'https://ghn.vn',
                'company_type': 'ghn',
                'priority': 'high',
                'description': '越南快递物流巨头'
            },
            {
                'name': 'Giao Hang Tiet Kiem (GHTK)',
                'url': 'https://ghtk.net',
                'company_type': 'ghtk',
                'priority': 'medium',
                'description': '越南经济快递服务商'
            },
            {
                'name': 'J&T Express Vietnam',
                'url': 'https://j&t.vn',
                'company_type': 'j&t',
                'priority': 'medium',
                'description': 'J&T越南分公司'
            },
            {
                'name': 'Ninja Van Vietnam',
                'url': 'https://ninja-van.com',
                'company_type': 'ninja_van',
                'priority': 'medium',
                'description': 'Ninja Van越南服务'
            },
            {
                'name': 'Viettel Post',
                'url': 'https://viettel-post.vn',
                'company_type': 'viettel_post',
                'priority': 'medium',
                'description': 'Viettel邮政服务'
            }
        ]

    def scan_target(self, target: dict) -> dict:
        """扫描单个目标"""
        result = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'vulnerabilities': [],
            'technologies': [],
            'business_features': [],
            'localization': {
                'vietnamese_detected': False,
                'business_logic_found': False,
                'order_system_detected': False
            }
        }

        try:
            print(f"[SCANNER] 开始扫描: {target['name']} ({target['url']})")
            self.scanned_count += 1

            # 1. 基本信息探测
            self._detect_basic_info(target, result)

            # 2. 技术栈识别
            self._detect_technologies(target, result)

            # 3. 越南本地化特征检测
            self._detect_localization(target, result)

            # 4. 业务逻辑漏洞检测
            self._detect_business_vulnerabilities(target, result)

            # 5. 订单系统检测
            self._detect_order_system(target, result)

            result['status'] = 'completed'
            print(f"[SUCCESS] {target['name']} 扫描完成")

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            print(f"[ERROR] {target['name']} 扫描失败: {e}")

        with self.lock:
            self.results.append(result)

        return result

    def _detect_basic_info(self, target: dict, result: dict):
        """检测基本信息"""
        try:
            response = self.session.get(target['url'], verify=False)

            if response.status_code == 200:
                result['basic_info'] = {
                    'status_code': response.status_code,
                    'server': response.headers.get('Server', 'Unknown'),
                    'content_type': response.headers.get('Content-Type', 'Unknown'),
                    'content_length': len(response.content),
                    'response_time': response.elapsed.total_seconds()
                }

                # 检测越南字符
                vi_keywords = self._get_vietnamese_keywords()
                content_lower = response.text.lower()

                detected_keywords = []
                for keyword in vi_keywords:
                    if keyword.lower() in content_lower:
                        detected_keywords.append(keyword)

                if detected_keywords:
                    result['localization']['vietnamese_detected'] = True
                    result['detected_keywords'] = detected_keywords

        except Exception as e:
            print(f"[ERROR] 基本信息检测失败: {e}")

    def _detect_technologies(self, target: dict, result: dict):
        """检测技术栈"""
        try:
            response = self.session.get(target['url'], verify=False)

            if response.status_code == 200:
                content = response.text.lower()

                # 常见技术栈特征
                tech_signatures = {
                    'php': ['php', '.php', 'php/'],
                    'asp': ['.asp', '.aspx', 'asp.net'],
                    'jsp': ['.jsp', '.jspx', 'java'],
                    'node.js': ['node.js', 'express', 'meteor'],
                    'django': ['django', 'python'],
                    'flask': ['flask', 'python'],
                    'rails': ['rails', 'ruby'],
                    'wordpress': ['wordpress', 'wp-content'],
                    'drupal': ['drupal'],
                    'joomla': ['joomla'],
                    'laravel': ['laravel', 'illuminate'],
                    'codeigniter': ['codeigniter']
                }

                detected_techs = []
                for tech, signatures in tech_signatures.items():
                    for signature in signatures:
                        if signature in content:
                            detected_techs.append(tech)
                            break

                result['technologies'] = list(set(detected_techs))

        except Exception as e:
            print(f"[ERROR] 技术栈检测失败: {e}")

    def _detect_localization(self, target: dict, result: dict):
        """检测越南本地化特征"""
        try:
            response = self.session.get(target['url'], verify=False)

            if response.status_code == 200:
                content = response.text.lower()
                vi_keywords = self._get_vietnamese_keywords()

                detected_count = 0
                for keyword in vi_keywords:
                    if keyword.lower() in content:
                        detected_count += 1

                # 计算越南化程度
                vietnamese_ratio = detected_count / len(vi_keywords)

                result['localization']['vietnamese_detected'] = vietnamese_ratio > 0.1
                result['localization']['vietnamese_ratio'] = vietnamese_ratio
                result['localization']['detected_keywords'] = [
                    kw for kw in vi_keywords
                    if kw.lower() in content
                ][:10]  # 限制显示数量

        except Exception as e:
            print(f"[ERROR] 本地化检测失败: {e}")

    def _detect_business_vulnerabilities(self, target: dict, result: dict):
        """检测业务逻辑漏洞"""
        try:
            # 检测常见的业务逻辑漏洞点
            business_vulns = [
                {
                    'name': '订单ID预测',
                    'type': 'business_logic',
                    'description': '订单ID可能存在可预测模式',
                    'check_func': self._check_order_id_predictability
                },
                {
                    'name': '价格篡改',
                    'type': 'business_logic',
                    'description': '运费或价格参数可能被篡改',
                    'check_func': self._check_price_manipulation
                },
                {
                    'name': '越权访问',
                    'type': 'access_control',
                    'description': '可能存在越权访问漏洞',
                    'check_func': self._check_privilege_escalation
                }
            ]

            for vuln in business_vulns:
                try:
                    is_vulnerable = vuln['check_func'](target)
                    if is_vulnerable:
                        result['vulnerabilities'].append({
                            'name': vuln['name'],
                            'type': vuln['type'],
                            'severity': 'medium',
                            'description': vuln['description']
                        })
                except Exception as e:
                    print(f"[ERROR] {vuln['name']} 检测失败: {e}")

            result['localization']['business_logic_found'] = len(result['vulnerabilities']) > 0

        except Exception as e:
            print(f"[ERROR] 业务漏洞检测失败: {e}")

    def _detect_order_system(self, target: dict, result: dict):
        """检测订单系统"""
        try:
            # 检查订单相关的页面
            order_pages = [
                '/don-hang', '/tracking', '/lich-su-mua-hang',
                '/order', '/track', '/history',
                '/order-tracking', '/lich-su-giao-hang'
            ]

            detected_order_features = []

            for page in order_pages:
                try:
                    url = urljoin(target['url'], page)
                    response = self.session.get(url, verify=False, timeout=10)

                    if response.status_code == 200:
                        content = response.text.lower()

                        if any(keyword in content for keyword in ['don hang', 'tracking', 'lich su']):
                            detected_order_features.append(page)

                except Exception as e:
                    continue

            result['business_features'] = detected_order_features

            if detected_order_features:
                result['localization']['order_system_detected'] = True

        except Exception as e:
            print(f"[ERROR] 订单系统检测失败: {e}")

    def _check_order_id_predictability(self, target: dict) -> bool:
        """检查订单ID可预测性"""
        try:
            # 模拟检查订单ID格式
            order_patterns = [
                r'DH\d{6,8}',  # DH123456
                r'GH\d{6,8}',  # GH123456
                r'TK\d{6,8}',  # TK123456
                r'[A-Z]{2,4}\d{6,8}'  # 多种格式
            ]

            response = self.session.get(target['url'], verify=False)
            content = response.text

            import re
            for pattern in order_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True

            return False

        except Exception:
            return False

    def _check_price_manipulation(self, target: dict) -> bool:
        """检查价格篡改漏洞"""
        try:
            # 检查价格相关参数
            price_params = ['price', 'cost', 'fee', 'amount', 'shipping_cost']

            # 尝试访问价格相关接口
            test_urls = [
                urljoin(target['url'], '/api/calculate'),
                urljoin(target['url'], '/shipping/cost'),
                urljoin(target['url'], '/order/cost')
            ]

            for url in test_urls:
                try:
                    response = self.session.get(url, verify=False)
                    if response.status_code == 200:
                        return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def _check_privilege_escalation(self, target: dict) -> bool:
        """检查越权访问漏洞"""
        try:
            # 检查管理后台访问
            admin_urls = [
                urljoin(target['url'], '/admin'),
                urljoin(target['url'], '/administrator'),
                urljoin(target['url'], '/login'),
                urljoin(target['url'], '/dashboard')
            ]

            for url in admin_urls:
                try:
                    response = self.session.get(url, verify=False)
                    if response.status_code in [200, 403]:  # 可能存在管理页面
                        return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def _get_vietnamese_keywords(self) -> list:
        """获取越南语关键词"""
        return [
            'bưu điện', 'giao hàng', 'vận chuyển', 'đơn hàng',
            'đơn hàng', 'theo dõi', 'lịch sử', 'khách hàng',
            'địa chỉ', 'thanh toán', 'giao hàng nhanh',
            'giao hàng tiết kiệm', 'VNPost', 'GHN', 'GHTK',
            'J&T', 'Viettel Post', 'Ninja Van', 'vận đơn',
            'kho hàng', 'chi nhánh', 'giá cước', 'phí ship'
        ]

    def batch_scan(self, max_workers: int = 3) -> None:
        """批量扫描目标"""
        print("=" * 60)
        print("Dragon-V Vietnamese Logistics System Scanner")
        print("越南物流系统批量扫描器")
        print("=" * 60)
        print(f"[INFO] 已加载 {self.targets_count} 个越南物流目标")
        print(f"[INFO] 开始扫描 {self.targets_count} 个目标")
        print(f"[INFO] 扫描器配置: 最大并发数 {max_workers}")
        print("=" * 60)

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有扫描任务
            future_to_target = {
                executor.submit(self.scan_target, target): target
                for target in self.targets
            }

            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                except Exception as e:
                    print(f"[ERROR] 扫描 {target['name']} 时发生异常: {e}")

        # 生成报告
        self._generate_report()

        end_time = time.time()
        total_time = end_time - start_time

        print("=" * 60)
        print(f"[SUMMARY] 扫描完成")
        print(f"[SUMMARY] 总耗时: {total_time:.2f} 秒")
        print(f"[SUMMARY] 成功扫描: {len([r for r in self.results if r['status'] == 'completed'])}/{self.targets_count}")
        print(f"[SUMMARY] 发现漏洞: {len([r for r in self.results if r.get('vulnerabilities')])}")
        print("=" * 60)

    def _generate_report(self):
        """生成扫描报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vietnam_logistics_scan_report_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            print(f"[SUCCESS] 扫描报告已保存: {filename}")

            # 生成简要总结
            self._generate_summary()

        except Exception as e:
            print(f"[ERROR] 生成报告失败: {e}")

    def _generate_summary(self):
        """生成扫描总结"""
        total_targets = len(self.results)
        completed_targets = len([r for r in self.results if r['status'] == 'completed'])
        vulnerable_targets = len([r for r in self.results if r.get('vulnerabilities')])
        vietnamese_targets = len([r for r in self.results if r['localization']['vietnamese_detected']])

        print("\n" + "=" * 60)
        print("扫描总结")
        print("=" * 60)
        print(f"总目标数: {total_targets}")
        print(f"成功扫描: {completed_targets}")
        print(f"发现漏洞: {vulnerable_targets}")
        print(f"越南本地化: {vietnamese_targets}")

        if vulnerable_targets > 0:
            print(f"\n[WARNING] 发现 {vulnerable_targets} 个存在漏洞的目标:")
            for result in self.results:
                if result.get('vulnerabilities'):
                    print(f"  - {result['target']['name']}: {len(result['vulnerabilities'])} 个漏洞")

        print("=" * 60)

def main():
    """主函数"""
    print("Dragon-V Vietnamese Logistics System Scanner")
    print("越南物流系统批量扫描器 v1.0")
    print("启动中...")

    # 创建扫描器实例
    scanner = VietnameseLogisticsScanner()

    # 执行批量扫描
    try:
        scanner.batch_scan(max_workers=3)
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断扫描")
    except Exception as e:
        print(f"[ERROR] 扫描过程中发生错误: {e}")

    print("[INFO] 扫描器已关闭")

if __name__ == "__main__":
    # Windows 上禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    main()