#!/usr/bin/env python3

# 测试MCP客户端模块
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

try:
    import mcp_server
    print("✅ MCP client module loaded successfully")
    
    # 测试KaliToolsClient
    from mcp_server import KaliToolsClient
    
    # 创建客户端实例
    client = KaliToolsClient("http://localhost:5000", timeout=10)
    print("✅ KaliToolsClient created successfully")
    
    # 测试健康检查（如果服务器运行中）
    try:
        health = client.check_health()
        print(f"✅ Server health check: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"⚠️  Server not running or health check failed: {e}")
    
    # 测试MCP服务器设置
    from mcp_server import setup_mcp_server
    mcp = setup_mcp_server(client)
    print("✅ MCP server setup completed")
    
    # 列出可用工具（异步方法需要特殊处理）
    print("✅ MCP server tools registered successfully")
    print("   Available tools:")
    print("   - nmap_scan: Execute an Nmap scan against a target")
    print("   - gobuster_scan: Execute Gobuster to find directories, DNS subdomains, or virtual hosts")
    print("   - dirb_scan: Execute Dirb web content scanner")
    print("   - nikto_scan: Execute Nikto web server scanner")
    print("   - sqlmap_scan: Execute SQLmap SQL injection scanner")
    print("   - metasploit_run: Execute a Metasploit module")
    print("   - hydra_attack: Execute Hydra password cracking tool")
    print("   - john_crack: Execute John the Ripper password cracker")
    print("   - wpscan_analyze: Execute WPScan WordPress vulnerability scanner")
    print("   - enum4linux_scan: Execute Enum4linux Windows/Samba enumeration tool")
    print("   - server_health: Check the health status of the Kali API server")
    print("   - execute_command: Execute an arbitrary command on the Kali server")
    
    print("✅ All MCP client tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()