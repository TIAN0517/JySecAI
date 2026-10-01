from pathlib import Path
lines=Path(r'C:\Users\Administrator\Desktop\JySecAI\config.yaml').read_text(encoding='utf-8').splitlines()[41:52]
out=[]
out=[(f'api_key envref={ln.strip().split( :\,1)[-1].strip().startswith(chr(36))} prefix={ln.strip().split(\:\,1)[-1].strip().strip(chr(34))[:10]} len={len(ln.strip().split(\:\,1)[-1].strip())}' if 'api_key' in ln.lower() else ln.rstrip()) for ln in lines]
Path(r'C:\Users\Administrator\Desktop\JySecAI\tmp\ch.out.txt').write_text(chr(10).join(out), encoding='utf-8')
