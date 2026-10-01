import os
seen=set(); out=[]
def add(w):
    w=w.strip()
    if w and w not in seen and 3<=len(w)<=24:
        seen.add(w); out.append(w)
for f in ['/tmp/rockyou_top1k.txt','/tmp/wordlist.txt']:
    if os.path.exists(f):
        for l in open(f,errors='ignore'): add(l)
for l in open('ofa77_pwds.txt'): add(l)   # my 523
# targeted Chinese + ofa77 + domain
for p in ['ofa77','ofa','admin','123456','888888','666666','shop','1777','377','168']:
    for n in ['123','1234','12345','123456','2024','2025','2026','2023','888','666','168','1777','377','888888','666666','111111','1314','520','5201314','9527','778899','12345678']:
        for c in (p+n, p+'@'+n, p+n+'!', p+'!'+n, n+p, p+n+'@', p+'_'+n):
            add(c)
for w in ['jingpin','shangcheng','jingpin123','shangcheng123','123456a','a123456','123456A','A123456','1qaz2wsx','1q2w3e4r','q1w2e3r','123456q','q123456','1234567','12345678','abcdef','abcd1234','1234abcd','woaini','520woaini','112233','123123','123321','000000a','88888888','66666666','123456654321','admin!','admin@','admin#','123456!','123456@','123456#','admin2024!','admin@2024','admin2025','admin@2025','1qaz@WSX','P@ssw0rd','passw0rd','admin1!@#','Admin@123456','admin123!','Admin@1234','admin@12345','admin@123456','admin12345!']:
    add(w)
open('ofa77_pwds_big.txt','w').write('\n'.join(out))
print('final dictionary size:', len(out))
