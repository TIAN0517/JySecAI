"""3400 /captcha GIF89a 下载 + 简单 OCR + /api/login 测试"""
import requests
import io
import time

s = requests.Session()
s.headers.update({
    'Origin': 'http://35.234.50.28:3400',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
})

# Step 1: 下载 captcha
print('[*] GET /captcha', flush=True)
r = s.get('http://35.234.50.28:3400/captcha', timeout=10)
print(f'  status={r.status_code} size={len(r.content)} Content-Type={r.headers.get("Content-Type")}', flush=True)
print(f'  set-cookie: {s.cookies.get_dict()}', flush=True)

# 写入文件做手工分析
gif_path = '/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/captcha3400.gif'
with open(gif_path, 'wb') as f:
    f.write(r.content)
print(f'  saved -> {gif_path}', flush=True)

# Step 2: 探测 captcha 数据格式（GIF89a 头/帧/调色板）
print('[*] Step 2: GIF header analysis', flush=True)
print(f'  magic: {r.content[:6]}', flush=True)
print(f'  hex first 80B: {r.content[:80].hex()}', flush=True)

# Step 3: 用 PIL 解析 GIF 帧
try:
    from PIL import Image
    img = Image.open(io.BytesIO(r.content))
    print(f'  PIL: size={img.size} mode={img.mode} n_frames={getattr(img, "n_frames", 1)}', flush=True)
    # 保存第一帧为 PNG 做清晰分析
    img.convert('RGB').save(gif_path.replace('.gif', '_frame0.png'))
    print(f'  frame0 saved', flush=True)
except Exception as e:
    print(f'  PIL err: {e}', flush=True)

# Step 4: 测试 /api/login（猜测）
print('[*] Step 4: GET/POST /api/login', flush=True)
for method, body in [('GET', None),
                      ('POST', '{}'),
                      ('POST', '{"username":"admin","password":"admin"}'),
                      ('POST', '{"username":"admin","password":"admin","captcha":"abcd"}'),
                      ('POST', '{"sessionId":"test"}')]:
    try:
        if method == 'GET':
            r2 = s.request(method, 'http://35.234.50.28:3400/api/login', timeout=10)
        else:
            r2 = s.request(method, 'http://35.234.50.28:3400/api/login',
                           json=eval(body) if body.startswith('{') else None,
                           timeout=10)
        bs = (body or '')[:50]
        print(f'  {method} {bs} -> {r2.status_code} {r2.text[:200]}', flush=True)
    except Exception as e:
        bs = (body or '')[:50]
        print(f'  {method} {bs} -> err {e}', flush=True)