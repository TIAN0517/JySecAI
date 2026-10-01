import openai

client = openai.OpenAI(
    base_url="http://127.0.0.1:8001/v1",
    api_key="EMPTY"
)

response = client.chat.completions.create(
    model="/workspace/Huihui-CyberStrike-OffSec-35B-abliterated-Q8_0.gguf",
    messages=[
        {"role": "system", "content": "You are a web application security auditor. Analyze the following HTTP traffic for potential vulnerabilities (e.g., OWASP Top 10, IDOR, misconfigurations) and provide remediation."},
        {"role": "user", "content": "GET /api/user?id=105 HTTP/1.1\nHost: example.com\nCookie: session=xyz..."}
    ],
    temperature=0.2
)

print(response.choices[0].message.content)
