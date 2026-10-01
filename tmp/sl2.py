from pathlib import Path
p=Path(r'C:\Users\Administrator\Desktop\JySecAI\internal\multiagent\eino_model_resilience.go')
lines=p.read_text(encoding='utf-8').splitlines()
Path(r'C:\Users\Administrator\Desktop\JySecAI\tmp\sl2.out.txt').write_text(chr(10).join(f'{i}:{lines[i-1]}' for i in range(150, min(260,len(lines)+1))), encoding='utf-8')
