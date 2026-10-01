import pathlib 
ls=pathlib.Path(r'C:\Users\Administrator\Desktop\JySecAI\platform\src\core\catalog.ts').read_text(encoding='utf-8').splitlines() 
for i in [56,57,58,59,60,61,123,124,125,126]: 
    print(i, ls[i-1]) 
