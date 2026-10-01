#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loan Data Extractor - 贷款数据提取器
专门提取贷款相关的真实数据
"""

import requests
import json
import time
import re
from urllib.parse import urljoin

class LoanDataExtractor:
    """贷款数据提取器"""
    
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,th;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        self.loan_data = {}
        
    def extract_loan_related_posts(self) -> list:
        """提取贷款相关文章"""
        print("🔍 搜索贷款相关文章...")
        
        loan_posts = []
        
        try:
            # 获取所有文章
            api_url = f"{self.target_url}/wp-json/wp/v2/posts"
            params = {'per_page': 100, 'page': 1}
            
            response = self.session.get(api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                posts = response.json()
                
                # 贷款相关关键词（泰语和英语）
                loan_keywords = [
                    'เงินกู้', 'สินเชื่อ', 'กู้', 'ยืม', 'loan', 'credit', 'borrow',
                    'ดอกเบี้ย', 'interest', 'ผ่อน', 'installment', 'สหกรณ์', 'cooperative',
                    'ฝาก', 'deposit', 'ออม', 'saving', 'กองทุน', 'fund',
                    'ค้ำประกัน', 'collateral', 'หลักประกัน', 'guarantee'
                ]
                
                for post in posts:
                    title = post.get("title", {}).get("rendered", "").lower()
                    content = post.get("content", {}).get("rendered", "").lower()
                    excerpt = post.get("excerpt", {}).get("rendered", "").lower()
                    
                    # 检查是否包含贷款关键词
                    combined_text = title + " " + content + " " + excerpt
                    is_loan_related = any(keyword in combined_text for keyword in loan_keywords)
                    
                    if is_loan_related:
                        loan_post = {
                            "id": post.get("id"),
                            "title": post.get("title", {}).get("rendered", "").strip(),
                            "content": post.get("content", {}).get("rendered", "").strip(),
                            "excerpt": post.get("excerpt", {}).get("rendered", "").strip(),
                            "date": post.get("date", ""),
                            "author": post.get("author", ""),
                            "categories": post.get("categories", []),
                            "tags": post.get("tags", []),
                            "link": post.get("link", ""),
                            "relevance_score": self._calculate_relevance_score(combined_text, loan_keywords)
                        }
                        loan_posts.append(loan_post)
                
                # 按相关性排序
                loan_posts.sort(key=lambda x: x["relevance_score"], reverse=True)
                print(f"   ✅ 找到贷款相关文章: {len(loan_posts)}篇")
                
        except Exception as e:
            print(f"   ❌ 提取文章失败: {str(e)}")
        
        return loan_posts
    
    def _calculate_relevance_score(self, text: str, keywords: list) -> float:
        """计算相关性得分"""
        score = 0
        for keyword in keywords:
            count = text.count(keyword)
            if keyword in ['เงินกู้', 'สินเชื่อ', 'loan', 'credit']:
                score += count * 3  # 高权重关键词
            elif keyword in ['ดอกเบี้ย', 'interest', 'สหกรณ์', 'cooperative']:
                score += count * 2  # 中权重关键词
            else:
                score += count  # 普通关键词
        
        return score
    
    def extract_loan_amounts_and_rates(self, posts: list) -> dict:
        """提取贷款金额和利率信息"""
        print("💰 提取贷款金额和利率信息...")
        
        loan_info = {
            "amounts_found": [],
            "interest_rates": [],
            "loan_terms": [],
            "collateral_info": [],
            "application_deadlines": []
        }
        
        # 金额模式（泰铢和数字）
        amount_patterns = [
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*บาท',  # 泰铢
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*THB',  # THB
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s* Baths?',  # Baths
            r'เงินกู้.*?(\d+(?:,\d{3})*(?:\.\d+)?)',  # 贷款金额
            r'วงเงิน.*?(\d+(?:,\d{3})*(?:\.\d+)?)',  # 资金数额
        ]
        
        # 利率模式
        rate_patterns = [
            r'(\d+(?:\.\d+)?)\s*%',
            r'ดอกเบี้ย.*?(\d+(?:\.\d+)?)\s*%',
            r'อัตราดอกเบี้ย.*?(\d+(?:\.\d+)?)',
            r'interest.*?(\d+(?:\.\d+)?)\s*%',
        ]
        
        # 贷款期限模式
        term_patterns = [
            r'(\d+)\s*ปี',  # 年
            r'(\d+)\s*เดือน',  # 月
            r'(\d+)\s*งวน',  # 天
            r'(\d+)\s*year',
            r'(\d+)\s*month',
            r'ผ่อน.*?(\d+)\s*งวน',  # 分期天数
        ]
        
        for post in posts:
            content = post["title"] + " " + post["content"]
            
            # 提取金额
            for pattern in amount_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for amount in matches:
                    clean_amount = amount.replace(',', '')
                    try:
                        numeric_amount = float(clean_amount)
                        if 1000 <= numeric_amount <= 10000000:  # 合理范围
                            loan_info["amounts_found"].append({
                                "amount": numeric_amount,
                                "currency": "THB",
                                "source_post_id": post["id"],
                                "source_title": post["title"][:100]
                            })
                    except:
                        pass
            
            # 提取利率
            for pattern in rate_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for rate in matches:
                    try:
                        numeric_rate = float(rate)
                        if 0 <= numeric_rate <= 30:  # 合理利率范围
                            loan_info["interest_rates"].append({
                                "rate": numeric_rate,
                                "unit": "%",
                                "source_post_id": post["id"],
                                "source_title": post["title"][:100]
                            })
                    except:
                        pass
            
            # 提取贷款期限
            for pattern in term_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for term in matches:
                    try:
                        numeric_term = int(term)
                        if 1 <= numeric_term <= 360:  # 合理期限范围
                            loan_info["loan_terms"].append({
                                "term": numeric_term,
                                "source_post_id": post["id"],
                                "source_title": post["title"][:100]
                            })
                    except:
                        pass
        
        # 去重和统计
        seen_amounts = set()
        unique_amounts = []
        for item in loan_info["amounts_found"]:
            key = (item["amount"], item["currency"], item["source_post_id"])
            if key not in seen_amounts:
                seen_amounts.add(key)
                unique_amounts.append(item)
        loan_info["amounts_found"] = unique_amounts
        
        seen_rates = set()
        unique_rates = []
        for item in loan_info["interest_rates"]:
            key = (item["rate"], item["unit"], item["source_post_id"])
            if key not in seen_rates:
                seen_rates.add(key)
                unique_rates.append(item)
        loan_info["interest_rates"] = unique_rates
        
        seen_terms = set()
        unique_terms = []
        for item in loan_info["loan_terms"]:
            key = (item["term"], item["source_post_id"])
            if key not in seen_terms:
                seen_terms.add(key)
                unique_terms.append(item)
        loan_info["loan_terms"] = unique_terms
        
        print(f"   💰 发现金额信息: {len(loan_info['amounts_found'])}条")
        print(f"   📊 发现利率信息: {len(loan_info['interest_rates'])}条")
        print(f"   📅 发现期限信息: {len(loan_info['loan_terms'])}条")
        
        return loan_info
    
    def extract_member_information(self, posts: list) -> dict:
        """提取成员信息"""
        print("👥 提取成员相关信息...")
        
        member_info = {
            "member_announcements": [],
            "member_qualifications": [],
            "application_requirements": [],
            "contact_information": [],
            "meeting_schedules": []
        }
        
        for post in posts:
            content = post["title"] + " " + post["content"]
            
            # 成员公告模式
            if any(keyword in content for keyword in ['สมาชิก', 'member', 'บุตรหลาน', 'รายชื่อ']):
                member_info["member_announcements"].append({
                    "post_id": post["id"],
                    "title": post["title"],
                    "date": post["date"],
                    "content_preview": post["excerpt"][:200] if post["excerpt"] else post["content"][:200]
                })
            
            # 申请条件模式
            if any(keyword in content for keyword in ['คุณสมบัติ', 'qualification', 'เงื่อนไข', 'requirement']):
                member_info["application_requirements"].append({
                    "post_id": post["id"],
                    "title": post["title"],
                    "requirements": self._extract_requirements_from_content(post["content"])
                })
            
            # 联系信息模式
            contact_patterns = [
                r'(\d{3}-\d{3}-\d{4})',  # 电话格式
                r'(\d{10})',  # 10位数字
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # 邮箱
            ]
            
            for pattern in contact_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    member_info["contact_information"].append({
                        "contact": match,
                        "source_post_id": post["id"],
                        "source_title": post["title"][:100]
                    })
        
        print(f"   👤 成员公告: {len(member_info['member_announcements'])}条")
        print(f"   📋 申请条件: {len(member_info['application_requirements'])}条")
        print(f"   📞 联系信息: {len(member_info['contact_information'])}条")
        
        return member_info
    
    def _extract_requirements_from_content(self, content: str) -> list:
        """从内容中提取申请条件"""
        requirements = []
        
        # 查找列表项
        list_patterns = [
            r'<li[^>]*>(.*?)</li>',
            r'(\d+\.\s*.*?)(?=\d+\.|$)',
            r'[-•]\s*(.*?)(?=[-•]|$)'
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                clean_match = re.sub(r'<[^>]+>', '', match).strip()
                if len(clean_match) > 10 and len(clean_match) < 200:
                    if any(keyword in clean_match.lower() for keyword in ['ต้อง', 'ควร', 'should', 'must', 'require']):
                        requirements.append(clean_match)
        
        return requirements[:10]  # 限制数量
    
    def extract_comprehensive_loan_data(self) -> dict:
        """提取综合贷款数据"""
        print(f"🎯 综合贷款数据提取: {self.target_url}")
        print("=" * 60)
        
        # 1. 提取贷款相关文章
        loan_posts = self.extract_loan_related_posts()
        
        if not loan_posts:
            return {"error": "未找到贷款相关数据"}
        
        # 2. 提取金额和利率信息
        financial_info = self.extract_loan_amounts_and_rates(loan_posts)
        
        # 3. 提取成员信息
        member_info = self.extract_member_information(loan_posts)
        
        # 4. 构造综合结果
        comprehensive_data = {
            "target": self.target_url,
            "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "loan_posts_count": len(loan_posts),
            "loan_posts": loan_posts[:20],  # 最多保存20篇
            "financial_information": financial_info,
            "member_information": member_info,
            "statistics": {
                "total_amounts": len(financial_info["amounts_found"]),
                "total_rates": len(financial_info["interest_rates"]),
                "total_terms": len(financial_info["loan_terms"]),
                "member_announcements": len(member_info["member_announcements"]),
                "application_requirements": len(member_info["application_requirements"])
            }
        }
        
        return comprehensive_data

def main():
    """主函数"""
    target = "https://peacoop.or.th"
    
    print("💰 贷款数据提取器")
    print("=" * 60)
    print(f"目标: {target}")
    print("专门提取贷款相关的真实数据")
    print("=" * 60)
    
    extractor = LoanDataExtractor(target)
    result = extractor.extract_comprehensive_loan_data()
    
    if "error" in result:
        print(f"\n❌ 提取失败: {result['error']}")
        return
    
    # 保存结果
    timestamp = int(time.time())
    result_file = f"loan_data_{timestamp}.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # 打印结果
    print("\n" + "=" * 60)
    print("💰 贷款数据提取结果")
    print("=" * 60)
    
    stats = result["statistics"]
    print(f"📊 贷款相关文章: {result['loan_posts_count']}篇")
    print(f"💰 金额信息: {stats['total_amounts']}条")
    print(f"📈 利率信息: {stats['total_rates']}条")
    print(f"📅 期限信息: {stats['total_terms']}条")
    print(f"👤 成员公告: {stats['member_announcements']}条")
    print(f"📋 申请条件: {stats['application_requirements']}条")
    
    # 显示金额信息
    if result["financial_information"]["amounts_found"]:
        print(f"\n💰 贷款金额示例:")
        for i, amount_info in enumerate(result["financial_information"]["amounts_found"][:5]):
            print(f"  {i+1}. {amount_info['amount']:,.0f} THB")
            print(f"     来源: {amount_info['source_title'][:50]}...")
    
    # 显示利率信息
    if result["financial_information"]["interest_rates"]:
        print(f"\n📈 利率信息示例:")
        for i, rate_info in enumerate(result["financial_information"]["interest_rates"][:5]):
            print(f"  {i+1}. {rate_info['rate']}%")
            print(f"     来源: {rate_info['source_title'][:50]}...")
    
    # 显示成员公告
    if result["member_information"]["member_announcements"]:
        print(f"\n👤 成员公告示例:")
        for i, announcement in enumerate(result["member_information"]["member_announcements"][:3]):
            print(f"  {i+1}. {announcement['title']}")
            print(f"     日期: {announcement['date']}")
            print(f"     预览: {announcement['content_preview'][:100]}...")
    
    # 显示申请条件
    if result["member_information"]["application_requirements"]:
        print(f"\n📋 申请条件示例:")
        for i, req in enumerate(result["member_information"]["application_requirements"][:3]):
            print(f"  {i+1}. {req['title'][:50]}...")
            for j, requirement in enumerate(req['requirements'][:3]):
                print(f"     • {requirement}")
    
    print(f"\n📄 完整贷款数据已保存到: {result_file}")
    print("=" * 60)
    
    print(f"\n⚠️ 重要说明:")
    print("这些是从目标网站实际提取的真实贷款相关数据")
    print("包含贷款金额、利率、申请条件、成员信息等敏感内容")
    print("请负责任地使用，仅用于授权的安全测试")

if __name__ == "__main__":
    main()
