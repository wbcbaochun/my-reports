#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速A股ETF分析 - 使用可用数据进行分析
"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 主要行业ETF列表
ETF_LIST = [
    ('sh.512480', '半导体ETF'),
    ('sh.512170', '医疗ETF'),
    ('sh.516160', '新能源车ETF'),
    ('sh.512600', '主要消费ETF'),
    ('sh.512070', '证券ETF'),
    ('sh.512330', '信息技术ETF'),
    ('sh.512880', '证券ETF(龙头)'),
    ('sh.512980', '传媒ETF'),
]

def get_available_data(etf_code, etf_name):
    """获取可用数据"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    rs = bs.query_history_k_data_plus(
        etf_code,
        "date,open,high,low,close,volume,pctChg",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="3"
    )
    
    if rs.error_code != '0':
        return None, f"错误: {rs.error_msg}"
    
    data = []
    while (rs.error_code == '0') & rs.next():
        data.append(rs.get_row_data())
    
    if not data:
        return None, "无数据"
    
    df = pd.DataFrame(data, columns=['date','open','high','low','close','volume','pctChg'])
    for col in ['open','high','low','close','volume','pctChg']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    return df, f"获取 {len(df)} 条数据"

def simple_analysis(df, etf_code, etf_name):
    """简单技术分析"""
    if df is None or len(df) < 5:
        return None
    
    latest = df.iloc[-1]
    
    # 基本指标
    current_price = latest['close']
    price_change = latest['pctChg']
    
    # 计算简单移动平均
    df['MA5'] = df['close'].rolling(window=min(5, len(df))).mean()
    df['MA10'] = df['close'].rolling(window=min(10, len(df))).mean()
    
    # 价格相对位置 (最近20天)
    lookback = min(20, len(df))
    recent_high = df['high'].iloc[-lookback:].max()
    recent_low = df['low'].iloc[-lookback:].min()
    
    if recent_high > recent_low:
        price_position = (current_price - recent_low) / (recent_high - recent_low) * 100
    else:
        price_position = 50
    
    # 成交量变化
    if len(df) >= 10:
        vol_recent = df['volume'].iloc[-5:].mean()
        vol_previous = df['volume'].iloc[-10:-5].mean()
        volume_ratio = vol_recent / (vol_previous + 1e-8)
    else:
        volume_ratio = 1.0
    
    # 简单突破判断
    above_ma5 = current_price > df['MA5'].iloc[-1] if not pd.isna(df['MA5'].iloc[-1]) else False
    above_ma10 = current_price > df['MA10'].iloc[-1] if not pd.isna(df['MA10'].iloc[-1]) else False
    
    # 趋势判断
    if len(df) >= 3:
        trend_3day = (df['close'].iloc[-1] - df['close'].iloc[-4]) / df['close'].iloc[-4] * 100
    else:
        trend_3day = 0
    
    # 简单评分
    score = 0
    if above_ma5: score += 1
    if above_ma10: score += 1
    if volume_ratio > 1.2: score += 1
    if volume_ratio > 1.5: score += 1
    if price_position < 40: score += 1  # 低位
    if trend_3day > 0: score += 1
    
    # 评级
    if score >= 5:
        rating = "看好"
    elif score >= 3:
        rating = "中性"
    else:
        rating = "谨慎"
    
    return {
        'code': etf_code,
        'name': etf_name,
        'price': round(current_price, 3),
        'change': round(price_change, 2),
        'position': round(price_position, 1),
        'volume_ratio': round(volume_ratio, 2),
        'above_ma5': above_ma5,
        'above_ma10': above_ma10,
        'trend_3day': round(trend_3day, 2),
        'score': score,
        'rating': rating,
        'data_points': len(df)
    }

def main():
    print("🚀 快速A股ETF分析开始...")
    
    # 登录baostock
    lg = bs.login()
    if lg.error_code != '0':
        print(f"❌ 登录失败: {lg.error_msg}")
        return
    
    print("✅ baostock登录成功\n")
    
    results = []
    
    for etf_code, etf_name in ETF_LIST:
        print(f"分析 {etf_name} ({etf_code})...")
        
        df, msg = get_available_data(etf_code, etf_name)
        if df is None:
            print(f"  ⚠️ {msg}")
            continue
        
        analysis = simple_analysis(df, etf_code, etf_name)
        if analysis:
            results.append(analysis)
            print(f"  ✅ 数据: {analysis['data_points']}条, 价格: {analysis['price']}, 评级: {analysis['rating']}")
        else:
            print(f"  ⚠️ 数据不足")
    
    # 生成报告
    if results:
        print(f"\n📊 分析完成，共分析 {len(results)} 个ETF")
        
        # 按评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        report_file = f"reports/快速ETF分析_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("A股行业ETF快速分析报告\n")
            f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"分析样本: {len(results)} 个ETF\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("📈 分析结果:\n\n")
            
            for i, res in enumerate(results, 1):
                f.write(f"{i}. {res['name']} ({res['code']})\n")
                f.write(f"   当前价格: {res['price']}元 | 涨跌: {res['change']}%\n")
                f.write(f"   价格位置: {res['position']}% | 成交量比: {res['volume_ratio']}倍\n")
                f.write(f"   站上5日线: {'✅' if res['above_ma5'] else '❌'} | 站上10日线: {'✅' if res['above_ma10'] else '❌'}\n")
                f.write(f"   3日趋势: {res['trend_3day']}% | 综合评分: {res['score']}/7\n")
                f.write(f"   投资评级: {res['rating']}\n\n")
            
            f.write("⚠️ 风险提示:\n")
            f.write("1. 本分析基于有限数据，仅供参考\n")
            f.write("2. 投资有风险，决策需谨慎\n")
            f.write("3. 数据可能存在延迟\n")
        
        print(f"📄 报告已保存: {report_file}")
        
        # 控制台输出摘要
        print("\n" + "=" * 60)
        print("🏆 推荐排名 (按评分):")
        for i, res in enumerate(results[:3], 1):
            print(f"{i}. {res['name']}: {res['rating']} (评分: {res['score']}, 价格: {res['price']}, 涨跌: {res['change']}%)")
    else:
        print("❌ 没有获取到有效数据")
    
    # 登出
    bs.logout()

if __name__ == "__main__":
    main()