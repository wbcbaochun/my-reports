#!/usr/bin/env python3
"""
行业主题ETF底部突破分析
使用baostock获取ETF数据，进行技术分析
"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import warnings
warnings.filterwarnings('ignore')

# 导入ETF映射
sys.path.append('.')
try:
    from industry_etf_mapping import get_etf_list
    INDUSTRY_ETFS = get_etf_list()
except:
    # 备用列表
    INDUSTRY_ETFS = {
        'sh.512480': '半导体ETF',
        'sh.512170': '医疗ETF',
        'sh.512690': '酒ETF',
        'sh.512000': '券商ETF',
        'sh.512400': '有色金属ETF',
        'sh.516160': '新能源ETF',
        'sh.512980': '传媒ETF',
        'sh.512200': '房地产ETF',
        'sh.512660': '军工ETF',
        'sh.515790': '光伏ETF',
    }

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

def login_baostock():
    """登录baostock"""
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return False
    print("login success!")
    return True

def logout_baostock():
    """登出baostock"""
    bs.logout()
    print("logout success!")

def get_etf_data(code, name, start_date, end_date):
    """获取ETF历史数据"""
    try:
        rs = bs.query_history_k_data_plus(
            code,
            "date,code,open,high,low,close,volume",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"  # 复权方式(3:后复权)
        )
        
        if rs.error_code != '0':
            print(f"  {name}({code})数据获取失败: {rs.error_msg}")
            return None
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if len(data_list) == 0:
            print(f"  {name}({code})无数据")
            return None
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 数据类型转换
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    except Exception as e:
        print(f"  获取{name}({code})数据异常: {e}")
        return None

def calculate_technical_indicators(df):
    """计算技术指标"""
    if df is None or len(df) < 60:
        return df
    
    # 计算移动平均线
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA60'] = df['close'].rolling(window=60).mean()
    
    # 计算MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 计算RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def check_bottom_breakout(df, etf_name, code):
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
    price_break_ma20 = bool(current_price > ma20)
    
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
        'etf_name': etf_name,
        'etf_code': code,
        'current_price': float(round(current_price, 4)),
        'max_price_120': float(round(max_price_120, 4)),
        'min_price_60': float(round(min_price_60, 4)),
        'drawdown': float(round(drawdown * 100, 1)),  # 百分比
        'volume_ratio': float(round(volume_ratio, 2)),
        'price_break_ma20': price_break_ma20,
        'price_break_high': price_break_high,
        'macd_golden_cross': macd_golden_cross,
        'rsi_recovery': rsi_recovery,
        'rsi_current': float(round(rsi_current, 1)),
        'ma20': float(round(ma20, 4)),
        'recent_high': float(round(recent_high, 4)),
        'score': int(score),
        'condition1': condition1,
        'condition2': condition2,
        'condition3': condition3,
        'condition4': condition4,
        'all_conditions_met': bool(condition1 and condition2 and condition3 and condition4)
    }
    
    return result

def main():
    """主函数"""
    print("=" * 60)
    print("行业主题ETF底部突破分析")
    print("=" * 60)
    
    # 设置分析周期
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')  # 6个月
    
    print(f"分析周期: {start_date} 至 {end_date}")
    print(f"分析ETF数量: {len(INDUSTRY_ETFS)}")
    print()
    
    # 登录baostock
    if not login_baostock():
        return
    
    results = []
    analyzed_count = 0
    
    # 分析每个ETF
    for code, name in INDUSTRY_ETFS.items():
        print(f"正在分析: {name} ({code})", end="", flush=True)
        
        # 获取数据
        df = get_etf_data(code, name, start_date, end_date)
        
        if df is not None:
            # 计算技术指标
            df = calculate_technical_indicators(df)
            
            # 检查底部突破
            result = check_bottom_breakout(df, name, code)
            
            if result:
                results.append(result)
                status = " [不符合]" if not result['all_conditions_met'] else " [符合]"
                print(f"{status} 得分: {result['score']}")
                analyzed_count += 1
            else:
                print(" [分析失败]")
        else:
            print(" [数据获取失败]")
    
    # 登出
    logout_baostock()
    
    if not results:
        print("\n⚠️ 未获取到有效分析结果")
        return
    
    # 按得分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n" + "=" * 60)
    print("分析结果汇总")
    print("=" * 60)
    print(f"成功分析: {analyzed_count}/{len(INDUSTRY_ETFS)} 个ETF")
    
    # 显示前20个结果
    top_n = min(20, len(results))
    for i, result in enumerate(results[:top_n]):
        print(f"\n{i+1}. {result['etf_name']} ({result['etf_code']})")
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
    output_file = "etf_breakout_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    print(f"\n详细结果已保存至: {output_file}")
    
    # 显示符合条件的ETF
    breakout_etfs = [r for r in results if r['all_conditions_met']]
    if breakout_etfs:
        print(f"\n🎯 发现 {len(breakout_etfs)} 个完全符合底部突破条件的ETF:")
        for etf in breakout_etfs:
            print(f"   • {etf['etf_name']} ({etf['etf_code']}) - 得分: {etf['score']}")
    else:
        print(f"\n⚠️ 未发现完全符合全部条件的ETF")
    
    # 显示前3名推荐
    print(f"\n🏆 推荐排名前3的ETF:")
    for i, result in enumerate(results[:3]):
        print(f"{i+1}. {result['etf_name']} ({result['etf_code']}) - 得分: {result['score']}/10")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()