#!/usr/bin/env python3
"""
A股行业板块底部突破分析
使用baostock获取行业指数数据，进行技术分析
"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import warnings
warnings.filterwarnings('ignore')

# 自定义JSON编码器处理numpy类型
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif pd.isna(obj):
            return None
        else:
            return super(NumpyEncoder, self).default(obj)

# 行业指数代码列表 (上证行业指数)
INDUSTRY_INDICES = {
    'sh.000008': '上证材料',
    'sh.000009': '上证工业', 
    'sh.000010': '上证能源',
    'sh.000011': '上证金融',
    'sh.000012': '上证医药',
    'sh.000013': '上证消费',
    'sh.000014': '上证信息',
    'sh.000015': '上证电信',
    'sh.000016': '上证公用',
    # 可以添加更多指数
}

def login_baostock():
    """登录baostock"""
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return None
    return lg

def logout_baostock(lg):
    """登出baostock"""
    bs.logout()

def get_industry_history(code, name, start_date, end_date):
    """获取行业指数历史数据"""
    try:
        rs = bs.query_history_k_data_plus(
            code, 
            'date,open,high,low,close,volume,amount,turn,pctChg',
            start_date=start_date, 
            end_date=end_date,
            frequency='d', 
            adjustflag='3'
        )
        
        if rs.error_code != '0':
            print(f"获取{name}({code})数据失败: {rs.error_msg}")
            return None
            
        data = rs.get_data()
        if data.empty:
            print(f"{name}({code})无数据")
            return None
            
        # 转换数据类型
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 'pctChg']
        for col in numeric_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce')
            
        data['date'] = pd.to_datetime(data['date'])
        data.set_index('date', inplace=True)
        data.sort_index(inplace=True)
        
        return data
    except Exception as e:
        print(f"获取{name}({code})数据异常: {e}")
        return None

def calculate_technical_indicators(df):
    """计算技术指标"""
    if df is None or df.empty:
        return None
        
    df = df.copy()
    
    # 计算移动平均线
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA60'] = df['close'].rolling(window=60).mean()
    
    # 计算MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    
    # 计算RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算成交量均线
    df['VOLUME_MA5'] = df['volume'].rolling(window=5).mean()
    df['VOLUME_MA10'] = df['volume'].rolling(window=10).mean()
    
    return df

def check_bottom_breakout(df, industry_name, code):
    """检查是否符合底部突破条件"""
    if df is None or len(df) < 60:  # 至少需要60个交易日
        return None
    
    recent_df = df.iloc[-60:]  # 最近60个交易日
    current_price = recent_df['close'].iloc[-1]
    
    # 1. 长期底部确认：较前期高点回调超过20%，且横盘震荡时间≥3个月
    max_price_120 = df['close'].max()  # 最近120个交易日的最高点
    min_price_60 = recent_df['close'].min()
    
    # 计算回调幅度
    if max_price_120 > 0:
        drawdown = (max_price_120 - min_price_60) / max_price_120
    else:
        drawdown = 0
    
    # 2. 量能配合：近期（5-10个交易日）成交量较底部均值放大1.5倍以上
    recent_volume_mean = recent_df['volume'].iloc[-10:].mean()
    bottom_volume_mean = recent_df['volume'].iloc[-20:-10].mean()  # 前10-20交易日作为底部均量
    
    if bottom_volume_mean > 0:
        volume_ratio = recent_volume_mean / bottom_volume_mean
    else:
        volume_ratio = 1
    
    # 3. 价格突破：收盘价突破关键阻力位（前高/均线密集区/下降趋势线）
    # 检查是否突破20日均线
    ma20 = recent_df['MA20'].iloc[-1]
    ma60 = recent_df['MA60'].iloc[-1]
    
    # 突破20日线
    price_break_ma20 = bool(current_price > ma20)  # 确保是Python bool类型
    
    # 突破近期高点（前20日高点）
    recent_high = recent_df['high'].iloc[-20:-1].max()
    price_break_high = bool(current_price > recent_high)
    
    # 4. 趋势转折：MACD金叉或RSI(14)从超卖区(<30)回升至50以上
    macd_current = recent_df['MACD'].iloc[-1]
    macd_signal_current = recent_df['MACD_signal'].iloc[-1]
    macd_previous = recent_df['MACD'].iloc[-2]
    macd_signal_previous = recent_df['MACD_signal'].iloc[-2]
    
    macd_golden_cross = bool(macd_current > macd_signal_current and macd_previous <= macd_signal_previous)
    
    rsi_current = recent_df['RSI'].iloc[-1]
    rsi_previous = recent_df['RSI'].iloc[-5]  # 5天前
    rsi_recovery = bool(rsi_previous < 30 and rsi_current > 50)
    
    # 综合判断
    condition1 = bool(drawdown > 0.20)  # 回调超过20%
    condition2 = bool(volume_ratio > 1.5)  # 成交量放大1.5倍以上
    condition3 = bool(price_break_ma20 or price_break_high)  # 价格突破
    condition4 = bool(macd_golden_cross or rsi_recovery)  # 趋势转折
    
    # 计算突破强度得分 (0-10)
    score = 0
    if condition1: score += 2
    if condition2: score += 3
    if condition3: score += 3
    if condition4: score += 2
    
    # 额外加分项
    if volume_ratio > 2.0: score += 1
    if price_break_ma20 and price_break_high: score += 1
    if macd_golden_cross and rsi_recovery: score += 1
    
    result = {
        'industry_name': industry_name,
        'industry_code': code,
        'current_price': float(round(current_price, 2)),
        'max_price_120': float(round(max_price_120, 2)),
        'min_price_60': float(round(min_price_60, 2)),
        'drawdown': float(round(drawdown * 100, 1)),  # 百分比
        'volume_ratio': float(round(volume_ratio, 2)),
        'price_break_ma20': price_break_ma20,
        'price_break_high': price_break_high,
        'macd_golden_cross': macd_golden_cross,
        'rsi_recovery': rsi_recovery,
        'rsi_current': float(round(rsi_current, 1)),
        'ma20': float(round(ma20, 2)),
        'recent_high': float(round(recent_high, 2)),
        'score': int(score),
        'condition1': condition1,
        'condition2': condition2,
        'condition3': condition3,
        'condition4': condition4,
        'all_conditions_met': bool(condition1 and condition2 and condition3 and condition4)
    }
    
    return result

def main():
    print("=" * 60)
    print("A股行业板块底部突破分析")
    print("=" * 60)
    
    # 日期设置
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')  # 6个月
    
    print(f"分析周期: {start_date} 至 {end_date}")
    print(f"分析行业数量: {len(INDUSTRY_INDICES)}")
    print()
    
    # 登录baostock
    lg = login_baostock()
    if lg is None:
        return
    
    results = []
    
    # 遍历行业指数
    for code, name in INDUSTRY_INDICES.items():
        print(f"正在分析: {name} ({code})", end=" ")
        
        # 获取历史数据
        df = get_industry_history(code, name, start_date, end_date)
        
        if df is None or df.empty:
            print(" [数据获取失败]")
            continue
            
        # 计算技术指标
        df = calculate_technical_indicators(df)
        
        if df is None:
            print(" [技术指标计算失败]")
            continue
            
        # 检查底部突破
        result = check_bottom_breakout(df, name, code)
        
        if result:
            results.append(result)
            if result['all_conditions_met']:
                print(f" [符合底部突破] 得分: {result['score']}")
            else:
                print(f" [不符合] 得分: {result['score']}")
        else:
            print(" [分析失败]")
    
    # 登出
    logout_baostock(lg)
    
    print("\n" + "=" * 60)
    print("分析结果汇总")
    print("=" * 60)
    
    if not results:
        print("未找到符合条件的行业板块")
        return
    
    # 按得分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 输出结果
    for i, result in enumerate(results[:10]):  # 只显示前10
        print(f"\n{i+1}. {result['industry_name']} ({result['industry_code']})")
        print(f"   当前价格: {result['current_price']} | 最大回撤: {result['drawdown']}%")
        print(f"   成交量倍数: {result['volume_ratio']}倍 | RSI当前: {result['rsi_current']}")
        print(f"   突破20日线: {result['price_break_ma20']} | 突破前高: {result['price_break_high']}")
        print(f"   MACD金叉: {result['macd_golden_cross']} | RSI回升: {result['rsi_recovery']}")
        print(f"   综合得分: {result['score']}/10")
        
        if result['all_conditions_met']:
            print("   🟢 符合全部底部突破条件，建议重点关注！")
        else:
            print("   🟡 部分条件未满足，需进一步观察")
    
    # 保存结果到JSON文件
    output_file = "industry_breakout_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    print(f"\n详细结果已保存至: {output_file}")
    
    # 显示符合条件的板块
    breakout_industries = [r for r in results if r['all_conditions_met']]
    if breakout_industries:
        print(f"\n🎯 发现 {len(breakout_industries)} 个完全符合底部突破条件的行业:")
        for ind in breakout_industries:
            print(f"   • {ind['industry_name']} ({ind['industry_code']}) - 得分: {ind['score']}")
    else:
        print(f"\n⚠️ 未发现完全符合全部条件的行业板块")
    
    print("\n" + "=" * 60)
    
    # 返回结果字典
    return {
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_analyzed': len(results),
        'breakout_industries': [r for r in results if r['all_conditions_met']],
        'top_industries': results[:5],  # 前5个高分行业
        'all_results': results
    }

def analyze_all_industries():
    """分析所有行业并返回结果"""
    return main()

if __name__ == "__main__":
    main()