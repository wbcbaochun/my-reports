#!/usr/bin/env python3
"""
传媒ETF成分股分析
分析十大重仓股的技术走势
"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 传媒ETF十大重仓股 (数据来源: 新浪财经, 2025-12-31)
TOP_HOLDINGS = [
    {'code': 'sz.002027', 'name': '分众传媒', 'weight': 9.33},
    {'code': 'sz.002558', 'name': '巨人网络', 'weight': 7.34},
    {'code': 'sz.300058', 'name': '蓝色光标', 'weight': 5.06},
    {'code': 'sz.002195', 'name': '岩山科技', 'weight': 5.04},
    {'code': 'sz.002517', 'name': '恺英网络', 'weight': 4.68},
    {'code': 'sz.002131', 'name': '利欧股份', 'weight': 4.65},
    {'code': 'sz.300418', 'name': '昆仑万维', 'weight': 4.59},
    {'code': 'sz.002555', 'name': '三七互娱', 'weight': 4.58},
    {'code': 'sz.300251', 'name': '光线传媒', 'weight': 3.01},
    {'code': 'sz.300002', 'name': '神州泰岳', 'weight': 2.84},
]

def get_stock_data(code, start_date, end_date):
    """获取股票数据"""
    try:
        rs = bs.query_history_k_data_plus(
            code,
            "date,code,open,high,low,close,volume,amount,turn",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"
        )
        
        if rs.error_code != '0':
            print(f"  获取失败: {rs.error_msg}")
            return None
        
        data = []
        while (rs.error_code == '0') & rs.next():
            data.append(rs.get_row_data())
        
        if not data:
            return None
            
        df = pd.DataFrame(data, columns=rs.fields)
        # 转换数据类型
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date')
    except Exception as e:
        print(f"  异常: {e}")
        return None

def analyze_stock_trend(df, name, weight):
    """分析股票趋势"""
    if df is None or len(df) < 20:
        return None
    
    recent = df.iloc[-20:]  # 最近20天
    current = recent.iloc[-1]
    
    # 计算技术指标（确保数据足够）
    if len(df) >= 20:
        ma20 = df['close'].rolling(20).mean().iloc[-1]
    else:
        ma20 = float('nan')
    
    if len(df) >= 10:
        ma10 = df['close'].rolling(10).mean().iloc[-1]
    else:
        ma10 = float('nan')
    
    # 近期表现
    price_change_5d = (current['close'] / df['close'].iloc[-5] - 1) * 100
    price_change_20d = (current['close'] / df['close'].iloc[-20] - 1) * 100
    
    # 成交量变化
    if len(recent) >= 10:
        vol_recent = recent['volume'].iloc[-5:].mean()
        vol_base = recent['volume'].iloc[-10:-5].mean()
        vol_ratio = vol_recent / vol_base if vol_base > 0 else 1
    else:
        vol_ratio = 1
    
    # 突破判断
    break_ma20 = bool(current['close'] > ma20 and not np.isnan(ma20))
    recent_high = recent['high'].iloc[-10:-1].max() if len(recent) >= 10 else 0
    break_high = bool(current['close'] > recent_high)
    
    # 相对强度评分
    score = 0
    if price_change_5d > 5: score += 2
    if price_change_20d > 10: score += 3
    if vol_ratio > 1.5: score += 2
    if break_ma20: score += 2
    if break_high: score += 3
    
    return {
        'name': name,
        'code': df['code'].iloc[-1],
        'weight': weight,
        'price': float(round(current['close'], 2)),
        'change_5d': float(round(price_change_5d, 1)),
        'change_20d': float(round(price_change_20d, 1)),
        'vol_ratio': float(round(vol_ratio, 2)),
        'break_ma20': break_ma20,
        'break_high': break_high,
        'ma20': float(round(ma20, 2)) if not np.isnan(ma20) else 0,
        'score': score,
        'strength': '强势' if score >= 8 else '中等' if score >= 5 else '弱势'
    }

def main():
    """主函数"""
    print("传媒ETF成分股分析")
    print("=" * 50)
    
    # 登录
    lg = bs.login()
    if lg.error_code != '0':
        print("登录失败")
        return
    
    # 日期设置: 2个月数据
    end_date = '2026-02-10'
    start_date = '2025-12-01'
    
    results = []
    total_weight = sum(h['weight'] for h in TOP_HOLDINGS)
    
    print(f"分析 {len(TOP_HOLDINGS)} 只重仓股 (总权重: {total_weight:.1f}%)")
    print("-" * 50)
    
    for stock in TOP_HOLDINGS:
        print(f"分析: {stock['name']}...", end="")
        
        df = get_stock_data(stock['code'], start_date, end_date)
        if df is None or len(df) < 20:
            print(" 数据不足")
            continue
            
        result = analyze_stock_trend(df, stock['name'], stock['weight'])
        
        if result:
            results.append(result)
            icon = "✅" if result['score'] >= 8 else "⚠️" if result['score'] >= 5 else "❌"
            print(f" {icon} 得分:{result['score']} {result['strength']}")
        else:
            print(" 分析失败")
    
    # 登出
    bs.logout()
    
    if results:
        # 按得分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n{'='*50}")
        print("成分股技术分析汇总")
        print(f"{'='*50}")
        
        # 计算加权得分
        weighted_score = sum(r['score'] * r['weight'] for r in results) / sum(r['weight'] for r in results)
        
        # 统计强势股比例
        strong_stocks = [r for r in results if r['score'] >= 8]
        medium_stocks = [r for r in results if r['score'] >= 5]
        
        print(f"成分股整体加权得分: {weighted_score:.1f}/12")
        print(f"强势股({len(strong_stocks)}只): {', '.join([s['name'] for s in strong_stocks])}")
        print(f"中等股({len(medium_stocks)}只): {', '.join([s['name'] for s in medium_stocks])}")
        print(f"弱势股({len(results)-len(medium_stocks)}只)")
        
        print(f"\n{'='*50}")
        print("📊 详细分析结果")
        print(f"{'='*50}")
        
        for i, r in enumerate(results[:5]):  # 显示前5名
            print(f"\n{i+1}. {r['name']} (权重:{r['weight']}%) - {r['strength']}")
            print(f"   当前价: {r['price']} | 5日涨跌: {r['change_5d']}% | 20日涨跌: {r['change_20d']}%")
            print(f"   量比: {r['vol_ratio']} | 突破MA20: {r['break_ma20']} | 突破前高: {r['break_high']}")
            print(f"   MA20: {r['ma20']} | 技术得分: {r['score']}/12")
        
        # 行业整体判断
        print(f"\n{'='*50}")
        print("💡 行业整体判断")
        print(f"{'='*50}")
        
        if weighted_score >= 7:
            print("✅ 成分股整体表现强劲，传媒ETF突破有基本面支撑")
        elif weighted_score >= 5:
            print("⚠️ 成分股表现分化，传媒ETF突破信号需谨慎验证")
        else:
            print("❌ 成分股普遍弱势，传媒ETF突破可能为假突破")
        
        # 投资建议
        print(f"\n{'='*50}")
        print("🎯 投资建议")
        print(f"{'='*50}")
        
        if strong_stocks:
            print(f"1. 重点关注强势股: {', '.join([s['name'] for s in strong_stocks[:3]])}")
            print(f"2. 观察中等股: {', '.join([s['name'] for s in medium_stocks[:3]])}")
            print(f"3. 回避弱势股: {', '.join([r['name'] for r in results if r['score'] < 5][:3])}")
        
        print(f"\n4. 传媒ETF权重股整体技术得分: {weighted_score:.1f}/12")
        print(f"5. 建议结合行业新闻和政策面进一步验证")
        
        # 保存结果
        import json
        with open('media_stocks_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 分析结果已保存至: media_stocks_analysis.json")
    else:
        print("\n❌ 未能获取足够的成分股数据")

if __name__ == "__main__":
    main()