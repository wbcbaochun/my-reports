#!/usr/bin/env python3
"""
行业ETF底部突破分析 (缩短时间窗口版本)
使用2个月数据，针对重点行业ETF
"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# 重点关注的行业ETF (选择交易活跃、代表性强的)
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
    'sh.510500': '中证500ETF',  # 宽基参考
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
        # 转换数据类型
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date')
    except Exception as e:
        print(f"  获取数据异常: {e}")
        return None

def calculate_indicators(df):
    """计算技术指标 (适配短周期)"""
    if df is None or len(df) < 20:
        return df
    
    df = df.copy()
    # 短周期均线
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    
    # MACD (短周期参数)
    exp1 = df['close'].ewm(span=6, adjust=False).mean()   # 缩短为6
    exp2 = df['close'].ewm(span=13, adjust=False).mean()  # 缩短为13
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=5, adjust=False).mean()  # 缩短为5
    
    # RSI (短周期)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(9).mean()  # 9日
    loss = -delta.where(delta < 0, 0).rolling(9).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 布林带 (短周期)
    df['BB_middle'] = df['close'].rolling(10).mean()
    bb_std = df['close'].rolling(10).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    
    return df

def analyze_breakout(df, name, code):
    """分析底部突破情况 (短周期适配)"""
    if df is None or len(df) < 20:
        return None
    
    recent = df.iloc[-20:]  # 只看最近20天
    current = recent.iloc[-1]
    
    # 1. 近期回调幅度 (20日内的回调)
    high_20 = recent['high'].max()
    low_20 = recent['low'].min()
    drawdown = (high_20 - low_20) / high_20 if high_20 > 0 else 0
    
    # 2. 成交量放大 (最近5天 vs 前5天)
    if len(recent) >= 10:
        vol_recent = recent['volume'].iloc[-5:].mean()
        vol_base = recent['volume'].iloc[-10:-5].mean()
        vol_ratio = vol_recent / vol_base if vol_base > 0 else 1
    else:
        vol_ratio = 1
    
    # 3. 价格突破
    break_ma10 = bool(current['close'] > current['MA10'])
    break_ma20 = bool(current['close'] > current['MA20'])
    
    # 4. 突破布林带上轨 (强势信号)
    break_bb_upper = bool(current['close'] > current['BB_upper'])
    
    # 5. 技术指标金叉/反转
    macd_golden = bool(current['MACD'] > current['MACD_signal'] and 
                      recent['MACD'].iloc[-2] <= recent['MACD_signal'].iloc[-2])
    rsi_oversold_recovery = bool(recent['RSI'].iloc[-3] < 40 and current['RSI'] > 50)
    
    # 6. 相对强度 (与沪深300比较)
    # 注意：这里简化处理，实际应该与基准比较
    
    # 得分计算 (总分15分)
    score = 0
    if drawdown > 0.15: score += 2          # 回调>15%
    if drawdown > 0.25: score += 1          # 回调>25% (额外加分)
    if vol_ratio > 1.3: score += 2          # 量能放大>30%
    if vol_ratio > 2.0: score += 1          # 量能放大>100% (额外加分)
    if break_ma10: score += 1
    if break_ma20: score += 2
    if break_bb_upper: score += 2
    if macd_golden: score += 2
    if rsi_oversold_recovery: score += 2
    
    # 突破强度评级
    if score >= 10:
        strength = "强势突破"
    elif score >= 7:
        strength = "中等突破" 
    elif score >= 4:
        strength = "弱突破"
    else:
        strength = "无突破"
    
    return {
        'name': name,
        'code': code,
        'price': float(round(current['close'], 4)),
        'drawdown_pct': float(round(drawdown * 100, 1)),
        'vol_ratio': float(round(vol_ratio, 2)),
        'break_ma10': break_ma10,
        'break_ma20': break_ma20,
        'break_bb_upper': break_bb_upper,
        'macd_golden': macd_golden,
        'rsi_oversold_recovery': rsi_oversold_recovery,
        'rsi_current': float(round(current['RSI'], 1)),
        'ma10': float(round(current['MA10'], 4)),
        'ma20': float(round(current['MA20'], 4)),
        'score': score,
        'strength': strength,
        'data_points': len(df),
        'all_conditions': bool(drawdown > 0.15 and vol_ratio > 1.3 and 
                              (break_ma10 or break_ma20) and 
                              (macd_golden or rsi_oversold_recovery))
    }

def generate_report(results):
    """生成分析报告"""
    report = []
    report.append("=" * 60)
    report.append("行业ETF底部突破分析报告")
    report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"数据周期: 2个月 (短周期分析)")
    report.append(f"分析标的: {len(results)}/{len(KEY_ETFS)} 个行业ETF")
    report.append("=" * 60)
    
    # 按得分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 头部3名
    report.append("\n🎯 **TOP 3 推荐行业ETF**")
    report.append("-" * 40)
    
    for i, r in enumerate(results[:3]):
        report.append(f"\n{i+1}. {r['name']} ({r['code']}) - {r['strength']}")
        report.append(f"   综合得分: {r['score']}/15 | 当前价: {r['price']}")
        report.append(f"   技术特征:")
        report.append(f"   • 近期回调: {r['drawdown_pct']}%")
        report.append(f"   • 量能放大: {r['vol_ratio']}倍")
        report.append(f"   • 突破MA20: {r['break_ma20']} | 突破布林上轨: {r['break_bb_upper']}")
        report.append(f"   • MACD金叉: {r['macd_golden']} | RSI回升: {r['rsi_oversold_recovery']}({r['rsi_current']})")
        if r['all_conditions']:
            report.append("   🚨 **符合全部底部突破条件!**")
    
    # 所有结果汇总
    report.append(f"\n📊 **所有ETF分析结果**")
    report.append("-" * 40)
    
    for i, r in enumerate(results):
        strength_icon = "✅" if r['score'] >= 7 else "⚠️" if r['score'] >= 4 else "❌"
        report.append(f"{strength_icon} {r['name']:12} 得分:{r['score']:2d} 回调:{r['drawdown_pct']:4.1f}% 量比:{r['vol_ratio']:4.2f}")
    
    # 投资建议
    report.append(f"\n💡 **投资建议摘要**")
    report.append("-" * 40)
    
    top_breakout = [r for r in results if r['score'] >= 7]
    if top_breakout:
        report.append(f"1. 重点关注: {', '.join([r['name'] for r in top_breakout[:3]])}")
        report.append(f"2. 突破强度: {top_breakout[0]['strength']} (得分:{top_breakout[0]['score']})")
        report.append(f"3. 建议策略: 分批建仓，设置止损")
    else:
        report.append("暂无强势突破品种，建议观望或关注宽基ETF")
    
    report.append(f"\n⚠️ **风险提示**")
    report.append("-" * 40)
    report.append("1. 基于2个月短周期技术分析，信号稳定性有限")
    report.append("2. ETF数据量有限，建议结合基本面分析")
    report.append("3. 投资有风险，入市需谨慎")
    
    return "\n".join(report)

def main():
    """主函数"""
    print("行业ETF技术分析 (短周期版本)")
    print("=" * 50)
    
    # 登录
    lg = bs.login()
    if lg.error_code != '0':
        print("登录失败")
        return
    
    # 日期设置: 2个月数据
    end_date = '2026-02-10'
    start_date = '2025-12-01'  # 约2.5个月
    
    results = []
    
    for code, name in KEY_ETFS.items():
        print(f"分析: {name:12}...", end="")
        
        df = get_etf_data(code, start_date, end_date)
        if df is None or len(df) < 20:
            print(" 数据不足")
            continue
            
        df = calculate_indicators(df)
        result = analyze_breakout(df, name, code)
        
        if result:
            results.append(result)
            icon = "✅" if result['score'] >= 7 else "⚠️" if result['score'] >= 4 else "❌"
            print(f" {icon} 得分:{result['score']:2d} 数据:{result['data_points']}天")
        else:
            print(" 分析失败")
    
    # 登出
    bs.logout()
    
    if results:
        # 生成报告
        report = generate_report(results)
        print("\n" + report)
        
        # 保存结果
        with open('etf_short_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        
        # 保存报告文本
        with open('etf_short_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
            
        print(f"\n✅ 分析完成，结果已保存")
        print(f"   JSON数据: etf_short_results.json")
        print(f"   文本报告: etf_short_report.txt")
    else:
        print("\n❌ 未能获取足够的ETF数据进行分析")

if __name__ == "__main__":
    main()