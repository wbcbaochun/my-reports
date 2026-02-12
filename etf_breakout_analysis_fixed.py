#!/usr/bin/env python3
"""
行业主题ETF底部突破分析 (修复版)
修复数据量不足问题，增加细分行业ETF覆盖
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

# 细分行业ETF映射 (补充更多细分行业)
SEGMENT_ETFS = {
    # 影视院线相关
    'sh.512980': '传媒ETF',  # 包含影视内容
    'sz.159805': '传媒ETF',
    'sh.515000': '科技ETF',  # 包含数字媒体
    'sh.515880': '通信ETF',  # 包含5G应用
    
    # 游戏娱乐
    'sh.515170': '游戏ETF',
    'sz.159869': '游戏ETF',
    
    # 教育
    'sh.516500': '教育ETF',
    
    # 旅游酒店
    'sh.513200': '旅游ETF',
    'sz.159766': '旅游ETF',
    
    # 体育产业
    'sh.515030': '体育ETF',
    
    # 环保新能源细分
    'sh.516790': '碳中和ETF',
    'sh.159885': '环保ETF',
    'sh.516780': '稀土ETF',
    'sh.159755': '锂电池ETF',
    
    # 医疗细分
    'sh.512290': '生物医药ETF',
    'sh.512220': '医疗器械ETF',
    'sh.515950': '创新药ETF',
    
    # 科技细分
    'sh.515860': '信息技术ETF',
    'sh.515770': '人工智能ETF',
    'sh.515050': '5GETF',
    'sh.159939': '信息技术ETF',
    
    # 消费细分
    'sz.159996': '家电ETF',
    'sh.515650': '消费50ETF',
    'sh.517080': '食品饮料ETF',
    'sh.512600': '主要消费ETF',
    
    # 金融细分
    'sh.512880': '证券ETF',
    'sh.512070': '保险主题ETF',
    'sh.515000': '银行ETF',
    
    # 周期细分
    'sh.515220': '煤炭ETF',
    'sh.515210': '钢铁ETF',
    'sh.512710': '军工龙头ETF',
}

# 合并两个ETF列表
ALL_ETFS = {**INDUSTRY_ETFS, **SEGMENT_ETFS}

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

def calculate_technical_indicators(df, min_days=20):
    """计算技术指标，调整最小数据要求"""
    if df is None or len(df) < min_days:
        return df
    
    # 计算移动平均线（根据可用数据调整窗口）
    available_days = len(df)
    ma_window = min(20, available_days // 3)  # 自适应窗口
    
    if ma_window >= 5:
        df['MA20'] = df['close'].rolling(window=ma_window).mean()
    
    # 如果数据足够，计算60日均线
    if available_days >= 30:
        ma60_window = min(60, available_days // 2)
        df['MA60'] = df['close'].rolling(window=ma60_window).mean()
    
    # 计算MACD（需要至少26个数据点）
    if available_days >= 26:
        exp1 = df['close'].ewm(span=min(12, available_days//2), adjust=False).mean()
        exp2 = df['close'].ewm(span=min(26, available_days//2), adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=min(9, available_days//3), adjust=False).mean()
    
    # 计算RSI
    if available_days >= 14:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def check_bottom_breakout(df, etf_name, code):
    """检查是否符合底部突破条件，适应不同数据量"""
    if df is None:
        return None
    
    available_days = len(df)
    
    # 根据数据量调整分析窗口
    analysis_window = min(60, available_days)
    if analysis_window < 20:  # 至少需要20天数据
        print(f"  数据不足({available_days}天)，跳过深度分析")
        return create_basic_result(df, etf_name, code)
    
    recent_df = df.iloc[-analysis_window:]  # 最近数据
    current_price = recent_df['close'].iloc[-1]
    
    # 1. 长期底部确认：较前期高点回调
    lookback_window = min(120, available_days)
    max_price = df['close'].iloc[-lookback_window:].max()
    min_price = recent_df['close'].min()
    
    # 计算回调幅度
    if max_price > 0:
        drawdown = (max_price - min_price) / max_price
    else:
        drawdown = 0
    
    # 2. 量能配合：近期成交量较底部均值放大
    if available_days >= 20:
        recent_volume_mean = recent_df['volume'].iloc[-10:].mean()
        bottom_volume_mean = recent_df['volume'].iloc[-20:-10].mean() if available_days >= 20 else recent_volume_mean
    else:
        recent_volume_mean = recent_df['volume'].mean()
        bottom_volume_mean = recent_volume_mean
    
    if bottom_volume_mean > 0:
        volume_ratio = recent_volume_mean / bottom_volume_mean
    else:
        volume_ratio = 1
    
    # 3. 价格突破：收盘价突破关键阻力位
    price_break_ma20 = False
    price_break_high = False
    
    if 'MA20' in df.columns and not pd.isna(df['MA20'].iloc[-1]):
        ma20 = df['MA20'].iloc[-1]
        price_break_ma20 = bool(current_price > ma20)
    
    # 突破近期高点（前N日高点）
    lookback_high = min(20, analysis_window - 1)
    if lookback_high > 1:
        recent_high = recent_df['high'].iloc[-lookback_high:-1].max()
        price_break_high = bool(current_price > recent_high)
    
    # 4. 趋势转折：技术指标信号
    macd_golden_cross = False
    rsi_recovery = False
    rsi_current = 50
    
    if 'MACD' in df.columns and 'MACD_signal' in df.columns:
        if len(df) >= 2:
            macd_current = df['MACD'].iloc[-1]
            macd_signal_current = df['MACD_signal'].iloc[-1]
            macd_previous = df['MACD'].iloc[-2]
            macd_signal_previous = df['MACD_signal'].iloc[-2]
            macd_golden_cross = bool(macd_current > macd_signal_current and macd_previous <= macd_signal_previous)
    
    if 'RSI' in df.columns:
        rsi_current = df['RSI'].iloc[-1]
        if len(df) >= 5:
            rsi_previous = df['RSI'].iloc[-5]
            rsi_recovery = bool(rsi_previous < 30 and rsi_current > 50)
    
    # 综合判断（调整条件以适应数据量）
    condition1 = bool(drawdown > 0.15)  # 回调超过15%
    condition2 = bool(volume_ratio > 1.3)  # 成交量放大1.3倍以上
    condition3 = bool(price_break_ma20 or price_break_high)  # 价格突破
    condition4 = bool(macd_golden_cross or rsi_recovery)  # 趋势转折
    
    # 计算突破强度得分 (0-10)，根据满足的条件数
    base_score = 0
    if condition1: base_score += 2
    if condition2: base_score += 2  # 降低权重
    if condition3: base_score += 3
    if condition4: base_score += 2
    
    # 额外加分项（降低要求）
    if volume_ratio > 1.8: base_score += 1
    if price_break_ma20 and price_break_high: base_score += 1
    if macd_golden_cross and rsi_recovery: base_score += 1
    
    # 数据质量调整（数据越多，可信度越高）
    data_quality_factor = min(1.0, available_days / 60.0)
    final_score = min(10, base_score * (0.5 + 0.5 * data_quality_factor))
    
    result = {
        'etf_name': etf_name,
        'etf_code': code,
        'current_price': float(round(current_price, 4)),
        'max_price': float(round(max_price, 4)),
        'min_price': float(round(min_price, 4)),
        'drawdown': float(round(drawdown * 100, 1)),  # 百分比
        'volume_ratio': float(round(volume_ratio, 2)),
        'price_break_ma20': price_break_ma20,
        'price_break_high': price_break_high,
        'macd_golden_cross': macd_golden_cross,
        'rsi_recovery': rsi_recovery,
        'rsi_current': float(round(rsi_current, 1)),
        'ma20': float(round(df['MA20'].iloc[-1], 4)) if 'MA20' in df.columns and not pd.isna(df['MA20'].iloc[-1]) else None,
        'recent_high': float(round(recent_high, 4)) if 'recent_high' in locals() else None,
        'score': float(round(final_score, 1)),
        'condition1': condition1,
        'condition2': condition2,
        'condition3': condition3,
        'condition4': condition4,
        'all_conditions_met': bool(condition1 and condition2 and condition3 and condition4),
        'data_days': available_days,
        'analysis_window': analysis_window
    }
    
    return result

def create_basic_result(df, etf_name, code):
    """创建基本结果（当数据不足时）"""
    if df is None or len(df) == 0:
        return None
    
    current_price = df['close'].iloc[-1]
    price_change = 0
    
    if len(df) >= 2:
        prev_price = df['close'].iloc[-2]
        if prev_price > 0:
            price_change = (current_price - prev_price) / prev_price * 100
    
    # 计算简单均线
    ma_window = min(5, len(df))
    if ma_window >= 3:
        ma_value = df['close'].iloc[-ma_window:].mean()
        above_ma = current_price > ma_value
    else:
        ma_value = None
        above_ma = False
    
    # 简单成交量分析
    if len(df) >= 5:
        recent_volume = df['volume'].iloc[-5:].mean()
        prev_volume = df['volume'].iloc[-10:-5].mean() if len(df) >= 10 else recent_volume
        volume_ratio = recent_volume / prev_volume if prev_volume > 0 else 1
    else:
        volume_ratio = 1
    
    # 简单得分
    score = 0
    if above_ma: score += 2
    if volume_ratio > 1.2: score += 2
    if price_change > 0: score += 1
    
    return {
        'etf_name': etf_name,
        'etf_code': code,
        'current_price': float(round(current_price, 4)),
        'price_change_pct': float(round(price_change, 2)),
        'above_ma': above_ma,
        'ma_value': float(round(ma_value, 4)) if ma_value else None,
        'volume_ratio': float(round(volume_ratio, 2)),
        'score': score,
        'all_conditions_met': False,
        'data_days': len(df),
        'analysis_type': 'basic'
    }

def main():
    """主函数"""
    print("=" * 70)
    print("行业主题ETF底部突破分析 (修复版 - 支持细分行业)")
    print("=" * 70)
    
    # 设置分析周期 - 延长至1年以确保足够数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 1年
    
    print(f"分析周期: {start_date} 至 {end_date}")
    print(f"分析ETF总数: {len(ALL_ETFS)} (含细分行业)")
    print()
    
    # 登录baostock
    if not login_baostock():
        return
    
    results = []
    analyzed_count = 0
    success_count = 0
    
    # 分析每个ETF
    etf_items = list(ALL_ETFS.items())
    for idx, (code, name) in enumerate(etf_items):
        print(f"[{idx+1:3d}/{len(etf_items)}] 分析: {name} ({code})", end="", flush=True)
        
        # 获取数据
        df = get_etf_data(code, name, start_date, end_date)
        
        if df is not None:
            analyzed_count += 1
            
            # 计算技术指标
            df = calculate_technical_indicators(df)
            
            # 检查底部突破
            result = check_bottom_breakout(df, name, code)
            
            if result:
                results.append(result)
                if result.get('analysis_type') == 'basic':
                    print(f" [基础分析] 得分: {result['score']:.1f} (数据: {result['data_days']}天)")
                else:
                    status = " [不符合]" if not result['all_conditions_met'] else " [符合]"
                    print(f"{status} 得分: {result['score']:.1f} (数据: {result['data_days']}天)")
                success_count += 1
            else:
                print(" [分析失败]")
        else:
            print(" [数据获取失败]")
    
    # 登出
    logout_baostock()
    
    print("\n" + "=" * 70)
    print("分析完成汇总")
    print("=" * 70)
    print(f"尝试分析: {len(etf_items)} 个ETF")
    print(f"成功获取数据: {analyzed_count} 个")
    print(f"完成分析: {success_count} 个")
    
    if not results:
        print("\n⚠️ 未获取到有效分析结果")
        return
    
    # 按得分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 显示前20个结果
    top_n = min(20, len(results))
    print(f"\n📊 前{top_n}个ETF分析结果:")
    
    for i, result in enumerate(results[:top_n]):
        analysis_type = result.get('analysis_type', 'advanced')
        print(f"\n{i+1:2d}. {result['etf_name']} ({result['etf_code']})")
        print(f"   当前价格: {result['current_price']} | 得分: {result['score']:.1f}/10")
        
        if analysis_type == 'advanced':
            print(f"   最大回撤: {result['drawdown']}% | 成交量倍数: {result['volume_ratio']}倍")
            print(f"   突破20日线: {result['price_break_ma20']} | 突破前高: {result['price_break_high']}")
            print(f"   MACD金叉: {result['macd_golden_cross']} | RSI当前: {result['rsi_current']}")
        else:
            if result.get('price_change_pct') is not None:
                print(f"   涨跌幅: {result['price_change_pct']}% | 成交量倍数: {result['volume_ratio']}倍")
            if result.get('ma_value'):
                print(f"   是否在均线上方: {result['above_ma']} | 均线值: {result['ma_value']}")
        
        print(f"   数据天数: {result['data_days']} | 分析类型: {analysis_type}")
        
        if result.get('all_conditions_met', False):
            print("   🟢 符合全部底部突破条件，建议重点关注！")
        elif result['score'] >= 6:
            print("   🟡 得分较高，值得关注")
        elif result['score'] >= 4:
            print("   🔵 中等得分，继续观察")
        else:
            print("   ⚫ 得分较低，保持关注")
    
    # 保存结果到JSON文件
    output_file = "etf_breakout_results_fixed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    print(f"\n💾 详细结果已保存至: {output_file}")
    
    # 生成细分行业分类统计
    print("\n📋 细分行业ETF统计:")
    categories = {}
    for result in results:
        etf_name = result['etf_name']
        # 简单分类
        if '半导体' in etf_name or '芯片' in etf_name:
            cat = '半导体/芯片'
        elif '医药' in etf_name or '医疗' in etf_name or '健康' in etf_name:
            cat = '医药医疗'
        elif '新能源' in etf_name or '光伏' in etf_name or '电池' in etf_name:
            cat = '新能源'
        elif '消费' in etf_name or '酒' in etf_name or '食品' in etf_name:
            cat = '消费'
        elif '科技' in etf_name or '信息' in etf_name or '人工' in etf_name or '5G' in etf_name:
            cat = '科技'
        elif '金融' in etf_name or '证券' in etf_name or '银行' in etf_name or '保险' in etf_name:
            cat = '金融'
        elif '传媒' in etf_name or '游戏' in etf_name or '影视' in etf_name:
            cat = '传媒娱乐'
        elif '军工' in etf_name:
            cat = '军工'
        elif '有色' in etf_name or '煤炭' in etf_name or '钢铁' in etf_name:
            cat = '周期资源'
        elif '地产' in etf_name or '基建' in etf_name:
            cat = '基建地产'
        elif '环保' in etf_name or '碳中和' in etf_name:
            cat = '环保'
        else:
            cat = '其他'
        
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(result)
    
    for cat, items in categories.items():
        avg_score = sum(item['score'] for item in items) / len(items) if items else 0
        high_score = max(item['score'] for item in items) if items else 0
        print(f"  {cat}: {len(items)} 个ETF，平均得分: {avg_score:.1f}，最高得分: {high_score:.1f}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()