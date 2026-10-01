import pathlib 
ls=pathlib.Path(r'C:\Users\Administrator\Desktop\JySecAI\config.yaml').read_text(encoding='utf-8').splitlines() 
print('\n'.join('%d:%s'%(i+1,ls[i]) for i in range(800,min(830,len(ls))))) 
