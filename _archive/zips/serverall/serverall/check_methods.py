#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from exploitation_module import ExploitationEngine

# 查看类的方法
methods = [method for method in dir(ExploitationEngine) if not method.startswith('_')]
print('ExploitationEngine 类的方法:')
for method in methods:
    print(f'  - {method}')

# 查看所有方法（包括私有方法）
all_methods = [method for method in dir(ExploitationEngine)]
print('\n所有方法（包括私有方法）:')
for method in all_methods:
    print(f'  - {method}')