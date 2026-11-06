#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""建立外部 MySQL 接收端所需的資料庫與專用帳號。

用途
----
JySecAI 的外部 MySQL 接收端（internal/receiver）需要三張表與一個「只授權該庫」
的專用帳號。這個腳本負責把它們建好，並驗證權限隔離真的生效。

為什麼不直接用 root
------------------
主力機的 MySQL 上還有其他庫含個資（授權記錄、政府/金融目標資料）。
接收端只寫自己的庫，用 root 等於把所有庫的權限都交出去。
腳本因此建立最小權限帳號：只對接收庫有 SELECT/INSERT/UPDATE/DELETE/
CREATE/ALTER/INDEX，沒有 DROP、沒有 GRANT OPTION、碰不到其他庫。

用法
----
    pip install pymysql
    export MYSQL_HOST=10.0.0.1 MYSQL_PORT=3306
    export MYSQL_ROOT_USER=root
    export MYSQL_ROOT_PASSWORD='...'
    python scripts/setup-receiver-db.py

環境變數
--------
MYSQL_HOST          主力機位址（預設 10.0.0.1）
MYSQL_PORT          連接埠（預設 3306）
MYSQL_ROOT_USER     管理帳號（預設 root）
MYSQL_ROOT_PASSWORD 管理帳號密碼（必填）
RECEIVER_DB         接收庫名稱（預設 jy_vuln_receiver）
RECEIVER_USER       接收端帳號（預設 jy_receiver）

密碼由腳本生成（只含英數），只寫進本機 config.yaml，不經由主控台輸出；
輸出只給長度與 sha256 前 12 碼。
"""

import getpass
import hashlib
import os
import re
import secrets
import string
import sys

try:
    import pymysql
except ImportError:
    sys.exit("需要 pymysql：pip install pymysql")

HOST = os.environ.get("MYSQL_HOST", "10.0.0.1")
PORT = int(os.environ.get("MYSQL_PORT", "3306"))
ROOT_USER = os.environ.get("MYSQL_ROOT_USER", "root")
RECEIVER_DB = os.environ.get("RECEIVER_DB", "jy_vuln_receiver")
RECEIVER_USER = os.environ.get("RECEIVER_USER", "jy_receiver")
RECEIVER_HOST = "%"

# 密碼字元集：只用英數。DSN 格式對 '/' 敏感、對 '@' 取「最後一個」才安全，
# 兩者都避開最省事。32 字元 ≈ 190 bits 熵。
ALPHABET = string.ascii_letters + string.digits

GRANTS = "SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX"


def root_password():
    value = os.environ.get("MYSQL_ROOT_PASSWORD")
    if value:
        return value
    return getpass.getpass("MySQL %s 的密碼: " % ROOT_USER)


def generate_password(length=32):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def main():
    password = generate_password()

    conn = pymysql.connect(
        host=HOST, port=PORT, user=ROOT_USER, password=root_password(),
        connect_timeout=8, read_timeout=30, write_timeout=30,
        charset="utf8mb4", autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE DATABASE IF NOT EXISTS %s CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                % RECEIVER_DB
            )
            # DROP USER 會一併清掉這個帳號的所有授權，所以不需要另外 REVOKE。
            cur.execute("DROP USER IF EXISTS '" + RECEIVER_USER + "'@'" + RECEIVER_HOST + "'")
            # pymysql 會做 query % args，SQL 裡的字面 '%' 要寫成 '%%' 才不會被
            # 當成格式符號。這裡不用 Python 的 % 格式化（會再吃掉一層 %）。
            cur.execute(
                "CREATE USER '" + RECEIVER_USER + "'@'%%' IDENTIFIED BY %s", (password,)
            )
            cur.execute(
                "GRANT " + GRANTS + " ON " + RECEIVER_DB + ".* TO '"
                + RECEIVER_USER + "'@'" + RECEIVER_HOST + "'"
            )
            cur.execute("FLUSH PRIVILEGES")
            cur.execute("SHOW GRANTS FOR '" + RECEIVER_USER + "'@'" + RECEIVER_HOST + "'")
            print("-- 接收端帳號的授權 --")
            for row in cur.fetchall():
                print("   %s" % row[0])
    finally:
        conn.close()

    # 用新帳號實際連一次，確認權限真的生效 —— 這一步不能省。
    conn = pymysql.connect(
        host=HOST, port=PORT, user=RECEIVER_USER, password=password,
        connect_timeout=8, read_timeout=15, write_timeout=15,
        charset="utf8mb4", autocommit=True, database=RECEIVER_DB,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW DATABASES")
            visible = [r[0] for r in cur.fetchall()]
            print("   可見資料庫 = %s" % (", ".join(visible) if visible else "(無)"))

            # 負向驗證：不得觸及其他庫。
            cur.execute(
                "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
                "WHERE SCHEMA_NAME NOT IN (%s, 'information_schema', 'performance_schema', 'mysql', 'sys')",
                (RECEIVER_DB,),
            )
            others = [r[0] for r in cur.fetchall()]
            if not others:
                print("   （這台 MySQL 上沒有其他庫可驗證隔離）")
            for other in others[:5]:
                try:
                    cur.execute("SELECT COUNT(*) FROM `%s`.`%s`" % (other, "nonexistent_probe_table"))
                    print("   !! 警告：可以讀取 %s —— 權限隔離失效" % other)
                except Exception as exc:
                    print("   越權讀取 %s 已被拒絕（%s）" % (other, type(exc).__name__))
    finally:
        conn.close()

    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()[:12]
    print("")
    print("完成。接收庫 = %s，帳號 = %s" % (RECEIVER_DB, RECEIVER_USER))
    print("密碼長度 %d，sha256 前 12 碼 %s" % (len(password), digest))
    print("請把密碼寫進本機 config.yaml 的 external_mysql.password，")
    print("或用環境變數 ${JY_SEC_MYSQL_PASSWORD} 帶入。")


if __name__ == "__main__":
    main()
