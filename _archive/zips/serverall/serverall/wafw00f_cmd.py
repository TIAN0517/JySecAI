#!/usr/bin/env python3
"""
WAFW00F命令行工具包装器
用于检测Web应用防火墙
"""

import sys
import os
import subprocess

def main():
    """主函数"""
    # 添加wafw00f模块路径
    wafw00f_path = os.path.join(os.path.dirname(__file__), 'wafw00f')
    sys.path.insert(0, wafw00f_path)

    # 运行wafw00f
    try:
        from wafw00f.main import main as wafw00f_main
        wafw00f_main()
    except Exception as e:
        print(f"运行wafw00f时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()