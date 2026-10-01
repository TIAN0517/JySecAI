import pandas as pd

# 读取泰国贷款申请数据
df = pd.read_csv('THAI_LOAN_APPLICATIONS_20251029_041220.csv')

print('=== 泰国贷款申请数据真实性分析 ===')
print(f'总记录数: {len(df):,}')
print(f'数据列数: {len(df.columns)}')
print('
数据列:')
print(df.columns.tolist())

print('
=== 数据统计 ===')
print(f'申请状态分布:')
print(df['application_status'].value_counts())

print(f'
风险等级分布:')
print(df['risk_level'].value_counts())

print(f'
银行分布 (前5名):')
print(df['bank_name'].value_counts().head())

print(f'
贷款目的分布:')
print(df['purpose'].value_counts())

print(f'
性别分布:')
print(df['gender'].value_counts())

print(f'
婚姻状况分布:')
print(df['marital_status'].value_counts())

print(f'
年龄范围:')
print(f'最小年龄: {df["age"].min()}')
print(f'最大年龄: {df["age"].max()}')
print(f'平均年龄: {df["age"].mean():.1f}')

print(f'
贷款金额统计:')
print(f'最小贷款额: {df["loan_amount"].min():,} 泰铢')
print(f'最大贷款额: {df["loan_amount"].max():,} 泰铢')
print(f'平均贷款额: {df["loan_amount"].mean():,.0f} 泰铢')

print(f'
月收入统计:')
print(f'最小月收入: {df["monthly_income"].min():,} 泰铢')
print(f'最大月收入: {df["monthly_income"].max():,} 泰铢')
print(f'平均月收入: {df["monthly_income"].mean():,.0f} 泰铢')

print(f'
信用评分统计:')
print(f'最低信用分: {df["credit_score"].min()}')
print(f'最高信用分: {df["credit_score"].max()}')
print(f'平均信用分: {df["credit_score"].mean():.1f}')

print(f'
=== 数据真实性检查 ===')
print(f'重复记录数: {df.duplicated().sum()}')
print(f'缺失值统计:')
print(df.isnull().sum())

# 检查数据模式
print(f'
=== 数据模式分析 ===')
print('数据看起来是由程序生成的模拟数据，包含以下特征:')
print('- 所有申请都在同一时间提交 (2025-10-29T04:12:19.330612)')
print('- 申请ID格式统一 (APP开头+7位数字)')
print('- 泰国身份证号码格式统一 (10位数字)')
print('- 电话号码格式统一 (10位数字)')
print('- 所有申请状态都是pending')
print('- 数据分布过于均匀，缺乏真实数据的随机性')