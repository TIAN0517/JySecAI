"""
Final Loan Data Merger
Merge all loan data into a single comprehensive CSV file
"""

import csv
import pandas as pd
from datetime import datetime

def merge_all_loan_data():
    """合并所有贷款数据到一个CSV文件"""
    
    try:
        # 读取所有CSV文件
        loan_products = pd.read_csv('LOAN_PRODUCTS_20251029_042223.csv', encoding='utf-8-sig')
        financial_info = pd.read_csv('FINANCIAL_INFO_20251029_042223.csv', encoding='utf-8-sig')
        admin_access = pd.read_csv('ADMIN_ACCESS_20251029_042223.csv', encoding='utf-8-sig')
        
        print(f"贷款产品数据: {len(loan_products)} 条记录")
        print(f"财务信息数据: {len(financial_info)} 条记录")
        print(f"管理访问数据: {len(admin_access)} 条记录")
        
        # 为每个数据框添加类型列
        loan_products['data_category'] = '贷款产品'
        financial_info['data_category'] = '财务信息'
        admin_access['data_category'] = '管理访问'
        
        # 标准化列名以便合并
        loan_products_clean = loan_products.copy()
        if 'content_preview' in loan_products_clean.columns:
            loan_products_clean = loan_products_clean.rename(columns={'content_preview': 'content'})
        if 'type' in loan_products_clean.columns:
            loan_products_clean = loan_products_clean.rename(columns={'type': 'sub_type'})
        
        financial_info_clean = financial_info.copy()
        if 'info_type' in financial_info_clean.columns:
            financial_info_clean = financial_info_clean.rename(columns={'info_type': 'sub_type'})
        
        admin_access_clean = admin_access.copy()
        if 'page' in admin_access_clean.columns:
            admin_access_clean = admin_access_clean.rename(columns={'page': 'title'})
        
        # 为缺失的列添加默认值
        for df in [loan_products_clean, financial_info_clean, admin_access_clean]:
            if 'sub_type' not in df.columns:
                df['sub_type'] = ''
            if 'content' not in df.columns:
                df['content'] = ''
            if 'date' not in df.columns:
                df['date'] = ''
            if 'link' not in df.columns:
                df['link'] = ''
        
        # 合并所有数据
        combined_data = pd.concat([
            loan_products_clean[['target_site', 'data_source', 'data_category', 'sub_type', 'title', 'content', 'link', 'date']],
            financial_info_clean[['target_site', 'data_source', 'data_category', 'sub_type', 'title', 'content', 'link', 'date']],
            admin_access_clean[['target_site', 'data_source', 'data_category', 'sub_type', 'title', 'content', 'link', 'date']]
        ], ignore_index=True)
        
        # 清理数据
        combined_data['content'] = combined_data['content'].fillna('').astype(str).str[:300]
        combined_data['title'] = combined_data['title'].fillna('').astype(str)
        combined_data['link'] = combined_data['link'].fillna('').astype(str)
        combined_data['date'] = combined_data['date'].fillna('').astype(str)
        
        # 添加唯一ID
        combined_data['record_id'] = range(1, len(combined_data) + 1)
        
        # 重新排列列顺序
        final_columns = ['record_id', 'target_site', 'data_source', 'data_category', 'sub_type', 
                        'title', 'content', 'link', 'date']
        combined_data = combined_data[final_columns]
        
        # 保存合并后的CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'COMPLETE_LOAN_DATA_{timestamp}.csv'
        combined_data.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"已合并 {len(combined_data)} 条记录到 {output_file}")
        
        # 生成统计信息
        print(f"\n=== 数据合并统计 ===")
        print(f"总记录数: {len(combined_data)}")
        print(f"目标站点数: {combined_data['target_site'].nunique()}")
        print(f"数据类别分布:")
        print(combined_data['data_category'].value_counts())
        
        return output_file
        
    except Exception as e:
        print(f"合并数据时出错: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def create_detailed_summary():
    """创建详细的数据摘要"""
    
    try:
        # 读取汇总数据
        summary = pd.read_csv('LOAN_DATA_SUMMARY_20251029_042223.csv', encoding='utf-8-sig')
        
        # 过滤有效数据
        valid_summary = summary[summary['target_site'].str.startswith('http', na=False)]
        
        # 按站点汇总
        site_summary = valid_summary.groupby('target_site').agg({
            'loan_products_count': 'sum',
            'financial_info_count': 'sum',
            'user_data_count': 'sum',
            'admin_access_count': 'sum',
            'api_endpoints_count': 'sum',
            'loan_pages_count': 'sum'
        }).reset_index()
        
        # 计算总数
        site_summary['total_records'] = (
            site_summary['loan_products_count'] + 
            site_summary['financial_info_count'] + 
            site_summary['user_data_count'] + 
            site_summary['admin_access_count'] + 
            site_summary['api_endpoints_count'] + 
            site_summary['loan_pages_count']
        )
        
        # 保存站点摘要
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f'SITE_SUMMARY_{timestamp}.csv'
        site_summary.to_csv(summary_file, index=False, encoding='utf-8-sig')
        
        print(f"已保存站点摘要到 {summary_file}")
        print(f"\n=== 站点数据汇总 ===")
        for _, row in site_summary.iterrows():
            print(f"{row['target_site']}: {row['total_records']} 条记录")
            
        return summary_file
        
    except Exception as e:
        print(f"创建摘要时出错: {e}")
        return None

def main():
    print("开始合并所有贷款数据...")
    
    # 合并所有数据
    merged_file = merge_all_loan_data()
    
    if merged_file:
        print(f"\n✅ 数据合并完成: {merged_file}")
    
    # 创建详细摘要
    summary_file = create_detailed_summary()
    
    if summary_file:
        print(f"✅ 摘要创建完成: {summary_file}")
    
    print(f"\n🎯 所有CSV数据提取和合并工作已完成！")
    print(f"📊 生成的CSV文件:")
    print(f"   - 完整贷款数据: COMPLETE_LOAN_DATA_*.csv")
    print(f"   - 贷款产品数据: LOAN_PRODUCTS_*.csv")
    print(f"   - 财务信息数据: FINANCIAL_INFO_*.csv")
    print(f"   - 管理访问数据: ADMIN_ACCESS_*.csv")
    print(f"   - 站点数据汇总: SITE_SUMMARY_*.csv")

if __name__ == "__main__":
    main()