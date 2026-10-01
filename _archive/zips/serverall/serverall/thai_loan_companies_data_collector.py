#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国贷款公司公开数据收集器
合法合规的网络爬虫工具，仅收集公开信息
"""

import requests
import json
import time
import random
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import csv
from typing import List, Dict, Any
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThaiLoanDataCollector:
    """泰国贷款公司公开数据收集器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # 泰国主要贷款公司网站（公开信息）
        self.loan_companies = [
            {
                "name": "MoneyCat Thailand",
                "website": "https://www.moneycat.co.th",
                "type": "小额借贷",
                "license_required": True
            },
            {
                "name": "AEON Thana Sinsap (Thailand)",
                "website": "https://www.aeon.co.th",
                "type": "信用卡/消费贷款",
                "license_required": True
            },
            {
                "name": "KTC Credit Card",
                "website": "https://www.ktc.co.th",
                "type": "信用卡/现金贷款",
                "license_required": True
            },
            {
                "name": "Ngern Tid Lor",
                "website": "https://www.ngerntidlor.com",
                "type": "汽车抵押贷款",
                "license_required": True
            },
            {
                "name": "Money Station",
                "website": "https://www.moneystation.co.th",
                "type": "小额借贷",
                "license_required": True
            },
            {
                "name": "Jaymart Financial",
                "website": "https://www.jaymart.co.th",
                "type": "消费金融",
                "license_required": True
            },
            {
                "name": "Tisco Bank",
                "website": "https://www.tisco.co.th",
                "type": "银行/汽车贷款",
                "license_required": True
            },
            {
                "name": "Srisawad",
                "website": "https://www.srisawad.co.th",
                "type": "抵押贷款",
                "license_required": True
            },
            {
                "name": "G Cash",
                "website": "https://www.gcash.co.th",
                "type": "P2P借贷",
                "license_required": True
            },
            {
                "name": "Lending Hub",
                "website": "https://www.lendinghub.co.th",
                "type": "P2P借贷",
                "license_required": True
            }
        ]

        # 泰国金融监管机构网站（公开数据）
        self.regulatory_sources = [
            {
                "name": "Bank of Thailand",
                "website": "https://www.bot.or.th",
                "type": "中央银行监管数据"
            },
            {
                "name": "SEC Thailand",
                "website": "https://www.sec.or.th",
                "type": "证券监管数据"
            },
            {
                "name": "Ministry of Finance",
                "website": "https://www.mof.go.th",
                "type": "财政部公开数据"
            }
        ]

        self.collected_data = []

    def random_delay(self, min_seconds=1, max_seconds=3):
        """随机延迟，避免过于频繁的请求"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def safe_request(self, url: str, timeout: int = 10) -> requests.Response:
        """安全的HTTP请求"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败 {url}: {e}")
            return None

    def extract_company_info(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """提取公司基本信息"""
        website = company["website"]
        logger.info(f"正在收集 {company['name']} 的公开信息...")

        company_data = {
            "公司名称": company["name"],
            "网站": website,
            "业务类型": company["type"],
            "收集时间": datetime.now().isoformat(),
            "状态": "处理中"
        }

        try:
            response = self.safe_request(website)
            if response is None:
                company_data["状态"] = "无法访问"
                return company_data

            soup = BeautifulSoup(response.content, 'html.parser')

            # 提取基本信息
            company_data.update(self.extract_contact_info(soup))
            company_data.update(self.extract_business_info(soup))
            company_data.update(self.extract_legal_info(soup))
            company_data["状态"] = "成功收集"

        except Exception as e:
            logger.error(f"提取 {company['name']} 信息失败: {e}")
            company_data["状态"] = "提取失败"
            company_data["错误"] = str(e)

        return company_data

    def extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取联系信息"""
        contact_info = {}

        # 查找电话号码
        phone_patterns = [
            r'0[2-9]\d{7}',  # 泰国座机格式
            r'0[689]\d{8}',  # 泰国手机格式
            r'\+66[2-9]\d{7}',
            r'\+66[689]\d{8}'
        ]

        text_content = soup.get_text()
        for pattern in phone_patterns:
            phones = re.findall(pattern, text_content)
            if phones:
                contact_info["联系电话"] = phones[0]
                break

        # 查找邮箱
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        if emails:
            contact_info["联系邮箱"] = emails[0]

        # 查找地址关键词
        address_keywords = ['Bangkok', 'Thailand', 'Road', 'Soi', 'ถนน', 'กรุงเทพ', 'ประเทศไทย']
        for keyword in address_keywords:
            if keyword in text_content:
                # 提取包含关键词的句子作为地址
                sentences = text_content.split('.')
                for sentence in sentences:
                    if keyword in sentence:
                        contact_info["公司地址"] = sentence.strip()
                        break
                break

        return contact_info

    def extract_business_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取业务信息"""
        business_info = {}

        # 查找贷款产品信息
        loan_keywords = ['loan', 'personal loan', 'cash loan', 'เงินกู้', 'สินเชื่อ', 'interest rate', 'ดอกเบี้ย']
        text_content = soup.get_text().lower()

        for keyword in loan_keywords:
            if keyword in text_content:
                business_info["主要业务"] = "贷款服务"
                break

        # 查找利率信息
        interest_patterns = [
            r'(\d+\.?\d*)%',
            r'(\d+\.?\d*)\s*percent',
            r'ดอกเบี้ย\s*(\d+\.?\d*)'
        ]

        for pattern in interest_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                business_info["利率信息"] = f"{matches[0]}%"
                break

        return business_info

    def extract_legal_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取法律/许可信息"""
        legal_info = {}

        # 查找许可证相关关键词
        license_keywords = ['license', 'permit', 'registered', 'กฎหมาย', 'ใบอนุญาต', 'จดทะเบียน']
        text_content = soup.get_text()

        for keyword in license_keywords:
            if keyword in text_content.lower():
                legal_info["法律状态"] = "需要核实许可证"
                break

        return legal_info

    def search_business_registration(self, company_name: str) -> Dict[str, str]:
        """搜索企业工商注册信息（模拟）"""
        # 注意：这里只是示例，实际应该使用合法的企业信息查询API
        reg_info = {
            "企业注册查询": "需要通过泰国商业发展厅官网查询",
            "查询网址": "https://www.dbd.go.th",
            "注册状态": "需要人工核实"
        }
        return reg_info

    def collect_regulatory_data(self) -> List[Dict[str, Any]]:
        """收集监管机构公开数据"""
        regulatory_data = []

        for source in self.regulatory_sources:
            logger.info(f"正在检查 {source['name']} 的公开数据...")

            try:
                response = self.safe_request(source["website"])
                if response is None:
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')

                # 查找公开报告或数据下载链接
                data_info = {
                    "监管机构": source["name"],
                    "网站": source["website"],
                    "数据类型": source["type"],
                    "检查时间": datetime.now().isoformat(),
                    "状态": "已检查"
                }

                regulatory_data.append(data_info)
                self.random_delay(2, 4)  # 避免过于频繁访问

            except Exception as e:
                logger.error(f"检查 {source['name']} 失败: {e}")

        return regulatory_data

    def save_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """保存数据到CSV文件"""
        if not data:
            logger.warning("没有数据可保存")
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                if data:
                    fieldnames = set()
                    for item in data:
                        fieldnames.update(item.keys())

                    writer = csv.DictWriter(csvfile, fieldnames=list(fieldnames))
                    writer.writeheader()
                    writer.writerows(data)

            logger.info(f"数据已保存到 {filename}")

        except Exception as e:
            logger.error(f"保存CSV文件失败: {e}")

    def save_to_json(self, data: List[Dict[str, Any]], filename: str):
        """保存数据到JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            logger.info(f"数据已保存到 {filename}")

        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")

    def generate_summary_report(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成汇总报告"""
        total_companies = len([d for d in data if "公司名称" in d])
        successful_collections = len([d for d in data if d.get("状态") == "成功收集"])

        report = {
            "收集时间": datetime.now().isoformat(),
            "目标公司总数": total_companies,
            "成功收集数": successful_collections,
            "成功率": f"{(successful_collections/total_companies*100):.1f}%" if total_companies > 0 else "0%",
            "数据类型": "公开信息",
            "合规声明": "本工具仅收集公开信息，遵守相关法律法规"
        }

        return report

    def run_collection(self):
        """执行数据收集"""
        logger.info("开始收集泰国贷款公司公开数据...")
        logger.info("⚠️ 声明：本工具仅收集公开信息，遵守泰国法律法规")

        # 收集公司信息
        for company in self.loan_companies:
            company_data = self.extract_company_info(company)
            self.collected_data.append(company_data)
            self.random_delay(1, 3)  # 礼貌性延迟

        # 收集监管数据
        regulatory_data = self.collect_regulatory_data()
        self.collected_data.extend(regulatory_data)

        # 生成报告
        summary = self.generate_summary_report(self.collected_data)

        # 保存数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.save_to_json(self.collected_data, f"thai_loan_companies_data_{timestamp}.json")
        self.save_to_csv(self.collected_data, f"thai_loan_companies_data_{timestamp}.csv")
        self.save_to_json(summary, f"collection_summary_{timestamp}.json")

        logger.info("数据收集完成！")
        logger.info(f"总计收集: {len(self.collected_data)} 条记录")
        logger.info(f"成功率: {summary['成功率']}")

        return self.collected_data

def main():
    """主函数"""
    print("=" * 60)
    print("泰国贷款公司公开数据收集器")
    print("=" * 60)
    print("⚠️ 重要声明：")
    print("1. 本工具仅收集公开可用信息")
    print("2. 遵守泰国法律法规和网络礼仪")
    print("3. 不收集任何私人或敏感数据")
    print("4. 仅用于合法的市场研究和分析")
    print("=" * 60)

    collector = ThaiLoanDataCollector()

    try:
        data = collector.run_collection()
        print("\n✅ 数据收集完成！")
        print(f"📊 收集到 {len(data)} 条记录")
        print("📁 数据已保存到本地文件")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断了数据收集过程")
    except Exception as e:
        print(f"\n❌ 数据收集过程中出现错误: {e}")

    print("\n📋 后续建议：")
    print("1. 检查生成的CSV和JSON文件")
    print("2. 手动核实重要信息")
    print("3. 通过官方渠道验证企业注册信息")
    print("4. 遵守数据使用相关法律法规")

if __name__ == "__main__":
    main()