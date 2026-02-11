#!/usr/bin/env python3
"""
精简版行业ETF底部突破分析
"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# 重点关注的行业ETF
KEY_ETFS = {
    'sh.512480': '半导体ETF',
    'sh.512170': '医疗ETF', 
    'sh.512690': '酒ETF',
    'sh.512000': '券商ETF',
    'sh.512400': '有色金属ETF',
    'sh.516160': '新能源ETF',
    'sh.512980': '传媒ETF',  # 包含影视院线
    'sh.512200': '房地产ETF',
    'sh.512660': '军工ETF',
    'sh.515790': '光伏ETF',
    'sh.510300': '沪深300ETF',  # 宽基参考
}

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super().default(obj)

def get_etf_data(code, start_date, end_date):
    """获取ETF数据"""
    try:
        rs = bs.query_history_k_data_plus(
            code,
            "date,code,open,high,low,close,volume,amount",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"
        )
        
        if rs.error_code != '0':
            return None
        
        data = []
        while (rs.error_code == '0') & rs.next():
            data.append(rs.get_row_data())
        
        if not data:
            return None
            
        df = pd.DataFrame(data, columns=rs.fields)
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date')
    except:
        return None

def calculate_indicators(df):
    """计算技术指标"""
    if df is None or len(df) < 20:
        return df
    
    df = df.copy()
    df['MA20'] = df['close'].rolling(20).mean()
    df['MA60'] = df['close'].rolling(60).mean()
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def analyze_breakout(df, name, code):
    """分析突破情况"""
    if df is None or len(df) < 60:
        return None
    
    recent = df.iloc[-60:]
    current = recent.iloc[-1]
    
    # 1. 回调幅度
    max_120 = df['close'].max()
    min_60 = recent['close'].min()
    drawdown = (max_120 - min_60) / max_120 if max_120 > 0 else 0
    
    # 2. 成交量放大
    vol_recent = recent['volume'].iloc[-10:].mean()
    vol_base = recent['volume'].iloc[-20:-10].mean()
    vol_ratio = vol_recent / vol_base if vol_base > 0 else 1
    
    # 3. 价格突破
    break_ma20 = bool(current['close'] > current['MA20'])
    recent_high = recent['high'].iloc[-20:-1].max()
    break_high = bool(current['close'] > recent_high)
    
    # 4. 趋势转折
    macd_golden = bool(current['MACD'] > current['MACD_signal'] and 
                      recent['MACD'].iloc[-2] <= recent['MACD_signal'].iloc[-2])
    rsi_recovery = bool(recent['RSI'].iloc[-5] < 30 and current['RSI'] > 50)
    
    # 得分计算
    score = 0
    if drawdown > 0.20: score += 2
    if vol_ratio > 1.5: score += 3
    if break_ma20 or break_high: score += 3
    if macd_golden or rsi_recovery: score += 2
    
    return {
        'name': name,
        'code': code,
        'price': float(round(current['close'], 4)),
        'drawdown_pct': float(round(drawdown * 100, 1)),
        'vol_ratio': float(round(vol_ratio, 2)),
        'break_ma20': break_ma20,
        'break_high': break_high,
        'macd_golden': macd_golden,
        'rsi_recovery': rsi_recovery,
        'rsi_current': float(round(current['RSI'], 1)),
        'ma20': float(round(current['MA20'], 4)),
        'score': score,
        'all_conditions': bool(drawdown > 0.20 and vol_ratio > 1.5 and 
                              (break_ma20 or break_high) and 
                              (macd_golden or rsi_recovery))
    }

def main():
    """主函数"""
    print("行业ETF技术分析")
    print("=" * 50)
    
    # 登录
    lg = bs.login()
    if lg.error_code != '0':
        print("登录失败")
        return
    
    # 日期设置
    end_date = '2026-02-10'
    start_date = '2025-08-01'  # 6个月
    
    results = []
    
    for code, name in KEY_ETFS.items():
        print(f"分析: {name}...", end="")
        
        df = get_etf_data(code, start_date, end_date)
        if df is None:
            print(" 无数据")
            continue
            
        df = calculate_indicators(df)
        result = analyze_breakout(df, name, code)
        
        if result:
            results.append(result)
            status = "✓" if result['all_conditions'] else "△"
            print(f" {status} 得分:{result['score']}")
        else:
            print(" 分析失败")
    
    # 登出
    bs.logout()
    
    # 排序并输出
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n{'='*50}")
    print(f"分析完成: {len(results)}/{len(KEY_ETFS)} 个ETF")
    
    # 输出前5名
    for i, r in enumerate(results[:5]):
        print(f"\n{i+1}. {r['name']} ({r['code']}) - 得分:{r['score']}/10")
        print(f"   当前价:{r['price']} | 回撤:{r['drawdown_pct']}% | 量比:{r['vol_ratio']}")
        print(f"   突破MA20:{r['break_ma20']} | 突破前高:{r['break_high']}")
        print(f"   MACD金叉:{r['macd_golden']} | RSI回升:{r['rsi_recovery']}({r['rsi_current']})")
        if r['all_conditions']:
            print("   🎯 符合全部底部突破条件!")
    
    # 保存结果
    if results:
        with open('etf_simple_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        print(f"\n结果已保存至: etf_simple_results.json")

if __name__ == "__main__":
    main()