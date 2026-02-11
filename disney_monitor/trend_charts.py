#!/usr/bin/env python3
"""
迪士尼排队趋势图表生成脚本
生成工作日/节假日不同时段的排队趋势图表，帮助规划游玩顺序和时间
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

# 配置
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wait_times.csv")
CHARTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
OUTPUT_REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trend_report.txt")

# 颜色配置
COLORS = {
    '美女与野兽的魔法物语': '#FF6B6B',
    '巨雷山': '#4ECDC4', 
    '小熊维尼猎蜜记': '#FFD166',
    '飞溅山': '#06D6A0',
    '幽灵公馆': '#118AB2'
}

# 星期几中文映射
WEEKDAY_NAMES = {
    0: '星期一',
    1: '星期二', 
    2: '星期三',
    3: '星期四',
    4: '星期五',
    5: '星期六',
    6: '星期日'
}

def setup_directories():
    """创建图表目录"""
    if not os.path.exists(CHARTS_DIR):
        os.makedirs(CHARTS_DIR)
        print(f"创建图表目录: {CHARTS_DIR}")

def load_and_prepare_data():
    """加载并预处理数据"""
    if not os.path.exists(DATA_FILE):
        print(f"数据文件不存在: {DATA_FILE}")
        return None
    
    try:
        df = pd.read_csv(DATA_FILE)
        
        if len(df) == 0:
            print("数据文件为空")
            return None
        
        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp_local'])
        
        # 提取日期和时间信息
        df['date'] = df['timestamp'].dt.date
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        df['day'] = df['timestamp'].dt.day
        df['hour'] = df['timestamp'].dt.hour
        df['minute'] = df['timestamp'].dt.minute
        df['weekday'] = df['timestamp'].dt.weekday  # 0=星期一, 6=星期日
        df['is_weekend'] = df['weekday'].isin([5, 6])  # 星期六、星期日
        
        # 计算时间段的标签
        df['time_period'] = df['hour'].apply(lambda x: get_time_period(x))
        
        # 只保留开放时的数据用于分析
        open_df = df[df['is_open'] == True].copy()
        
        print(f"数据加载成功: {len(df)} 条记录, {len(open_df)} 条开放记录")
        print(f"时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        print(f"包含日期数: {df['date'].nunique()} 天")
        print(f"包含星期: {sorted(df['weekday'].unique())}")
        
        return df, open_df
        
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def get_time_period(hour):
    """将小时转换为时间段标签"""
    if 8 <= hour < 11:
        return "早上 (8-11点)"
    elif 11 <= hour < 14:
        return "中午 (11-14点)"
    elif 14 <= hour < 17:
        return "下午 (14-17点)"
    elif 17 <= hour < 20:
        return "傍晚 (17-20点)"
    else:
        return f"{hour:02d}:00"

def generate_time_series_charts(df, open_df):
    """生成时间序列趋势图"""
    if len(open_df) < 3:
        print("数据不足，无法生成时间序列图（至少需要3条开放记录）")
        return False
    
    # 创建图形
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.suptitle('东京迪士尼乐园排队时间趋势分析', fontsize=16, fontweight='bold')
    
    # 1. 整体时间序列图
    ax = axes[0, 0]
    for attraction in open_df['chinese_name'].unique():
        attr_data = open_df[open_df['chinese_name'] == attraction].copy()
        if len(attr_data) > 1:
            attr_data = attr_data.sort_values('timestamp')
            ax.plot(attr_data['timestamp'], attr_data['wait_time'], 
                   marker='o', linewidth=2, markersize=6, label=attraction,
                   color=COLORS.get(attraction, 'gray'))
    
    ax.set_xlabel('时间')
    ax.set_ylabel('等待时间 (分钟)')
    ax.set_title('各项目等待时间时间序列')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # 格式化x轴时间显示
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. 按小时平均等待时间
    ax = axes[0, 1]
    hourly_avg = open_df.groupby(['chinese_name', 'hour'])['wait_time'].mean().unstack()
    
    if not hourly_avg.empty:
        for attraction in hourly_avg.index:
            hours = hourly_avg.columns
            values = hourly_avg.loc[attraction]
            ax.plot(hours, values, marker='s', linewidth=2, markersize=6, 
                   label=attraction, color=COLORS.get(attraction, 'gray'))
    
    ax.set_xlabel('小时')
    ax.set_ylabel('平均等待时间 (分钟)')
    ax.set_title('按小时平均等待时间')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(range(8, 21, 2))
    
    # 3. 工作日 vs 周末对比
    ax = axes[1, 0]
    weekday_data = open_df[open_df['is_weekend'] == False]
    weekend_data = open_df[open_df['is_weekend'] == True]
    
    categories = []
    weekday_means = []
    weekend_means = []
    
    for attraction in open_df['chinese_name'].unique():
        wk_data = weekday_data[weekday_data['chinese_name'] == attraction]
        we_data = weekend_data[weekend_data['chinese_name'] == attraction]
        
        if len(wk_data) > 0 and len(we_data) > 0:
            categories.append(attraction[:8] + '...' if len(attraction) > 8 else attraction)
            weekday_means.append(wk_data['wait_time'].mean())
            weekend_means.append(we_data['wait_time'].mean())
    
    if categories:
        x = np.arange(len(categories))
        width = 0.35
        
        ax.bar(x - width/2, weekday_means, width, label='工作日', color='#3498db', alpha=0.8)
        ax.bar(x + width/2, weekend_means, width, label='周末', color='#e74c3c', alpha=0.8)
        
        ax.set_xlabel('项目')
        ax.set_ylabel('平均等待时间 (分钟)')
        ax.set_title('工作日 vs 周末等待时间对比')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
    
    # 4. 时间段分析
    ax = axes[1, 1]
    period_data = open_df.groupby(['chinese_name', 'time_period'])['wait_time'].mean().unstack()
    
    if not period_data.empty:
        x = np.arange(len(period_data.index))
        width = 0.2
        periods = period_data.columns
        
        for i, period in enumerate(periods):
            offset = (i - len(periods)/2 + 0.5) * width
            ax.bar(x + offset, period_data[period], width, label=period, alpha=0.8)
        
        ax.set_xlabel('项目')
        ax.set_ylabel('平均等待时间 (分钟)')
        ax.set_title('不同时间段等待时间对比')
        ax.set_xticks(x)
        ax.set_xticklabels([name[:6]+'...' if len(name) > 6 else name for name in period_data.index], 
                          rotation=45, ha='right')
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
    
    # 5. 热力图：等待时间 vs 小时
    ax = axes[2, 0]
    if len(open_df) >= 10:
        heatmap_data = pd.pivot_table(open_df, values='wait_time', 
                                     index='chinese_name', columns='hour', 
                                     aggfunc='mean')
        
        if not heatmap_data.empty:
            im = ax.imshow(heatmap_data.values, aspect='auto', cmap='YlOrRd')
            ax.set_xlabel('小时')
            ax.set_ylabel('项目')
            ax.set_title('等待时间热力图 (小时 × 项目)')
            ax.set_xticks(range(len(heatmap_data.columns)))
            ax.set_xticklabels([str(h) for h in heatmap_data.columns])
            ax.set_yticks(range(len(heatmap_data.index)))
            ax.set_yticklabels(heatmap_data.index, fontsize=8)
            
            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('等待时间 (分钟)')
    
    # 6. 数据量统计
    ax = axes[2, 1]
    record_counts = open_df['chinese_name'].value_counts()
    
    if len(record_counts) > 0:
        colors = [COLORS.get(name, 'gray') for name in record_counts.index]
        ax.bar(range(len(record_counts)), record_counts.values, color=colors, alpha=0.8)
        ax.set_xlabel('项目')
        ax.set_ylabel('数据记录数')
        ax.set_title('各项目数据量统计 (开放状态)')
        ax.set_xticks(range(len(record_counts)))
        ax.set_xticklabels(record_counts.index, rotation=45, ha='right', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 在柱子上添加数量标签
        for i, v in enumerate(record_counts.values):
            ax.text(i, v + 0.1, str(v), ha='center', fontsize=9)
    
    # 调整布局
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # 保存图表
    chart_path = os.path.join(CHARTS_DIR, 'trend_analysis.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"时间序列图表已保存: {chart_path}")
    return True

def generate_individual_attraction_charts(open_df):
    """为每个项目生成单独的详细图表"""
    if len(open_df) < 5:
        print("数据不足，无法生成单独项目图表")
        return False
    
    attractions = open_df['chinese_name'].unique()
    
    for attraction in attractions:
        attr_data = open_df[open_df['chinese_name'] == attraction].copy()
        
        if len(attr_data) < 3:
            continue
        
        # 按时间排序
        attr_data = attr_data.sort_values('timestamp')
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'{attraction} - 详细等待时间分析', fontsize=14, fontweight='bold')
        
        # 1. 时间序列
        ax = axes[0, 0]
        ax.plot(attr_data['timestamp'], attr_data['wait_time'], 
               marker='o', linewidth=2, markersize=6, color=COLORS.get(attraction, 'blue'))
        ax.set_xlabel('时间')
        ax.set_ylabel('等待时间 (分钟)')
        ax.set_title('等待时间时间序列')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 2. 小时分布
        ax = axes[0, 1]
        hourly_data = attr_data.groupby('hour')['wait_time'].agg(['mean', 'count'])
        if len(hourly_data) > 0:
            hours = hourly_data.index
            means = hourly_data['mean']
            counts = hourly_data['count']
            
            bars = ax.bar(hours, means, color=COLORS.get(attraction, 'green'), alpha=0.7)
            ax.set_xlabel('小时')
            ax.set_ylabel('平均等待时间 (分钟)')
            ax.set_title('按小时平均等待时间')
            ax.set_xticks(hours)
            ax.grid(True, alpha=0.3, axis='y')
            
            # 在柱子上添加数量标签
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + 1, 
                       f'n={count}', ha='center', fontsize=8)
        
        # 3. 星期几分布
        ax = axes[1, 0]
        if attr_data['weekday'].nunique() > 1:
            weekday_data = attr_data.groupby('weekday')['wait_time'].agg(['mean', 'count'])
            weekdays = weekday_data.index
            means = weekday_data['mean']
            
            bars = ax.bar(weekdays, means, color=COLORS.get(attraction, 'orange'), alpha=0.7)
            ax.set_xlabel('星期几')
            ax.set_ylabel('平均等待时间 (分钟)')
            ax.set_title('按星期几平均等待时间')
            ax.set_xticks(weekdays)
            ax.set_xticklabels([WEEKDAY_NAMES.get(w, str(w)) for w in weekdays], rotation=45, ha='right')
            ax.grid(True, alpha=0.3, axis='y')
        
        # 4. 箱线图
        ax = axes[1, 1]
        if len(attr_data) >= 5:
            bp = ax.boxplot(attr_data['wait_time'], patch_artist=True)
            bp['boxes'][0].set_facecolor(COLORS.get(attraction, 'purple'))
            bp['boxes'][0].set_alpha(0.7)
            
            ax.set_ylabel('等待时间 (分钟)')
            ax.set_title('等待时间分布统计')
            ax.grid(True, alpha=0.3, axis='y')
            
            # 添加统计信息
            stats_text = f"""统计信息:
