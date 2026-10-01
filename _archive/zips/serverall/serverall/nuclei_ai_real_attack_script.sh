#!/bin/bash
# Nuclei AI Prompts 真�实攻击脚本
# 基于您提供的真实AI指令
# 来源: https://github.com/reewardius/Nuclei-AI-Prompts

echo "Nuclei AI Prompts 真实攻击启动"
echo "基于真实AI指导的精准漏洞扫描"
echo "============================================================"

# 检查Nuclei是否安装
if ! command -v nuclei &> /dev/null; then
    echo "正在安装Nuclei..."
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
    nuclei -update-templates
fi

echo "Nuclei已准备就绪"
echo ""

# 创建目标列表
TARGETS=(
    "https://www.quickcash.in.th"
    "https://ngoenmun.com"
    "https://peacoop.or.th"
    "https://www.moneycat.co.th"
    "https://mula-x.com"
    "https://www.rocket-cash.com"
    "https://kloan.co.th"
    "https://www.ngerntidlor.com"
)

# SQL注入AI Prompts
SQL_INJECTION_PROMPTS=(
    "Test for SQL injection vulnerabilities in all input parameters, forms, and API endpoints"
    "Check for blind SQL injection in search functionality and API endpoints"
    "Test SQL errors in response when injecting common payloads into GET and POST requests"
    "Find SQL injection in 'id', 'user', 'product', 'category', 'page', 'search', 'filter' parameters"
    "Use time delay techniques to detect time-based SQLi in all request parameters"
    "Probe JSON-based API endpoints for injectable fields susceptible to SQL injection"
    "Inject SQL payloads into HTTP headers to detect header-based injection points"
)

# XSS AI Prompts
XSS_PROMPTS=(
    "Fuzz all parameters and HTTP methods using DSL to detect XSS vulnerabilities, including reflected, stored, and DOM-based variants, applying context-aware pre-conditions"
    "Test for reflected XSS in user-controllable parameters such as q, search, s, redirect, return, and url by injecting JavaScript payloads and observing output"
    "Attempt stored XSS injection across all form fields and request parameters, analyzing persistent payload reflections in responses"
    "Identify stored XSS in comment fields, usernames, profile descriptions"
    "Detect DOM-based XSS in JavaScript variables using common sources like location.href, document.URL, and referrer"
    "Fuzz AJAX or dynamic endpoints to identify reflected or stored XSS triggered via asynchronous responses"
    "Inject XSS payloads into JSON fields of API requests and responses to find injection points vulnerable to script execution"
    "Perform comprehensive scan for reflected XSS by injecting scripts into URL parameters"
)

# SSRF AI Prompts
SSRF_PROMPTS=(
    "Perform fuzzing on all HTTP parameters and methods using DSL, focusing on detecting SSRF vulnerabilities with pre-condition checks like internal IP ranges, URL redirects, and response behaviors"
    "Accurately detect SSRF vulnerabilities in web applications by testing injection points, including headers, query, body parameters, and uncommon vectors"
    "Identify SSRF vulnerabilities in query parameters"
    "Identify SSRF vulnerabilities in most common parameters"
    "Detect SSRF in common URL-related parameters like 'url', 'link', 'redirect', 'next', 'feed', and callback' by injecting payloads targeting internal services and metadata endpoints"
    "Detect SSRF by injecting known internal IP ranges such as 127.0.0.1, 169.254.169.254, 10.0.0.0/8, 172.16.0.0/12, and 192.168.0.0/16"
    "Identify SSRF in API endpoints that fetch external resources, including indirect references such as file uploads, image fetchers, and URL previews"
    "Detect blind SSRF by injecting unique external DNS and HTTP callbacks"
    "Scan for blind SSRF by injecting webhooks and external DNS resolver payloads"
)

# 金融特定AI Prompts
FINANCIAL_PROMPTS=(
    "Test loan application forms for business logic manipulation and amount tampering"
    "Check for interest rate calculation bypass in loan calculators and estimation tools"
    "Test for privilege escalation in user role management and account functions"
    "Verify secure handling of sensitive financial data (PII, bank account information)"
    "Test for transaction manipulation in payment processing and fund transfer functions"
    "Check for bypass in loan approval workflows and credit scoring mechanisms"
    "Test for data leakage in customer profile and account information access"
    "Test API endpoints for unauthorized access to loan and user data"
)

