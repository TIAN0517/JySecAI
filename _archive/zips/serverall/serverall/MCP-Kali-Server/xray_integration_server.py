#!/usr/bin/env python3
"""
Xray MCP集成服务器
与Burp Suite协同工作的安全扫描系统
"""

import os
import sys
import json
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import uuid

class XrayMCPServer:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)

        # Xray配置
        self.xray_path = os.environ.get('XRAY_PATH', './tools/xray')
        self.xray_config = os.environ.get('XRAY_CONFIG', './config/xray_config.yaml')
        self.output_dir = os.environ.get('XRAY_OUTPUT_DIR', './xray_results')

        # 确保目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.xray_config), exist_ok=True)
        os.makedirs('./tools', exist_ok=True)

        # 数据库初始化
        self.init_database()

        # 配置路由
        self.setup_routes()

    def init_database(self):
        """初始化Xray扫描数据库"""
        conn = sqlite3.connect('xray_scans.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                target TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                start_time TEXT,
                end_time TEXT,
                result_file TEXT,
                vuln_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id TEXT PRIMARY KEY,
                scan_id TEXT,
                vuln_type TEXT,
                severity TEXT,
                target TEXT,
                detail TEXT,
                request_data TEXT,
                response_data TEXT,
                poc TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scan_id) REFERENCES scans (id)
            )
        ''')

        conn.commit()
        conn.close()

    def setup_routes(self):
        """设置API路由"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy", "service": "xray-mcp-server", "version": "1.0.0"})

        @self.app.route('/api/xray/info', methods=['GET'])
        def get_xray_info():
            """获取Xray信息"""
            try:
                if os.path.exists(self.xray_path):
                    result = subprocess.run([self.xray_path, 'version'],
                                          capture_output=True, text=True, timeout=10)
                    return jsonify({
                        "status": "installed",
                        "version": result.stdout.strip(),
                        "path": self.xray_path
                    })
                else:
                    return jsonify({
                        "status": "not_installed",
                        "message": "Xray not found at specified path",
                        "path": self.xray_path
                    }), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/xray/config', methods=['GET', 'POST'])
        def manage_config():
            """管理Xray配置"""
            if request.method == 'GET':
                if os.path.exists(self.xray_config):
                    with open(self.xray_config, 'r', encoding='utf-8') as f:
                        config_content = f.read()
                    return jsonify({"config": config_content})
                else:
                    # 返回默认配置
                    default_config = self.get_default_config()
                    return jsonify({"config": default_config})

            elif request.method == 'POST':
                config_data = request.json.get('config')
                if config_data:
                    with open(self.xray_config, 'w', encoding='utf-8') as f:
                        f.write(config_data)
                    return jsonify({"status": "config_saved"})
                return jsonify({"error": "No config provided"}), 400

        @self.app.route('/api/xray/scan', methods=['POST'])
        def start_scan():
            """启动Xray扫描"""
            data = request.json
            target = data.get('target')
            scan_type = data.get('scan_type', 'web')
            options = data.get('options', {})

            if not target:
                return jsonify({"error": "Target is required"}), 400

            # 生成扫描ID
            scan_id = str(uuid.uuid4())

            # 创建数据库记录
            conn = sqlite3.connect('xray_scans.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scans (id, target, scan_type, status, start_time)
                VALUES (?, ?, ?, 'running', ?)
            ''', (scan_id, target, scan_type, datetime.now().isoformat()))
            conn.commit()
            conn.close()

            # 异步启动扫描
            thread = threading.Thread(target=self.run_xray_scan,
                                    args=(scan_id, target, scan_type, options))
            thread.daemon = True
            thread.start()

            return jsonify({
                "scan_id": scan_id,
                "status": "started",
                "target": target,
                "scan_type": scan_type
            })

        @self.app.route('/api/xray/scan/<scan_id>/status', methods=['GET'])
        def get_scan_status(scan_id):
            """获取扫描状态"""
            conn = sqlite3.connect('xray_scans.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, target, scan_type, status, start_time, end_time,
                       result_file, vuln_count
                FROM scans WHERE id = ?
            ''', (scan_id,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return jsonify({
                    "scan_id": result[0],
                    "target": result[1],
                    "scan_type": result[2],
                    "status": result[3],
                    "start_time": result[4],
                    "end_time": result[5],
                    "result_file": result[6],
                    "vuln_count": result[7]
                })
            else:
                return jsonify({"error": "Scan not found"}), 404

        @self.app.route('/api/xray/scan/<scan_id>/results', methods=['GET'])
        def get_scan_results(scan_id):
            """获取扫描结果"""
            conn = sqlite3.connect('xray_scans.db')
            cursor = conn.cursor()

            # 获取漏洞列表
            cursor.execute('''
                SELECT id, vuln_type, severity, target, detail, poc
                FROM vulnerabilities WHERE scan_id = ?
                ORDER BY severity DESC
            ''', (scan_id,))

            vulns = cursor.fetchall()
            conn.close()

            vulnerabilities = []
            for vuln in vulns:
                vulnerabilities.append({
                    "id": vuln[0],
                    "type": vuln[1],
                    "severity": vuln[2],
                    "target": vuln[3],
                    "detail": json.loads(vuln[4]) if vuln[4] else {},
                    "poc": vuln[5]
                })

            return jsonify({
                "scan_id": scan_id,
                "vulnerabilities": vulnerabilities,
                "total_count": len(vulnerabilities)
            })

        @self.app.route('/api/xray/burp/integration', methods=['POST'])
        def burp_integration():
            """Burp Suite集成接口"""
            data = request.json

            # 提取Burp请求
            burp_request = data.get('request')
            target_url = data.get('target_url')
            headers = data.get('headers', {})

            if not burp_request or not target_url:
                return jsonify({"error": "Request and target_url are required"}), 400

            # 生成Burp到Xray的测试用例
            test_cases = self.generate_burp_test_cases(target_url, burp_request, headers)

            return jsonify({
                "status": "test_cases_generated",
                "target_url": target_url,
                "test_cases": test_cases
            })

        @self.app.route('/api/xray/export/<scan_id>', methods=['GET'])
        def export_results(scan_id):
            """导出扫描结果"""
            format_type = request.args.get('format', 'json')

            conn = sqlite3.connect('xray_scans.db')
            cursor = conn.cursor()

            # 获取扫描信息
            cursor.execute('''
                SELECT target, scan_type, start_time, end_time, vuln_count
                FROM scans WHERE id = ?
            ''', (scan_id,))

            scan_info = cursor.fetchone()
            if not scan_info:
                return jsonify({"error": "Scan not found"}), 404

            # 获取漏洞详情
            cursor.execute('''
                SELECT vuln_type, severity, target, detail, request_data,
                       response_data, poc
                FROM vulnerabilities WHERE scan_id = ?
                ORDER BY severity DESC
            ''', (scan_id,))

            vulns = cursor.fetchall()
            conn.close()

            if format_type == 'html':
                html_report = self.generate_html_report(scan_id, scan_info, vulns)
                return html_report, 200, {'Content-Type': 'text/html; charset=utf-8'}
            else:
                return self.generate_json_report(scan_id, scan_info, vulns)

    def get_default_config(self):
        """获取默认Xray配置"""
        return """
# Xray 默认配置文件
name: xray-scan

# 代理设置
proxy:
  http: ""
  https: ""
  socks5: ""

# 浏览器设置
browser:
  phontomjs: ""

# 插件配置
plugins:
  xss:
    enabled: true
  sql:
    enabled: true
  cmd-injection:
    enabled: true
  xxe:
    enabled: true
  path-traversal:
    enabled: true
  brute-force:
    enabled: true
  fastjson:
    enabled: true
  ssrf:
    enabled: true
  redirect:
    enabled: true
  xstream:
    enabled: true
  weak-password:
    enabled: true

# 输出配置
output:
  html_report: ""
  json_report: ""
  markdown_report: ""

# 其他设置
max_concurrency: 50
max_redirect: 5
max_depth: 5
timeout: 30
"""

    def run_xray_scan(self, scan_id, target, scan_type, options):
        """运行Xray扫描"""
        try:
            # 准备输出文件
            result_file = os.path.join(self.output_dir, f"{scan_id}.json")

            # 构建Xray命令
            cmd = [
                self.xray_path,
                'webscan',
                '--url', target,
                '--json-output', result_file,
                '--no-headless'
            ]

            # 添加扫描选项
            if options.get('basic_crawler', False):
                cmd.extend(['--basic-crawler'])

            if options.get('plugins'):
                cmd.extend(['--plugins', ','.join(options['plugins'])])

            # 运行扫描
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            # 更新数据库
            end_time = datetime.now().isoformat()
            vuln_count = 0

            if os.path.exists(result_file):
                vuln_count = self.parse_and_save_results(scan_id, result_file)

            conn = sqlite3.connect('xray_scans.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scans SET status = 'completed', end_time = ?,
                              result_file = ?, vuln_count = ?
                WHERE id = ?
            ''', (end_time, result_file, vuln_count, scan_id))
            conn.commit()
            conn.close()

        except Exception as e:
            # 更新错误状态
            conn = sqlite3.connect('xray_scans.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scans SET status = 'failed', end_time = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), scan_id))
            conn.commit()
            conn.close()
            print(f"Scan error: {e}")

    def parse_and_save_results(self, scan_id, result_file):
        """解析并保存Xray结果"""
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                results = json.load(f)

            conn = sqlite3.connect('xray_scans.db')
            cursor = conn.cursor()

            vuln_count = 0
            for item in results:
                vuln_id = str(uuid.uuid4())

                cursor.execute('''
                    INSERT INTO vulnerabilities
                    (id, scan_id, vuln_type, severity, target, detail,
                     request_data, response_data, poc)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    vuln_id,
                    scan_id,
                    item.get('plugin', ''),
                    item.get('detail', {}).get('severity', ''),
                    item.get('target', {}).get('url', ''),
                    json.dumps(item.get('detail', {})),
                    json.dumps(item.get('detail', {}).get('request', {})),
                    json.dumps(item.get('detail', {}).get('response', {})),
                    item.get('detail', {}).get('poc', '')
                ))
                vuln_count += 1

            conn.commit()
            conn.close()
            return vuln_count

        except Exception as e:
            print(f"Error parsing results: {e}")
            return 0

    def generate_burp_test_cases(self, target_url, burp_request, headers):
        """生成Burp到Xray的测试用例"""
        test_cases = []

        # XSS测试用例
        test_cases.append({
            "type": "xss",
            "payload": "<script>alert('xss')</script>",
            "description": "跨站脚本攻击测试",
            "target_param": "search"
        })

        # SQL注入测试用例
        test_cases.append({
            "type": "sql-injection",
            "payload": "' OR '1'='1",
            "description": "SQL注入测试",
            "target_param": "id"
        })

        # 路径遍历测试用例
        test_cases.append({
            "type": "path-traversal",
            "payload": "../../../etc/passwd",
            "description": "路径遍历测试",
            "target_param": "file"
        })

        return test_cases

    def generate_html_report(self, scan_id, scan_info, vulns):
        """生成HTML报告"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Xray扫描报告 - {scan_id}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .vulnerability {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .high {{ border-left: 5px solid #d32f2f; }}
                .medium {{ border-left: 5px solid #f57c00; }}
                .low {{ border-left: 5px solid #388e3c; }}
                .detail {{ background: #f9f9f9; padding: 10px; margin-top: 10px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Xray安全扫描报告</h1>
                <p><strong>扫描ID:</strong> {scan_id}</p>
                <p><strong>目标:</strong> {scan_info[0]}</p>
                <p><strong>扫描类型:</strong> {scan_info[1]}</p>
                <p><strong>开始时间:</strong> {scan_info[2]}</p>
                <p><strong>结束时间:</strong> {scan_info[3]}</p>
                <p><strong>发现漏洞:</strong> {scan_info[4]} 个</p>
            </div>

            <h2>漏洞详情</h2>
        """

        for vuln in vulns:
            severity_class = vuln[1].lower()
            html += f"""
            <div class="vulnerability {severity_class}">
                <h3>{vuln[0]} - {vuln[1]}</h3>
                <p><strong>目标:</strong> {vuln[2]}</p>
                <div class="detail">
                    <pre>{json.dumps(json.loads(vuln[3]) if vuln[3] else {}, indent=2, ensure_ascii=False)}</pre>
                </div>
            </div>
            """

        html += """
        </body>
        </html>
        """

        return html

    def generate_json_report(self, scan_id, scan_info, vulns):
        """生成JSON报告"""
        report = {
            "scan_id": scan_id,
            "scan_info": {
                "target": scan_info[0],
                "scan_type": scan_info[1],
                "start_time": scan_info[2],
                "end_time": scan_info[3],
                "vuln_count": scan_info[4]
            },
            "vulnerabilities": []
        }

        for vuln in vulns:
            report["vulnerabilities"].append({
                "type": vuln[0],
                "severity": vuln[1],
                "target": vuln[2],
                "detail": json.loads(vuln[3]) if vuln[3] else {},
                "request": json.loads(vuln[4]) if vuln[4] else {},
                "response": json.loads(vuln[5]) if vuln[5] else {},
                "poc": vuln[6]
            })

        return jsonify(report)

    def run(self, host='127.0.0.1', port=5002):
        """启动服务器"""
        print(f"Xray MCP Server starting on {host}:{port}")
        self.app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Xray MCP Integration Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=5002, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Debug mode')

    args = parser.parse_args()

    server = XrayMCPServer()
    server.run(host=args.host, port=args.port)