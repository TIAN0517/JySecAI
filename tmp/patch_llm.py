from pathlib import Path
p=Path(r'C:\Users\Administrator\Desktop\JySecAI\config.yaml')
t=p.read_text(encoding='utf-8')
old=t
t=t.replace(' default_channel: nvidia-primary',' default_channel: jy-gateway',1)
t=t.replace(' model_retry_max_retries: 0',' model_retry_max_retries: 6',1)
t=t.replace(' model_retry_max_backoff_sec: 0',' model_retry_max_backoff_sec: 45',1)
t=t.replace(' model_failover_channels: []',' model_failover_channels: [jy-gateway]',1)
t=t.replace(' model_failover_max_retries: 0',' model_failover_max_retries: 2',1)
if t==old: raise SystemExit('no replacements')
p.write_text(t, encoding='utf-8')
print('patched')
