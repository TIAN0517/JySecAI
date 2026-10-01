#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dast-Xray 数据库配置切换工具
用于快速切换不同数据库配置
"""

import os
import sys
import shutil
import subprocess

def switch_database_config(database_type):
    """切换数据库配置"""
    config_dir = "src/main/resources"
    original_config = os.path.join(config_dir, "application.yml")
    backup_config = os.path.join(config_dir, "application.yml.backup")

    if not os.path.exists(backup_config):
        print("创建原配置文件备份...")
        shutil.copy2(original_config, backup_config)

    # 数据库配置映射
    configs = {
        "h2-memory": {
            "url": "jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE",
            "username": "sa",
            "password": "",
            "driver": "org.h2.Driver",
            "dialect": "h2"
        },
        "h2-file": {
            "url": "jdbc:h2:file:./data/dast-xray;DB_CLOSE_ON_EXIT=FALSE",
            "username": "sa",
            "password": "admin123",
            "driver": "org.h2.Driver",
            "dialect": "h2"
        },
        "mysql": {
            "url": "jdbc:mysql://localhost:3306/dast_xray?useSSL=false&serverTimezone=UTC&characterEncoding=utf8&allowPublicKeyRetrieval=true",
            "username": "root",
            "password": "yourpassword",
            "driver": "com.mysql.cj.jdbc.Driver",
            "dialect": "mysql"
        },
        "postgresql": {
            "url": "jdbc:postgresql://localhost:5432/dast_xray",
            "username": "postgres",
            "password": "yourpassword",
            "driver": "org.postgresql.Driver",
            "dialect": "postgresql"
        }
    }

    if database_type not in configs:
        print(f"错误: 不支持的数据库类型 '{database_type}'")
        print(f"支持的类型: {', '.join(configs.keys())}")
        return False

    config = configs[database_type]

    # 读取原配置文件
    with open(original_config, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换数据库配置
    lines = content.split('\n')
    new_lines = []
    in_datasource = False

    for line in lines:
        if line.strip().startswith('datasource:'):
            in_datasource = True
            new_lines.append(line)
        elif in_datasource and line.strip().startswith('url:'):
            new_lines.append(f'    url: {config["url"]}')
        elif in_datasource and line.strip().startswith('username:'):
            new_lines.append(f'    username: {config["username"]}')
        elif in_datasource and line.strip().startswith('password:'):
            new_lines.append(f'    password: {config["password"]}')
        elif in_datasource and line.strip().startswith('driver-class-name:'):
            new_lines.append(f'    driver-class-name: {config["driver"]}')
        elif in_datasource and line.strip().startswith('h2:'):
            if database_type.startswith('h2'):
                new_lines.append(line)
            else:
                # 跳过H2配置如果不是H2数据库
                continue
        elif in_datasource and line.strip().startswith('pagehelper:'):
            new_lines.append(f'  helperDialect: {config["dialect"]}')
            in_datasource = False
            new_lines.append(line)
        else:
            new_lines.append(line)

    # 写入新配置
    with open(original_config, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"✅ 已切换到 {database_type} 数据库配置")
    return True

def rebuild_project():
    """重新构建项目"""
    print("🔄 重新构建项目...")
    try:
        result = subprocess.run(
            ["/c/ProgramData/chocolatey/lib/maven/apache-maven-3.9.11/bin/mvn",
             "clean", "package", "-DskipTests"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print("✅ 项目构建成功")
            return True
        else:
            print(f"❌ 项目构建失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 构建超时")
        return False
    except Exception as e:
        print(f"❌ 构建错误: {e}")
        return False

def main():
    print("🔧 Dast-Xray 数据库配置切换工具")
    print("=" * 50)

    if len(sys.argv) != 2:
        print("用法: python switch-database.py <数据库类型>")
        print("\n支持的数据库类型:")
        print("  h2-memory     - H2 内存数据库 (默认)")
        print("  h2-file       - H2 文件数据库 (持久化)")
        print("  mysql         - MySQL 数据库")
        print("  postgresql    - PostgreSQL 数据库")
        return

    database_type = sys.argv[1].lower()

    # 检查目录
    if not os.path.exists("pom.xml"):
        print("❌ 错误: 请在项目根目录运行此脚本")
        return

    # 切换配置
    if switch_database_config(database_type):
        # 询问是否重新构建
        rebuild = input("\n是否重新构建项目? (y/N): ").lower().strip()
        if rebuild in ['y', 'yes']:
            if rebuild_project():
                print("\n🎉 数据库配置切换完成!")
                print(f"现在可以启动应用: java -jar target/app.jar")
            else:
                print("\n⚠️  配置已更新但构建失败，请检查错误信息")
        else:
            print("\n✅ 配置已更新，请手动重新构建项目")

if __name__ == "__main__":
    main()