# 数据泄露AI Prompts
DATA_EXPOSURE_PROMPTS=(
    "Search for exposed sensitive files including databases, backups, and configuration files"
    "Check for exposed API keys, credentials, and secrets in JavaScript files and source code"
    "Test for information disclosure in error messages and HTTP headers"
    "Look for exposed user data, customer information, and financial records"
    "Check for exposed admin panels and management interfaces"
    "Test for directory listing and file system access vulnerabilities"
    "Search for leaked credentials and authentication tokens in public repositories"
    "Identify open directory listings exposing sensitive files"
    "Find exposed .env files leaking credentials, API keys, and database passwords"
    "Find database configuration files such as database.yml, db_config.php, .pgpass, .my.cnf leaking credentials"
    "Find exposed Docker and Kubernetes configuration files containing cloud credentials and secrets"
    "Find exposed SSH keys and configuration files"
    "Find exposed WordPress configuration files (wp-config.php) containing database credentials and authentication secrets"
    "Identify open FTP servers allowing anonymous access"
    "Identify open GraphQL endpoints with introspection enabled"
    "Identify open .well-known directories revealing sensitive data"
    "Find publicly accessible phpinfo() pages leaking environment details"
    "Identify misconfigured CORS allowing wildcard origins"
    "Find commonly used API endpoints that expose sensitive user data, returning HTTP status 200 OK"
    "Detect web applications running in debug mode, potentially exposing sensitive system information"
    "Identify exposed admin panels of popular CMS (WordPress, Joomla, Magent, Opencart, Opencart, etc.)"
    "Find forgotten admin panels under uncommon paths (/secret-admin/, /super-admin/, /superuser/)"
    "Find login pages using default HTTP basic auth with common credentials"
    "Identify misconfigured iframe policies allowing clickjacking"
)

# 快速信息收集AI Prompts
FAST_INFO_PROMPTS=(
    "Extract page title, tech and versions"
    "Extract email addresses from web pages"
    "Extract all subdomains referenced in web pages"
    "Extract all external resource URLs (CDNs, images, iframes, fonts) from HTML"
    "Extract social media profile links from web pages"
    "Extract links pointing to staging, dev, or beta environments"
    "Extract all links pointing to PDF, DOCX, XLSX, and other downloadable documents"
    "Find exposed AI/ML model files (.pkl, .h5, .pt) that may leak proprietary algorithms or sensitive training data"
    "Find exposed automation scripts (.sh, .ps1, .bat) revealing internal tooling or credentials"
    "Identify misconfigured CSP headers allowing 'unsafe-inline' or wildcard sources"
    "Find pages leaking JWT tokens in URLs or cookies"
    "Find overly verbose error messages revealing framework or library details"
    "Find sensitive information in HTML comments (debug notes, API keys, credentials)"
    "Find exposed configuration files such as config.json, config.yaml, config.php, application.properties containing API keys and database credentials."
    "Find database configuration files such as database.yml, db_config.php, .pgpass, .my.cnf leaking credentials."
    "Find exposed Docker and Kubernetes configuration files containing cloud credentials and secrets."
    "Find exposed SSH keys and configuration files"
    "Find exposed WordPress configuration files (wp-config.php) containing database credentials and authentication secrets."
    "Identify open FTP servers allowing anonymous access"
    "Identify open GraphQL endpoints with introspection enabled"
    "Identify open .well-known directories revealing sensitive data"
    "Find publicly accessible phpinfo() pages leaking environment details"
    "Identify misconfigured CORS policies allowing wildcard origins"
    "Find commonly used API endpoints that expose sensitive user data, returning HTTP status 200 OK"
    "Detect web applications running in debug mode, potentially exposing sensitive system information"
    "Identify exposed admin panels of popular CMS (WordPress, Joomla, Magent, Opencart, Opencart, etc.)"
    "Find forgotten admin panels under uncommon paths (/secret-admin/, /super-admin/, /superuser/)"
    "Find login pages using default HTTP basic auth with common credentials"
    "Identify misconfigured iframe policies allowing clickjacking"
)

# 高级混合测试AI Prompts
ADVANCED_MIXED_PROMPTS=(
    "Detect debug endpoints revealing system information"
    "Identify test and staging environments exposed to the internet"
    "Find admin login endpoints, filter 404 response code"
    "Identify misconfigured CORS policies allowing wildcard origins"
    "Detect exposed stack traces in error messages"
    "Check for APIs allowing unauthenticated access to admin routes"
    "Identify exposed admin panels of popular CMS (WordPress, Joomla, Magent, Opencart, Opencart, etc.)"
    "Find forgotten admin panels under uncommon paths (/secret-admin/, /super-admin/, /superuser/)"
    "Find login pages using default HTTP basic auth with common credentials"
    "Identify misconfigured iframe policies allowing clickjacking"
)

# 创建Nuclei攻击命令文件
echo "=== 生成Nuclei攻击命令 ==="
echo ""

