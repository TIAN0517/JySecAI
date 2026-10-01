from pathlib import Path
lines=Path(r'C:\Users\Administrator\Desktop\JySecAI\config.yaml').read_text(encoding='utf-8').splitlines()
chunk=chr(10).join(f'{i}:{lines[i-1]}' for i in range(370, min(430,len(lines)+1)) if 'key' not in lines[i-1].lower() and 'secret' not in lines[i-1].lower() and 'password' not in lines[i-1].lower())
Path(r'C:\Users\Administrator\Desktop\JySecAI\tmp\cfg.out.txt').write_text(chunk, encoding='utf-8')
