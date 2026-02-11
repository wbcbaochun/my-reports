#!/usr/bin/env python3
"""
查看迪士尼排队监测数据的脚本
"""

import csv
import os
import sys
from datetime import datetime
import pandas as pd

CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wait_times.csv")

def show_recent_data(limit=10):
    """显示最近的数据记录"""
    if not os.path.exists(CSV_FILE):
        print("数据文件不存在，尚未记录任何数据")
        return
    
    try:
        # 使用pandas读取数据（如果可用）
        try:
            import pandas as pd
            df = pd.read_csv(CSV_FILE)
            print(f"数据文件: {CSV_FILE}")
            print(f"总记录数: {len(df)}")
            print(f"时间范围: {df['timestamp_local'].min()} 到 {df['timestamp_local'].max()}")
            print(f"监测项目数: {df['attraction_id'].nunique()}")
            
            print("\n最近记录:")
            recent = df.tail(limit)
            for _, row in recent.iterrows():
                status = "✅ 开放" if row['is_open'] else "❌ 关闭"
                print(f"{row['timestamp_local']} - {row['chinese_name']}: {row['wait_time']}分钟 {status}")
            
            print("\n各项目最新状态:")
            latest = df.sort_values('timestamp_local').groupby('chinese_name').last().reset_index()
            for _, row in latest.iterrows():
                status = "✅ 开放" if row['is_open'] else "❌ 关闭"
                print(f"{row['chinese_name']}: {row['wait_time']}分钟 {status}")
                
        except ImportError:
            # 回退到纯CSV读取
            print("Pandas不可用，使用基础CSV读取")
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                print(f"总记录数: {len(rows)}")
                
                print("\n最近记录:")
                for row in rows[-limit:]:
                    status = "✅ 开放" if row['is_open'].lower() == 'true' else "❌ 关闭"
                    print(f"{row['timestamp_local']} - {row['chinese_name']}: {row['wait_time']}分钟 {status}")
                    
    except Exception as e:
        print(f"读取数据时出错: {e}")

def show_summary():
    """显示数据摘要"""
    if not os.path.exists(CSV_FILE):
        print("数据文件不存在")
        return
    
    try:
        import pandas as pd
        df = pd.read_csv(CSV_FILE)
        
        # 转换为datetime
        df['timestamp'] = pd.to_datetime(df['timestamp_local'])
        
        print("=== 迪士尼排队监测数据摘要 ===")
        print(f"数据文件: {CSV_FILE}")
        print(f"记录时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        print(f"总数据点: {len(df)}")
        print(f"监测项目: {', '.join(df['chinese_name'].unique())}")
        
        print("\n各项目数据统计:")
        for name in df['chinese_name'].unique():
            project_data = df[df['chinese_name'] == name]
            open_data = project_data[project_data['is_open'] == True]
            
            if len(open_data) > 0:
                avg_wait = open_data['wait_time'].mean()
                max_wait = open_data['wait_time'].max()
                min_wait = open_data['wait_time'].min()
                print(f"\n{name}:")
                print(f"  开放记录数: {len(open_data)}/{len(project_data)}")
                print(f"  平均等待: {avg_wait:.1f}分钟")
                print(f"  最长等待: {max_wait}分钟")
                print(f"  最短等待: {min_wait}分钟")
            else:
                print(f"\n{name}: 尚无开放记录")
                
    except ImportError:
        print("需要pandas库进行摘要分析，请安装: pip install pandas")
    except Exception as e:
        print(f"生成摘要时出错: {e}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "summary":
            show_summary()
        elif sys.argv[1].isdigit():
            show_recent_data(int(sys.argv[1]))
        else:
            print("用法: python3 check_data.py [summary|数量]")
            print("示例:")
            print("  python3 check_data.py          # 显示最近10条记录")
            print("  python3 check_data.py 20       # 显示最近20条记录")
            print("  python3 check_data.py summary  # 显示数据摘要")
    else:
        show_recent_data(10)

if __name__ == "__main__":
    main()