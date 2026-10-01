from pathlib import Path 
p=Path(r'C:\Users\Administrator\Desktop\JySecAI\.github\workflows\jysec-ci.yml') 
t=p.read_text(encoding='utf-8') 
old='''      - run: docker compose -f compose.jysec.yml config --quiet\n      - run:           docker run --rm\n          --add-host core:127.0.0.1\n          --add-host control-plane:127.0.0.1\n          -v "$PWD/deploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro"\n          nginx:1.29-alpine nginx -t\n''' 