最小值: {attr_data['wait_time'].min():.1f}分钟
中位数: {attr_data['wait_time'].median():.1f}分钟
平均值: {attr_data['wait_time'].mean():.1f}分钟
最大值: {attr_data['wait_time'].max():.1f}分钟
标准差: {attr_data['wait_time'].std():.1f}分钟
记录数: {len(attr_data)}"""
            
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 调整布局
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # 保存图表
        safe_name = attraction.replace(' ', '_').replace('(', '').replace(')', '')
        chart_path = os.path.join(CHARTS_DIR, f'{safe_name}_analysis.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  {attraction} 图表已保存")
    
    return True

def generate_recommendation_report(df, open_df):
    """生成游玩建议报告"""
    if len(open_df) < 5:
        print("数据不足，无法生成详细建议报告")
        return "数据不足，请等待更多数据积累后生成建议报告。"
    
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("🏰 东京迪士尼乐园游玩建议报告")
    report_lines.append("=" * 60)
    report_lines.append(f"基于 {len(open_df)} 条开放记录分析")
    report_lines.append(f"数据时间范围: {df['timestamp'].min().strftime('%Y-%m-%d')} 到 {df['timestamp'].max().strftime('%Y-%m-%d')}")
    report_lines.append("")
    
    # 总体建议
    report_lines.append("📊 总体游玩建议:")
    report_lines.append("-" * 40)
    
    # 最佳游玩时间（平均等待最短的小时）
    if open_df['hour'].nunique() > 0:
        best_hour = open_df.groupby('hour')['wait_time'].mean().idxmin()
        best_avg = open_df.groupby('hour')['wait_time'].mean().min()
        report_lines.append(f"• 最佳游玩时段: {best_hour:02d}:00 左右")
        report_lines.append(f"  理由: 该时段平均等待时间最低 ({best_avg:.1f}分钟)")
    
    # 工作日 vs 周末建议
    weekday_data = open_df[open_df['is_weekend'] == False]
    weekend_data = open_df[open_df['is_weekend'] == True]
    
    if len(weekday_data) > 0 and len(weekend_data) > 0:
        weekday_avg = weekday_data['wait_time'].mean()
        weekend_avg = weekend_data['wait_time'].mean()
        
        if weekday_avg < weekend_avg:
            report_lines.append(f"• 建议工作日游玩:")
            report_lines.append(f"  工作日平均等待: {weekday_avg:.1f}分钟 vs 周末: {weekend_avg:.1f}分钟")
        else:
            report_lines.append(f"• 周末等待时间更短:")
            report_lines.append(f"  周末平均等待: {weekend_avg:.1f}分钟 vs 工作日: {weekday_avg:.1f}分钟")
    
    # 各项目具体建议
    report_lines.append("")
    report_lines.append("🎢 各项目游玩建议:")
    report_lines.append("-" * 40)
    
    for attraction in open_df['chinese_name'].unique():
        attr_data = open_df[open_df['chinese_name'] == attraction].copy()
        
        if len(attr_data) >= 3:
            # 最佳游玩时间
            if attr_data['hour'].nunique() > 0:
                best_hour = attr_data.groupby('hour')['wait_time'].mean().idxmin()
                best_avg = attr_data.groupby('hour')['wait_time'].mean().min()
                worst_hour = attr_data.groupby('hour')['wait_time'].mean().idxmax()
                worst_avg = attr_data.groupby('hour')['wait_time'].mean().max()
                
                report_lines.append(f"• {attraction}:")
                report_lines.append(f"  最佳时间: {best_hour:02d}:00 (平均{best_avg:.1f}分钟)")
                report_lines.append(f"  避免时间: {worst_hour:02d}:00 (平均{worst_avg:.1f}分钟)")
                report_lines.append(f"  平均等待: {attr_data['wait_time'].mean():.1f}分钟")
    
    # 游玩顺序建议
    report_lines.append("")
    report_lines.append("🔄 推荐游玩顺序:")
    report_lines.append("-" * 40)
    
    # 按平均等待时间排序
    attraction_stats = []
    for attraction in open_df['chinese_name'].unique():
        attr_data = open_df[open_df['chinese_name'] == attraction].copy()
        if len(attr_data) >= 2:
            avg_wait = attr_data['wait_time'].mean()
            open_rate = len(attr_data) / len(df[df['chinese_name'] == attraction]) * 100
            attraction_stats.append({
                'name': attraction,
                'avg_wait': avg_wait,
                'open_rate': open_rate,
                'record_count': len(attr_data)
            })
    
    if attraction_stats:
        # 先按开放率高排序，再按等待时间短排序
        attraction_stats.sort(key=lambda x: (-x['open_rate'], x['avg_wait']))
        
        report_lines.append("建议顺序 (开放率高 → 等待时间短):")
        for i, stats in enumerate(attraction_stats):
            report_lines.append(f"  {i+1}. {stats['name']}: {stats['avg_wait']:.1f}分钟 (开放率{stats['open_rate']:.1f}%)")
    
    # 数据质量说明
    report_lines.append("")
    report_lines.append("📝 数据质量说明:")
    report_lines.append("-" * 40)
    report_lines.append(f"• 总数据记录数: {len(df)}")
    report_lines.append(f"• 开放记录数: {len(open_df)} ({len(open_df)/len(df)*100:.1f}%)")
    report_lines.append(f"• 覆盖日期数: {df['date'].nunique()} 天")
    report_lines.append(f"• 覆盖小时数: {df['hour'].nunique()} 小时")
    report_lines.append(f"• 建议可靠性: {'低' if len(open_df) < 20 else '中' if len(open_df) < 50 else '高'}")
    report_lines.append("• 随着数据积累，建议会越来越准确")
    
    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append("📅 报告生成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)

def main():
    """主函数"""
    print("开始生成迪士尼排队趋势图表...")
    
    # 设置目录
    setup_directories()
    
    # 加载数据
    data = load_and_prepare_data()
    if data is None:
        sys.exit(1)
    
    df, open_df = data
    
    # 检查数据量
    total_records = len(df)
    open_records = len(open_df)
    
    print(f"数据统计: 总记录{total_records}条, 开放记录{open_records}条")
    
    if open_records < 3:
        print("⚠️  警告: 开放记录不足，图表可能不完整")
        print("建议等待更多数据积累（至少10条开放记录）")
    
    # 生成趋势图表
    charts_generated = False
    if open_records >= 3:
        print("生成综合趋势图表...")
        if generate_time_series_charts(df, open_df):
            charts_generated = True
        
        if open_records >= 5:
            print("生成各项目详细图表...")
            generate_individual_attraction_charts(open_df)
    else:
        print("数据不足，跳过图表生成")
    
    # 生成建议报告
    print("生成游玩建议报告...")
    report = generate_recommendation_report(df, open_df)
    
    # 保存报告
    try:
        with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"建议报告已保存: {OUTPUT_REPORT}")
    except Exception as e:
        print(f"保存报告失败: {e}")
    
    # 打印报告摘要
    print("\n" + "=" * 60)
    print("📋 报告摘要:")
    print("=" * 60)
    
    # 提取关键信息打印
    lines = report.split('\n')
    for line in lines:
        if line.startswith('•') or line.startswith('  ') or '最佳' in line or '建议' in line:
            print(line)
    
    print("=" * 60)
    
    if charts_generated:
        print(f"✅ 趋势图表已生成到目录: {CHARTS_DIR}")
    else:
        print("⚠️  图表未生成（数据不足）")
    
    print(f"📄 详细报告: {OUTPUT_REPORT}")
    print("✅ 分析完成!")

if __name__ == "__main__":
    main()