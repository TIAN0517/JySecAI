import pathlib 
ls=pathlib.Path(r'C:\Users\Administrator\Desktop\JySecAI\web\static\js\chat-codex-layout.test.cjs').read_text(encoding='utf-8').splitlines() 
print('\n'.join('%d:%s'%(i+1,ls[i]) for i in range(0,min(20,len(ls))))) 
