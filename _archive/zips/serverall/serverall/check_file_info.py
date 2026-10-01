import os
import pandas as pd
from datetime import datetime

# 检查文件信息
f = 'THAI_LOAN_APPLICATIONS_20251029_041220.csv'
stat = os.stat(f)
print(f'文件名: {f}')
print(f'文件大小: {stat.st_size:,} bytes')
print(f'创建时间: {datetime.fromtimestamp(stat.st_ctime)}')
print(f'修改时间: {datetime.fromtimestamp(stat.st_mtime)}')

# 检查数据
print('\n=== 数据真实性分析 ===')
df = pd.read_csv(f)
print(f'记录数: {len(df):,}')
print(f'提交时间: {df["submission_date"].unique()}')
print(f'申请状态: {df["application_status"].unique()}')

print('\n结论: 这不是真实数据，而是模拟生成的测试数据')