"""
Complete Loan Data CSV Extractor
Convert extracted loan data to CSV format
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any

class LoanDataCSVExtractor:
    def __init__(self):
        self.data_files = [
            'FAST_LOAN_DATA_20251029_034030.json',
            'ENHANCED_LOAN_DATA_20251029_040142.json',
            'QUICK_LOAN_DATA_20251029_041255.json'
        ]
    
    def load_all_data(self) -> Dict[str, Any]:
        """加载所有JSON数据文件"""
        all_data = {}
        
        for file in self.data_files:
            if os.path.exists(file):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_data[file] = data
                        print(f"已加载文件: {file}")
                except Exception as e:
                    print(f"加载文件 {file} 时出错: {e}")
            else:
                print(f"文件不存在: {file}")
        
        return all_data
    
    def extract_loan_products(self, all_data: Dict[str, Any]) -> List[Dict]:
        """提取贷款产品数据"""
        loan_products = []
        
        for filename, data in all_data.items():
            if isinstance(data, dict):
                # 处理主数据文件
                for target_url, site_data in data.items():
                    if isinstance(site_data, dict):
                        # 从增强数据中提取贷款产品
                        if 'loan_products' in site_data:
                            for product in site_data['loan_products']:
                                loan_products.append({
                                    'target_site': target_url,
                                    'data_source': filename,
                                    'product_type': 'loan_product',
                                    'title': product.get('title', ''),
                                    'content_preview': product.get('content_preview', '')[:200],
                                    'link': product.get('link', ''),
                                    'date': product.get('date', ''),
                                    'type': product.get('type', '')
                                })
                        
                        # 从快速数据中提取贷款页面
                        if 'loan_pages' in site_data:
                            for page in site_data['loan_pages']:
                                if page.get('accessible'):
                                    loan_products.append({
                                        'target_site': target_url,
                                        'data_source': filename,
                                        'product_type': 'loan_page',
                                        'title': page.get('title', ''),
                                        'content_preview': page.get('page', ''),
                                        'link': f"{target_url}{page.get('page', '')}",
                                        'date': '',
                                        'type': 'accessible_page'
                                    })
                        
                        # 从快速数据中提取关键端点
                        if 'key_endpoints' in site_data:
                            for endpoint in site_data['key_endpoints']:
                                if endpoint.get('accessible') and 'loan' in endpoint.get('endpoint', '').lower():
                                    loan_products.append({
                                        'target_site': target_url,
                                        'data_source': filename,
                                        'product_type': 'loan_api',
                                        'title': endpoint.get('endpoint', ''),
                                        'content_preview': str(endpoint.get('data_preview', ''))[:200],
                                        'link': f"{target_url}{endpoint.get('endpoint', '')}",
                                        'date': '',
                                        'type': 'api_endpoint'
                                    })
        
        return loan_products
    
    def extract_financial_info(self, all_data: Dict[str, Any]) -> List[Dict]:
        """提取财务信息数据"""
        financial_info = []
        
        for filename, data in all_data.items():
            if isinstance(data, dict):
                for target_url, site_data in data.items():
                    if isinstance(site_data, dict):
                        # 从增强数据中提取财务信息
                        if 'financial_info' in site_data:
                            for info in site_data['financial_info']:
                                financial_info.append({
                                    'target_site': target_url,
                                    'data_source': filename,
                                    'info_type': info.get('type', ''),
                                    'title': info.get('title', ''),
                                    'content': info.get('content_preview', '')[:200],
                                    'link': info.get('link', ''),
                                    'date': info.get('date', ''),
                                    'file_type': info.get('file_type', '')
                                })
                        
                        # 从快速数据中提取API访问信息
                        if 'api_access' in site_data:
                            for api in site_data['api_access']:
                                if api.get('accessible'):
                                    financial_info.append({
                                        'target_site': target_url,
                                        'data_source': filename,
                                        'info_type': 'api_access',
                                        'title': api.get('endpoint', ''),
                                        'content': f"数据数量: {api.get('data_count', 'N/A')}",
                                        'link': f"{target_url}{api.get('endpoint', '')}",
                                        'date': '',
                                        'file_type': api.get('content_type', '')
                                    })
        
        return financial_info
    
    def extract_user_data(self, all_data: Dict[str, Any]) -> List[Dict]:
        """提取用户数据"""
        user_data = []
        
        for filename, data in all_data.items():
            if isinstance(data, dict):
                for target_url, site_data in data.items():
                    if isinstance(site_data, dict):
                        # 从增强数据中提取用户数据
                        if 'user_data' in site_data:
                            for user in site_data['user_data']:
                                if isinstance(user, dict) and 'id' in user:
                                    user_data.append({
                                        'target_site': target_url,
                                        'data_source': filename,
                                        'user_id': user.get('id', ''),
                                        'username': user.get('username', user.get('name', '')),
                                        'email': user.get('email', ''),
                                        'roles': ', '.join(user.get('roles', [])) if isinstance(user.get('roles'), list) else user.get('roles', ''),
                                        'link': user.get('link', ''),
                                        'endpoint': user.get('endpoint', '')
                                    })
        
        return user_data
    
    def extract_admin_access(self, all_data: Dict[str, Any]) -> List[Dict]:
        """提取管理访问数据"""
        admin_access = []
        
        for filename, data in all_data.items():
            if isinstance(data, dict):
                for target_url, site_data in data.items():
                    if isinstance(site_data, dict):
                        # 从增强数据中提取管理访问
                        if 'admin_access' in site_data:
                            for admin in site_data['admin_access']:
                                admin_access.append({
                                    'target_site': target_url,
                                    'data_source': filename,
                                    'page': admin.get('page', ''),
                                    'status_code': admin.get('status_code', ''),
                                    'accessible': admin.get('accessible', False),
                                    'content_length': admin.get('content_length', ''),
                                    'link': f"{target_url}{admin.get('page', '')}"
                                })
                        
                        # 从快速数据中提取管理访问
                        if 'admin_access' in site_data:
                            for admin in site_data['admin_access']:
                                admin_access.append({
                                    'target_site': target_url,
                                    'data_source': filename,
                                    'page': admin.get('page', ''),
                                    'status_code': admin.get('status_code', ''),
                                    'accessible': admin.get('accessible', False),
                                    'content_length': admin.get('content_length', ''),
                                    'link': f"{target_url}{admin.get('page', '')}"
                                })
        
        return admin_access
    
    def save_to_csv(self, data: List[Dict], filename: str, fieldnames: List[str]):
        """保存数据到CSV文件"""
        if not data:
            print(f"没有数据可保存到 {filename}")
            return
            
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f"已保存 {len(data)} 条记录到 {filename}")
    
    def generate_complete_csv_report(self):
        """生成完整的CSV报告"""
        print("开始加载所有贷款数据...")
        all_data = self.load_all_data()
        
        if not all_data:
            print("没有找到数据文件，请先运行数据提取器")
            return
        
        print("正在提取贷款产品数据...")
        loan_products = self.extract_loan_products(all_data)
        
        print("正在提取财务信息数据...")
        financial_info = self.extract_financial_info(all_data)
        
        print("正在提取用户数据...")
        user_data = self.extract_user_data(all_data)
        
        print("正在提取管理访问数据...")
        admin_access = self.extract_admin_access(all_data)
        
        # 保存到CSV文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 贷款产品CSV
        if loan_products:
            self.save_to_csv(loan_products, 
                           f'LOAN_PRODUCTS_{timestamp}.csv',
                           ['target_site', 'data_source', 'product_type', 'title', 'content_preview', 'link', 'date', 'type'])
        
        # 财务信息CSV
        if financial_info:
            self.save_to_csv(financial_info,
                           f'FINANCIAL_INFO_{timestamp}.csv',
                           ['target_site', 'data_source', 'info_type', 'title', 'content', 'link', 'date', 'file_type'])
        
        # 用户数据CSV
        if user_data:
            self.save_to_csv(user_data,
                           f'USER_DATA_{timestamp}.csv',
                           ['target_site', 'data_source', 'user_id', 'username', 'email', 'roles', 'link', 'endpoint'])
        
        # 管理访问CSV
        if admin_access:
            self.save_to_csv(admin_access,
                           f'ADMIN_ACCESS_{timestamp}.csv',
                           ['target_site', 'data_source', 'page', 'status_code', 'accessible', 'content_length', 'link'])
        
        # 生成汇总CSV
        self.generate_summary_csv(all_data, timestamp)
        
        print(f"\n=== CSV数据提取完成 ===")
        print(f"贷款产品: {len(loan_products)} 条记录")
        print(f"财务信息: {len(financial_info)} 条记录")
        print(f"用户数据: {len(user_data)} 条记录")
        print(f"管理访问: {len(admin_access)} 条记录")
    
    def generate_summary_csv(self, all_data: Dict[str, Any], timestamp: str):
        """生成汇总CSV"""
        summary_data = []
        
        for filename, data in all_data.items():
            if isinstance(data, dict):
                for target_url, site_data in data.items():
                    if isinstance(site_data, dict):
                        summary_data.append({
                            'target_site': target_url,
                            'data_source': filename,
                            'loan_products_count': len(site_data.get('loan_products', [])),
                            'financial_info_count': len(site_data.get('financial_info', [])),
                            'user_data_count': len(site_data.get('user_data', [])),
                            'admin_access_count': len(site_data.get('admin_access', [])),
                            'api_endpoints_count': len(site_data.get('api_endpoints', [])),
                            'loan_pages_count': len(site_data.get('loan_pages', [])),
                            'timestamp': site_data.get('timestamp', '')
                        })
        
        if summary_data:
            self.save_to_csv(summary_data,
                           f'LOAN_DATA_SUMMARY_{timestamp}.csv',
                           ['target_site', 'data_source', 'loan_products_count', 'financial_info_count', 
                            'user_data_count', 'admin_access_count', 'api_endpoints_count', 
                            'loan_pages_count', 'timestamp'])

def main():
    extractor = LoanDataCSVExtractor()
    extractor.generate_complete_csv_report()

if __name__ == "__main__":
    main()