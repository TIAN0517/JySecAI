#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Data Extractor - API数据提取器
从可访问的API端点提取真实数据
"""

import requests
import json
import time

def extract_from_accessible_api():
    """从可访问的API提取数据"""
    
    print("📊 API数据提取器")
    print("=" * 50)
    print("从已确认可访问的API端点提取数据")
    print("=" * 50)
    
    # 创建会话
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    })
    
    # 可访问的API端点
    api_endpoints = [
        ("文章列表", "https://peacoop.or.th/wp-json/wp/v2/posts"),
        ("页面列表", "https://peacoop.or.th/wp-json/wp/v2/pages"),
        ("分类列表", "https://peacoop.or.th/wp-json/wp/v2/categories"),
        ("标签列表", "https://peacoop.or.th/wp-json/wp/v2/tags"),
        ("媒体文件", "https://peacoop.or.th/wp-json/wp/v2/media"),
        ("评论列表", "https://peacoop.or.th/wp-json/wp/v2/comments"),
        ("用户列表", "https://peacoop.or.th/wp-json/wp/v2/users"),
        ("站点信息", "https://peacoop.or.th/wp-json/wp/v2"),
        ("文章类型", "https://peacoop.or.th/wp-json/wp/v2/types"),
        ("文章状态", "https://peacoop.or.th/wp-json/wp/v2/statuses")
    ]
    
    extracted_data = {
        "target": "https://peacoop.or.th",
        "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "api_data": {},
        "summary": {}
    }
    
    total_items = 0
    
    for name, url in api_endpoints:
        print(f"\n🔍 提取 {name}: {url}")
        
        try:
            # 尝试不同的参数获取更多数据
            params = {
                'per_page': 100,  # 每页最多100项
                'page': 1
            }
            
            response = session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if isinstance(data, list):
                        item_count = len(data)
                        total_items += item_count
                        print(f"   ✅ 成功提取 {item_count} 项")
                        
                        # 保存数据（限制数量避免文件过大）
                        if item_count > 0:
                            extracted_data["api_data"][name] = {
                                "count": item_count,
                                "url": url,
                                "data": data[:20]  # 只保存前20项
                            }
                            
                            # 显示部分数据示例
                            if name == "文章列表":
                                print(f"   📝 文章示例:")
                                for i, post in enumerate(data[:3]):
                                    title = post.get("title", {}).get("rendered", "无标题").strip()
                                    author = post.get("author", "未知")
                                    date = post.get("date", "未知日期")
                                    print(f"      {i+1}. {title[:50]}...")
                                    print(f"         作者ID: {author}, 日期: {date}")
                            
                            elif name == "用户列表":
                                print(f"   👥 用户示例:")
                                for i, user in enumerate(data[:3]):
                                    name = user.get("name", "未知用户")
                                    slug = user.get("slug", "无slug")
                                    print(f"      {i+1}. {name} ({slug})")
                            
                            elif name == "页面列表":
                                print(f"   📄 页面示例:")
                                for i, page in enumerate(data[:3]):
                                    title = page.get("title", {}).get("rendered", "无标题").strip()
                                    print(f"      {i+1}. {title[:50]}...")
                    
                    elif isinstance(data, dict):
                        print(f"   ✅ 成功提取配置信息")
                        extracted_data["api_data"][name] = {
                            "type": "config",
                            "data": data
                        }
                        
                        if name == "站点信息":
                            name_field = data.get("name", "未知站点")
                            description = data.get("description", "无描述")
                            url_field = data.get("url", "")
                            print(f"   🏠 站点信息:")
                            print(f"      名称: {name_field}")
                            print(f"      描述: {description[:100]}...")
                            print(f"      URL: {url_field}")
                    
                except json.JSONDecodeError:
                    print(f"   ❌ JSON解析失败")
                    
            elif response.status_code == 401:
                print(f"   🔒 需要认证")
                
            elif response.status_code == 403:
                print(f"   🚫 访问被禁止")
                
            elif response.status_code == 404:
                print(f"   ❌ 端点不存在")
                
            else:
                print(f"   ❌ 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 访问失败: {str(e)}")
    
    # 生成总结
    extracted_data["summary"] = {
        "total_api_endpoints": len(api_endpoints),
        "successful_extractions": len(extracted_data["api_data"]),
        "total_items_extracted": total_items,
        "data_types": list(extracted_data["api_data"].keys())
    }
    
    # 保存结果
    timestamp = int(time.time())
    result_file = f"api_extracted_data_{timestamp}.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    # 打印总结
    print(f"\n" + "=" * 50)
    print("📊 API数据提取总结")
    print("=" * 50)
    
    summary = extracted_data["summary"]
    print(f"🎯 目标: {extracted_data['target']}")
    print(f"🔗 测试端点: {summary['total_api_endpoints']}个")
    print(f"✅ 成功提取: {summary['successful_extractions']}个")
    print(f"📊 数据总量: {summary['total_items_extracted']}项")
    print(f"📋 数据类型: {', '.join(summary['data_types'])}")
    print(f"📄 完整数据: {result_file}")
    
    # 重要数据展示
    if "文章列表" in extracted_data["api_data"]:
        posts = extracted_data["api_data"]["文章列表"]["data"]
        print(f"\n📝 文章详情:")
        for i, post in enumerate(posts[:5]):
            title = post.get("title", {}).get("rendered", "无标题").strip()
            content = post.get("content", {}).get("rendered", "")
            excerpt = post.get("excerpt", {}).get("rendered", "")
            print(f"  {i+1}. {title}")
            if excerpt:
                print(f"     摘要: {excerpt[:100]}...")
            print(f"     内容长度: {len(content)} 字符")
    
    print(f"\n⚠️ 重要说明:")
    print("这些是从目标网站API实际提取的真实数据")
    print("包含文章内容、用户信息、站点配置等敏感信息")
    print("请负责任地使用，仅用于授权的安全测试")
    
    return extracted_data

if __name__ == "__main__":
    result = extract_from_accessible_api()
    
    print(f"\n🎉 数据提取完成!")
    print(f"成功从真实网站提取了实际的API数据")