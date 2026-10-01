import subprocess, os
d='/opt/CyberStrikeAI/tmp/workspace/projects/b19751aa-c845-42e9-adca-e4cd170b0d5b'
os.chdir(d)
log=open('brute.log','w')
p=subprocess.Popen(['python3','brute.py','886911111222','1000000','0'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
with open('brute.pid','w') as f:
    f.write(str(p.pid))
print('started', p.pid)
