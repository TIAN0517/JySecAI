from pathlib import Path
p=Path(r'C:\Users\Administrator\Desktop\JySecAI\internal\handler\auth.go')
lines=p.read_text(encoding='utf-8').splitlines()
Path(r'C:\Users\Administrator\Desktop\JySecAI\tmp\sl.out.txt').write_text(chr(10).join(f'{i}:{lines[i-1]}' for i in range(45, min(120,len(lines)+1))), encoding='utf-8')
