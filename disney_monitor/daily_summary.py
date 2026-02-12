#!/usr/bin/env python3
"""
迪士尼排队数据每日汇总脚本
生成多天状况一览报告
"""

import csv
import os
import sys
from datetime import datetime
import pandas as pd
import json

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wait_times.csv")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daily_summary.txt")
OUTPUT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daily_summary.html")
TEMPLATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "report_template.html")

def load_data():
    """加载CSV数据"""
    if not os.path.exists(DATA_FILE):
        print(f"数据文件不存在: {DATA_FILE}")
        return None
    
    try:
        df = pd.read_csv(DATA_FILE)
        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp_local'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        return df
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def generate_daily_summary(df):
    """生成每日汇总报告"""
    if df is None or len(df) == 0:
        return "暂无足够数据生成汇总报告"
    
    report_lines = []
    
    # 报告标题
    report_lines.append("=" * 60)
    report_lines.append("🏰 东京迪士尼乐园排队数据每日汇总报告")
    report_lines.append("=" * 60)
    report_lines.append(f"数据时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
    report_lines.append(f"总数据记录数: {len(df)}")
    report_lines.append(f"监测项目数: {df['chinese_name'].nunique()}")
    report_lines.append("")
    
    # 按日期分析
    dates = sorted(df['date'].unique())
    report_lines.append("📅 按日期汇总:")
    report_lines.append("-" * 40)
    
    for date in dates:
        date_data = df[df['date'] == date]
        date_str = date.strftime('%Y-%m-%d')
        report_lines.append(f"\n📆 {date_str}:")
        
        # 该日总记录数
        total_records = len(date_data)
        report_lines.append(f"  总记录数: {total_records}")
        
        # 按项目分析
        for name in sorted(date_data['chinese_name'].unique()):
            project_data = date_data[date_data['chinese_name'] == name]
            open_data = project_data[project_data['is_open'] == True]
            
            if len(open_data) > 0:
                avg_wait = open_data['wait_time'].mean()
                max_wait = open_data['wait_time'].max()
                min_wait = open_data['wait_time'].min()
                open_count = len(open_data)
                
                report_lines.append(f"  🎢 {name}:")
                report_lines.append(f"    开放率: {open_count}/{len(project_data)} ({open_count/len(project_data)*100:.1f}%)")
                report_lines.append(f"    平均等待: {avg_wait:.1f}分钟")
                report_lines.append(f"    最长等待: {max_wait}分钟")
                report_lines.append(f"    最短等待: {min_wait}分钟")
            else:
                report_lines.append(f"  🎢 {name}: 当日未开放")
    
    # 各项目总体统计
    report_lines.append("\n" + "=" * 60)
    report_lines.append("📊 各项目总体统计:")
    report_lines.append("-" * 40)
    
    for name in sorted(df['chinese_name'].unique()):
        project_data = df[df['chinese_name'] == name]
        open_data = project_data[project_data['is_open'] == True]
        
        if len(open_data) > 0:
            avg_wait = open_data['wait_time'].mean()
            max_wait = open_data['wait_time'].max()
            open_rate = len(open_data) / len(project_data) * 100
            
            # 找到峰值时间
            if len(open_data) > 0:
                peak_time_data = open_data.loc[open_data['wait_time'].idxmax()]
                peak_time = peak_time_data['timestamp'].strftime('%Y-%m-%d %H:%M')
                peak_wait = peak_time_data['wait_time']
            else:
                peak_time = "N/A"
                peak_wait = 0
            
            report_lines.append(f"🎢 {name}:")
            report_lines.append(f"  总记录数: {len(project_data)}")
            report_lines.append(f"  开放率: {open_rate:.1f}% ({len(open_data)}/{len(project_data)})")
            report_lines.append(f"  平均等待: {avg_wait:.1f}分钟")
            report_lines.append(f"  最长等待: {max_wait}分钟")
            report_lines.append(f"  峰值时间: {peak_time} ({peak_wait}分钟)")
        else:
            report_lines.append(f"🎢 {name}: 无开放记录")
    
    # 等待时间趋势分析
    report_lines.append("\n" + "=" * 60)
    report_lines.append("📈 等待时间趋势分析:")
    report_lines.append("-" * 40)
    
    # 按小时分析平均等待时间
    if len(df[df['is_open'] == True]) > 0:
        open_data = df[df['is_open'] == True]
        hourly_stats = open_data.groupby('hour')['wait_time'].agg(['mean', 'max', 'count']).round(1)
        
        report_lines.append("\n按小时平均等待时间:")
        for hour in sorted(hourly_stats.index):
            stats = hourly_stats.loc[hour]
            if stats['count'] > 0:
                hour_str = f"{hour:02d}:00-{hour:02d}:59"
                report_lines.append(f"  {hour_str}: 平均{stats['mean']}分钟 (基于{int(stats['count'])}条记录)")
    
    # 建议游玩时间
    report_lines.append("\n" + "=" * 60)
    report_lines.append("💡 游玩建议:")
    report_lines.append("-" * 40)
    
    if len(df[df['is_open'] == True]) > 0:
        open_data = df[df['is_open'] == True]
        
        # 找到平均等待时间最低的小时
        if not open_data.empty:
            best_hour = open_data.groupby('hour')['wait_time'].mean().idxmin()
            best_avg = open_data.groupby('hour')['wait_time'].mean().min()
            report_lines.append(f"建议游玩时间: {best_hour:02d}:00 左右")
            report_lines.append(f"理由: 该时段平均等待时间最低 ({best_avg:.1f}分钟)")
            
        # 找到最佳项目（平均等待时间最短且开放率高的项目）
        project_stats = []
        for name in df['chinese_name'].unique():
            project_data = df[df['chinese_name'] == name]
            open_data = project_data[project_data['is_open'] == True]
            
            if len(open_data) > 0:
                avg_wait = open_data['wait_time'].mean()
                open_rate = len(open_data) / len(project_data) * 100
                project_stats.append({
                    'name': name,
                    'avg_wait': avg_wait,
                    'open_rate': open_rate,
                    'record_count': len(open_data)
                })
        
        if project_stats:
            # 按平均等待时间排序
            project_stats.sort(key=lambda x: x['avg_wait'])
            report_lines.append(f"\n排队最友好的项目:")
            for i, stats in enumerate(project_stats[:3]):
                report_lines.append(f"  {i+1}. {stats['name']}: 平均{stats['avg_wait']:.1f}分钟 (开放率{stats['open_rate']:.1f}%)")
    else:
        report_lines.append("暂无足够数据提供游玩建议")
    
    report_lines.append("\n" + "=" * 60)
    report_lines.append("📝 报告生成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)

def save_report(report_text):
    """保存报告到文件"""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"报告已保存到: {OUTPUT_FILE}")
        return True
    except Exception as e:
        print(f"保存报告失败: {e}")
        return False

def main():
    """主函数"""
    print("开始生成迪士尼排队数据每日汇总报告...")
    
    # 加载数据
    df = load_data()
    if df is None:
        sys.exit(1)
    
    # 生成报告
    report = generate_daily_summary(df)
    
    # 打印报告
    print("\n" + report)
    
    # 保存报告
    if save_report(report):
        print("\n✅ 报告生成完成!")
    else:
        print("\n⚠️  报告生成完成但保存失败")

if __name__ == "__main__":
    main()