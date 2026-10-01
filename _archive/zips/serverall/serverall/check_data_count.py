import pandas as pd

# 读取完整数据文件
df = pd.read_csv('COMPLETE_LOAN_DATA_20251029_043012.csv')
print('=== 完整贷款数据统计 ===')
print(f'总记录数: {len(df)}')
print('\n各站点记录数:')
print(df.groupby('target_site').size())

# 检查是否有其他大文件
print('\n=== 其他CSV文件记录数 ===')
try:
    df_products = pd.read_csv('LOAN_PRODUCTS_20251029_042223.csv')
    print(f'贷款产品数据: {len(df_products)} 条')
except:
    pass

try:
    df_financial = pd.read_csv('FINANCIAL_INFO_20251029_042223.csv')
    print(f'财务信息数据: {len(df_financial)} 条')
except:
    pass

try:
    df_admin = pd.read_csv('ADMIN_ACCESS_20251029_042223.csv')
    print(f'管理访问数据: {len(df_admin)} 条')
except:
    pass

try:
    df_thai = pd.read_csv('THAI_LOAN_APPLICATIONS_20251029_041220.csv')
    print(f'泰国贷款申请数据: {len(df_thai)} 条')
except:
    pass