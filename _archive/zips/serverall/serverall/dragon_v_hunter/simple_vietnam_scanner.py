#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Vietnam Express Scanner
简化的越南快递扫描器

专注越南快递网站的基本漏洞检测
"""

import sys
import time
import concurrent.futures
import threading
import json
from datetime import datetime
import requests

# 设置 UTF-8 编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

class SimpleVietnamScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.session.timeout = 10

        # 越南快递目标列表
        self.targets = [
            {'name': 'VNPost', 'url': 'https://vnpost.vn', 'priority': 'high'},
            {'name': 'GHN', 'url': 'https://ghn.vn', 'priority': 'high'},
            {'name': 'GHTK', 'url': 'https://ghtk.net', 'priority': 'medium'},
            {'name': 'J&T Vietnam', 'url': 'https://j&t.vn', 'priority': 'medium'}
        ]

        self.results = []
        self.lock = threading.Lock()
        self.total_count = len(self.targets)

    def scan_target(self, target):
        """扫描单个目标"""
        result = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown'
        }

        try:
            print(f"[SCAN] 开始扫描: {target['name']} ({target['url']})")

            # 基本信息获取
            response = self.session.get(target['url'], verify=False)

            if response.status_code == 200:
                result['status'] = 'success'
                result['info'] = {
                    'status_code': response.status_code,
                    'server': response.headers.get('Server', 'Unknown'),
                    'content_length': len(response.content),
                    'response_time': response.elapsed.total_seconds()
                }

                # 检测越南语内容
                content = response.text.lower()
                vietnamese_keywords = ['bưu điện', 'giao hàng', 'vận chuyển', 'don hang', 'tracking']

                detected_keywords = []
                for keyword in vietnamese_keywords:
                    if keyword in content:
                        detected_keywords.append(keyword)

                result['vietnamese_keywords'] = detected_keywords

                # 基本漏洞检测
                vulnerabilities = []

                # 检查常见管理后台
                admin_paths = ['/admin', '/administrator', '/login', '/dashboard']
                for path in admin_paths:
                    admin_url = target['url'] + path
                    try:
                        admin_response = self.session.get(admin_url, verify=False, timeout=5)
                        if admin_response.status_code == 200:
                            vulnerabilities.append(f'发现管理页面: {path}')
                    except:
                        pass

                # 检查订单追踪功能
                order_paths = ['/don-hang', '/tracking', '/track', '/order']
                for path in order_paths:
                    order_url = target['url'] + path
                    try:
                        order_response = self.session.get(order_url, verify=False, timeout=5)
                        if order_response.status_code == 200:
                            vulnerabilities.append(f'发现订单页面: {path}')
                    except:
                        pass

                result['vulnerabilities'] = vulnerabilities
                result['vulnerability_count'] = len(vulnerabilities)

            else:
                result['status'] = 'failed'
                result['error'] = f"HTTP {response.status_code}"

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        with self.lock:
            self.results.append(result)

        return result

    def batch_scan(self, max_workers=2):
        """批量扫描"""
        print("=" * 60)
        print("Simple Vietnam Express Scanner")
        print("简化的越南快递扫描器")
        print("=" * 60)
        print(f"目标数量: {self.total_count}")
        print(f"开始扫描...")
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
                    print(f"[ERROR] 扫描 {target['name']} 失败: {e}")

        # 生成报告
        self.generate_report()

        end_time = time.time()
        total_time = end_time - start_time

        print("=" * 60)
        print("扫描完成")
        print(f"总耗时: {total_time:.2f} 秒")
        print(f"成功扫描: {len([r for r in self.results if r['status'] == 'success'])}/{self.total_count}")
        print(f"发现漏洞: {len([r for r in self.results if r.get('vulnerability_count', 0) > 0])}")
        print("=" * 60)

    def generate_report(self):
        """生成报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simple_vietnam_scan_report_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"[SUCCESS] 报告已保存: {filename}")

            # 输出简要总结
            print("\n扫描总结:")
            for result in self.results:
                status_icon = "✓" if result['status'] == 'success' else "✗"
                vuln_count = result.get('vulnerability_count', 0)
                print(f"  {status_icon} {result['target']['name']}: {vuln_count} 个问题")

                if result.get('vulnerabilities'):
                    for vuln in result['vulnerabilities']:
                        print(f"    - {vuln}")

        except Exception as e:
            print(f"[ERROR] 生成报告失败: {e}")

def main():
    print("Simple Vietnam Express Scanner")
    print("简化的越南快递扫描器")
    print("启动中...")

    scanner = SimpleVietnamScanner()

    try:
        scanner.batch_scan(max_workers=2)
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断扫描")
    except Exception as e:
        print(f"[ERROR] 扫描错误: {e}")

    print("[INFO] 扫描器已关闭")

if __name__ == "__main__":
    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    main()