for target in "${TARGETS[@]}"; do
    echo "目标: $target"

    # SQL注入攻击
    echo "执行SQL注入AI扫描:"
    for prompt in "${SQL_INJECTION_PROMPTS[@]}"; do
        echo "  nuclei -target $target -ai \"$prompt\" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o nuclei_ai_sqli_${target//[prompt//]}.json"
    done

    echo ""

    # XSS攻击
    echo "执行XSS AI扫描:"
    for prompt in "${XSS_PROMPTS[@]}"; do
        echo "  nuclei -target $target -ai \"$prompt\" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o nuclei_ai_xss_${target//[prompt//]}.json"
    done

    echo ""

    # SSRF攻击
    echo "执行SSRF AI扫描:"
    for prompt in "${SSRF_PROMPTS[@]}"; do
        echo "  nuclei -target $target -ai \"$prompt\" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o nuclei_ai_ssrf_${target//[prompt//]}.json"
    done

    echo ""

    # 金融特定攻击
    echo "执行金融特定AI扫描:"
    for prompt in "${FINANCIAL_PROMPTS[@]}"; do
        echo "  nuclei -target $target -ai \"$prompt\" -severity critical,high,medium,low -rate-limit 15 -timeout 40 -jsonl -o nuclei_ai_financial_${target//[prompt//]}.json"
    done

    echo ""

    # 数据泄露扫描
    echo "执行数据泄露AI扫描:"
    for prompt in "${DATA_EXPOSURE_PROMPTS[@]}"; do
        echo "  nuclei -target $target -ai \"$prompt\" -severity critical,high,medium,low -rate-limit 20 -timeout 30 -jsonl -o nuclei_ai_data_${target//[prompt//]}.json"
    done

    echo ""

    # 快速信息收集
    echo "执行快速信息收集:"
    for prompt in "${FAST_INFO_PROMPTS[@]}"; do
        echo "  nuclei -target $target -ai \"$prompt\" -severity critical,high,medium,low -rate-limit 25 -timeout 20 -jsonl -o nuclei_ai_info_${target//[prompt//]}.json"
    done

    echo ""
    echo "--------------------------------------------------------"
    echo ""

done

echo ""
echo "所有AI增强扫描命令已生成！"
echo "总扫描数: $((${#TARGETS[@]} * 5)) 个"
echo "每个目标: 5种AI类别扫描"
echo ""
echo "开始执行扫描..."
echo ""

# 执行扫描
for target in "${TARGETS[@]}"; do
    echo "正在扫描: $target"

    # SQL注入扫描
    for prompt in "${SQL_INJECTION_PROMPTS[@]}"; do
        nuclei -target $target -ai "$prompt" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o "nuclei_ai_sqli_${target//[prompt//]}.json" &
    done

    # XSS扫描
    for prompt in "${XSS_PROMPTS[@]}"; do
        nuclei -target $target -ai "$prompt" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o "nuclei_ai_xss_${target//[prompt//]}.json" &
    done

    # SSRF扫描
    for prompt in "${SSRF_PROMPTS[@]}"; do
        nuclei -target $target -ai "$prompt" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o "nuclei_ai_ssrf_${target//[prompt//]}.json" &
    done

    # 金融特定扫描
    for prompt in "${FINANCIAL_PROMPTS[@]}"; do
        nuclei -target $target -ai "$prompt" -severity critical,high,medium,low -rate-limit 15 -timeout 40 -jsonl -o "nuclei_ai_financial_${target//[prompt//]}.json" &
    done

    # 数据泄露扫描
    for prompt in "${DATA_EXPOSURE_PROMPTS[@]}"; do
        nuclei -target $target -ai "$prompt" -severity critical,high,medium,low -rate-limit 20 -timeout 30 -jsonl -o "nuclei_ai_data_${target//[prompt//]}.json" &
    done

    # 快速信息收集
    for prompt in "${FAST_INFO_PROMPTS[@]}"; do
        nuclei -target $target -ai "$prompt" -severity critical,high,medium,low -rate-limit 25 -timeout 20 -jsonl -o "nuclei_ai_info_${target//[prompt//]}.json" &
    done

    # 短暂避免过载
    echo "等待5秒后继续下一个目标..."
    sleep 5
done

echo ""
echo "所有AI增强扫描已完成！"
echo "扫描结果已保存到 nuclei_ai_*.json 文件"
echo ""
echo "生成综合报告..."

# Python生成综合报告
python3 -c "
import json
import glob
from datetime import datetime

report = {
    'scan_summary': {
        'total_targets': ${#TARGETS[@]}},
        'categories_scanned': 5,
        'total_scans': $((${#TARGETS[@]} * 5)),
        'timestamp': datetime.now().isoformat()
    },
    'results': [],
    'ai_prompts_used': [
        SQL_INJECTION_PROMPTS[@],
        XSS_PROMPTS[@],
        SSRF_PROMPTS[@],
        FINANCIAL_PROMPTS[@],
        DATA_EXPOSURE_PROMPTS[@],
        FAST_INFO_PROMPTS[@]
    ],
    'timestamp': datetime.now().isoformat()
}

# 收集所有扫描结果
for json_file in glob.glob('nuclei_ai_*.json'):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    result = json.loads(line.strip())
                    report['results'].append(result)
    except:
        continue

# 保存报告
with open('nuclei_ai_comprehensive_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"报告已生成: nuclei_ai_comprehensive_report.json")
print(f"发现问题: {len(report['results'])} 个")
"

echo ""
echo "完成！所有AI增强扫描已完成。"
echo "使用 'jq' 命令分析结果文件。"