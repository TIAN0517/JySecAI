import openai

client = openai.OpenAI(
    base_url="http://127.0.0.1:8001/v1",
    api_key="EMPTY"
)

# 模擬從代理或日誌擷取的 HTTP 請求
sample_http_traffic = """
POST /api/v1/update_profile HTTP/1.1
Host: internal-app.local
Content-Type: application/json
Cookie: session_id=guest_user_9821

{
  "user_id": 10042,
  "role": "admin",
  "bio": "<script>alert(document.cookie)</script>"
}
"""

prompt = f"""
Analyze the following HTTP request for potential security flaws (e.g., OWASP Top 10, IDOR, input validation issues). 
Highlight findings and provide defensive remediation:

```http
{sample_http_traffic}
