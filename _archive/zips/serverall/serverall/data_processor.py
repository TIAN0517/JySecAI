import json
import csv
import sys
import os
from datetime import datetime

# 设置输出编码
os.system('chcp 65001 > nul')
sys.stdout.reconfigure(encoding='utf-8')

# 加载响应数据
print("[*] 加载响应数据...")
with open('response_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"[OK] 成功加载数据")
print(f"[*] 总商品数: {data['page']['count']}")
print(f"[*] 当前页商品数: {len(data['dataList'])}")

# ============================================
# 1. 提取关键商品信息
# ============================================
print("\n" + "="*80)
print("1. 商品信息提取")
print("="*80)

items_summary = []
for idx, item in enumerate(data['dataList'], 1):
    items_summary.append({
        '序号': idx,
        '商品名': item.get('itemName', 'N/A'),
        '标题': item.get('title', 'N/A')[:50],  # 限制长度
        '原价': item.get('marketPrice', 0),
        '折扣价': item.get('price', 0),
        '折扣率': item.get('itemOffRate', 'N/A'),
        '商家': item.get('codShopName', 'N/A'),
        '有货': item.get('isStock', 'N/A'),
        '商品ID': item.get('itemId', 'N/A'),
    })

# 显示前5条
print("\n[*] 前 5 条商品:\n")
for item in items_summary[:5]:
    item_name = item.get('商品名') or 'N/A'
    original_price = item.get('原价') or 0
    discount_price = item.get('折扣价') or 0
    discount_rate = item.get('折扣率') or 'N/A'
    print(f"   #{item['序号']:2d} | {str(item_name)[:20]:20s} | 原价: {original_price:8.0f} | 折扣价: {discount_price:8.0f} | {str(discount_rate):6s}")

# ============================================
# 2. 价格统计分析
# ============================================
print("\n" + "="*80)
print("2. 价格统计分析")
print("="*80)

prices = [item.get('price', 0) for item in data['dataList'] if item.get('price')]
market_prices = [item.get('marketPrice', 0) for item in data['dataList'] if item.get('marketPrice')]

if prices:
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)
    
    print(f"\n[*] 折扣价统计:")
    print(f"   - 最低价: {min_price:,.2f}")
    print(f"   - 最高价: {max_price:,.2f}")
    print(f"   - 平均价: {avg_price:,.2f}")

if market_prices:
    avg_market = sum(market_prices) / len(market_prices)
    avg_discount = ((avg_market - avg_price) / avg_market * 100) if avg_market > 0 else 0
    print(f"\n[*] 原价统计:")
    print(f"   - 平均原价: {avg_market:,.2f}")
    print(f"   - 平均折扣: {avg_discount:.1f}%")

# ============================================
# 3. 商家分布
# ============================================
print("\n" + "="*80)
print("3. 商家分布统计")
print("="*80)

merchants = {}
for item in data['dataList']:
    merchant = item.get('codShopName', 'Unknown')
    merchants[merchant] = merchants.get(merchant, 0) + 1

print(f"\n[*] 商家数量: {len(merchants)}")
print(f"\n[*] 前 10 大商家:")
sorted_merchants = sorted(merchants.items(), key=lambda x: x[1], reverse=True)
for idx, (merchant, count) in enumerate(sorted_merchants[:10], 1):
    print(f"   {idx:2d}. {merchant:30s} : {count:3d} 商品")

# ============================================
# 4. 库存状态统计
# ============================================
print("\n" + "="*80)
print("4. 库存状态")
print("="*80)

stock_status = {}
for item in data['dataList']:
    status = item.get('isStock', 'unknown')
    stock_status[status] = stock_status.get(status, 0) + 1

print(f"\n[*] 库存分布:")
for status, count in sorted(stock_status.items()):
    status_text = "有货" if status == 'y' else "无货" if status == 'n' else "未知"
    percentage = (count / len(data['dataList']) * 100) if len(data['dataList']) > 0 else 0
    print(f"   - {status_text:4s} ({status}): {count:3d} ({percentage:5.1f}%)")

# ============================================
# 5. 导出到 CSV
# ============================================
print("\n" + "="*80)
print("5. 数据导出")
print("="*80)

csv_filename = 'items_export.csv'
try:
    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['序号', '商品名', '标题', '原价', '折扣价', '折扣率', '商家', '有货', '商品ID']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items_summary)
    print(f"\n[OK] 已导出到 CSV: {csv_filename}")
    print(f"   - 记录数: {len(items_summary)}")
except Exception as e:
    print(f"[ERROR] CSV 导出失败: {e}")

# ============================================
# 6. 统计总结
# ============================================
print("\n" + "="*80)
print("6. 统计总结")
print("="*80)

summary_text = f"""
[*] 数据统计总结:
   - 总商品数: {data['page']['count']:,} 条
   - 当前页商品: {len(data['dataList'])} 条
   - 商家数: {len(merchants)} 家
   - 有货商品: {stock_status.get('y', 0)} 条
   - 无货商品: {stock_status.get('n', 0)} 条
   - 平均折扣价: {avg_price:,.2f}
   - 平均原价: {avg_market:,.2f}
   - 平均折扣率: {avg_discount:.1f}%
"""

print(summary_text)

# 保存到文件
with open('data_summary.txt', 'w', encoding='utf-8') as f:
    f.write(summary_text)

print("[OK] 统计结果已保存到: data_summary.txt")
print("\n" + "="*80)
