from pathlib import Path
import json,urllib.request,ssl
text=Path(r'C:\Users\Administrator\Desktop\JySecAI\config.yaml').read_text(encoding='utf-8')
key=''
grab=False
for ln in text.splitlines():
 if ln.strip()=='jy-gateway:': grab=True; continue
 if grab and ln.strip().startswith('api_key:'): key=ln.split(':',1)[1].strip().strip(chr(34)); break
print('prefix', key[:8], 'len', len(key))
req=urllib.request.Request('https://llm.jytian.cc.cd/api/v1/models', headers={'Authorization':'Bearer '+key})
try:
 with urllib.request.urlopen(req, timeout=12) as r: print('models', r.status)
except Exception as e: print('models_err', getattr(e,'code',type(e).__name__))
body=json.dumps({'model':'jy-5.3-coder','stream':False,'max_tokens':8,'messages':[{'role':'user','content':'ping'}]}).encode()
req2=urllib.request.Request('https://llm.jytian.cc.cd/api/v1/chat/completions', data=body, headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
try:
 with urllib.request.urlopen(req2, timeout=30) as r: print('chat', r.status)
except Exception as e: print('chat_err', getattr(e,'code',type(e).__name__), str(e)[:80])
