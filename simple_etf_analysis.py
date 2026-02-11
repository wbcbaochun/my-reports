#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版A股行业ETF量化分析 (方案A: 行业ETF替代)
"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 行业ETF映射表 (精选10个主要行业)
ETF_MAPPING = {
    'sh.512480': '半导体ETF',
    'sh.512170': '医疗ETF',
    'sh.516160': '新能源车ETF',
    'sh.512600': '主要消费ETF',
    'sh.512070': '证券ETF',
    'sh.512330': '信息技术ETF',
    'sh.512560': '军工ETF',
    'sh.512400': '有色金属ETF',
    'sh.512200': '房地产ETF',
    'sh.512010': '医药ETF',
    'sh.512880': '证券ETF(龙头)',
    'sh.512980': '传媒ETF',
    'sh.515790': '光伏ETF',
    'sh.515170': '食品饮料ETF',
}

def init_baostock():
    """初始化baostock连接"""
    lg = bs.login()
    if lg.error_code != '0':
        print(f"❌ 登录失败: {lg.error_msg}")
        return None
    print("✅ baostock登录成功")
    return True

def get_etf_data(etf_code, start_date, end_date):
    """获取ETF日线数据"""
    rs = bs.query_history_k_data_plus(
        etf_code,
        "date,code,open,high,low,close,volume,amount,pctChg",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="3"
    )
    
    if rs.error_code != '0':
        print(f"   ⚠️ 获取失败: {rs.error_msg}")
        return None
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    if df.empty:
        return None
    
    # 转换数据类型
    for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pctChg']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df

def calculate_technical_indicators(df):
    """计算技术指标"""
    if df is None or len(df) < 60:
        return df
    
    df = df.copy()
    
    # 移动平均线
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA60'] = df['close'].rolling(window=60).mean()
    
    # 价格相对位置 (最近60天)
    recent_high = df['high'].rolling(window=60).max()
    recent_low = df['low'].rolling(window=60).min()
    df['price_position'] = (df['close'] - recent_low) / (recent_high - recent_low + 1e-8)
    
    # 成交量指标
    df['volume_ma5'] = df['volume'].rolling(window=5).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma5']
    
    # RSI (14天)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-8)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp12 = df['close'].ewm(span=12, adjust=False).mean()
    exp26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    
    return df

def analyze_breakout(df):
    """分析底部突破特征"""
    if df is None or len(df) < 60:
        return None
    
    latest = df.iloc[-1]
    
    # 计算回调幅度 (最近60天)
    recent_high = df['high'].iloc[-60:].max()
    recent_low = df['low'].iloc[-60:].min()
    current_price = latest['close']
    
    drawdown = (recent_high - current_price) / recent_high if recent_high > 0 else 0
    rebound = (current_price - recent_low) / recent_low if recent_low > 0 else 0
    
    # 成交量放大 (最近5天 vs 前20天)
    if len(df) >= 25:
        recent_vol = df['volume'].iloc[-5:].mean()
        prev_vol = df['volume'].iloc[-25:-5].mean()
        volume_surge = recent_vol / (prev_vol + 1e-8)
    else:
        volume_surge = 1.0
    
    # 突破信号
    price_above_ma20 = current_price > latest['MA20']
    rsi_value = latest['RSI'] if not pd.isna(latest['RSI']) else 50
    rsi_recovering = rsi_value > 30 and rsi_value < 70  # 中性区域
    
    # MACD金叉
    if len(df) >= 2:
        prev = df.iloc[-2]
        macd_golden = (prev['MACD'] < prev['MACD_signal']) and (latest['MACD'] > latest['MACD_signal'])
    else:
        macd_golden = False
    
    # 综合得分 (0-10)
    score = 0
    
    # 回调充分 (>20%)
    if drawdown > 0.2:
        score += 2
    elif drawdown > 0.15:
        score += 1
    
    # 价格低位 (位置<30%)
    if latest['price_position'] < 0.3:
        score += 1
    
    # 价格突破20日线
    if price_above_ma20:
        score += 1
    
    # 成交量放大 (>1.5倍)
    if volume_surge > 1.5:
        score += 2
    elif volume_surge > 1.2:
        score += 1
    
    # RSI合理
    if 30 < rsi_value < 70:
        score += 1
    
    # MACD金叉
    if macd_golden:
        score += 2
    
    # 突破强度评级
    if score >= 7:
        strength = "强突破"
    elif score >= 5:
        strength = "中等突破"
    elif score >= 3:
        strength = "弱突破"
    else:
        strength = "无突破"
    
    return {
        'etf_code': latest['code'],
        'etf_name': '',
        'current_price': round(current_price, 3),
        'price_change': round(latest['pctChg'], 2) if not pd.isna(latest['pctChg']) else 0,
        'drawdown': round(drawdown * 100, 1),
        'rebound': round(rebound * 100, 1),
        'price_position': round(latest['price_position'] * 100, 1),
        'volume_surge': round(volume_surge, 2),
        'above_ma20': price_above_ma20,
        'rsi': round(rsi_value, 1),
        'macd_golden': macd_golden,
        'score': score,
        'strength': strength
    }

def generate_text_report(analyses):
    """生成文本报告"""
    if not analyses:
        return "❌ 没有获取到有效的ETF数据"
    
    # 按得分排序
    sorted_analyses = sorted(analyses, key=lambda x: x['score'], reverse=True)
    
    report = []
    report.append("=" * 60)
    report.append("A股行业ETF技术分析报告 (方案A: 行业ETF替代)")
    report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"分析样本: {len(analyses)} 个行业ETF")
    report.append("=" * 60)
    report.append("")
    
    # 总体统计
    strong = sum(1 for a in analyses if a['strength'] == "强突破")
    medium = sum(1 for a in analyses if a['strength'] == "中等突破")
    weak = sum(1 for a in analyses if a['strength'] == "弱突破")
    
    report.append("📊 总体市场状况:")
    report.append(f"  强突破行业: {strong} 个")
    report.append(f"  中等突破行业: {medium} 个")
    report.append(f"  弱突破行业: {weak} 个")
    report.append(f"  无突破行业: {len(analyses) - strong - medium - weak} 个")
    report.append("")
    
    # 推荐前3名
    report.append("🏆 推荐关注行业 (按突破强度排名):")
    report.append("")
    
    for i, analysis in enumerate(sorted_analyses[:3], 1):
        report.append(f"{i}. {analysis['etf_name']} ({analysis['etf_code']})")
        report.append(f"   突破强度: {analysis['strength']} (得分: {analysis['score']}/10)")
        report.append(f"   当前价格: {analysis['current_price']}元 | 涨跌: {analysis['price_change']}%")
        report.append(f"   从高点回调: {analysis['drawdown']}% | 从低点反弹: {analysis['rebound']}%")
        report.append(f"   价格位置: {analysis['price_position']}% (0%=最低, 100%=最高)")
        report.append(f"   成交量放大: {analysis['volume_surge']}倍")
        report.append(f"   站上20日线: {'✅' if analysis['above_ma20'] else '❌'}")
        report.append(f"   RSI指标: {analysis['rsi']} ({'超卖' if analysis['rsi'] < 30 else '中性' if analysis['rsi'] < 70 else '超买'})")
        report.append(f"   MACD金叉: {'✅' if analysis['macd_golden'] else '❌'}")
        
        if analysis['score'] >= 7:
            advice = "强烈关注: 多重技术指标显示明确突破信号，建议重点关注。"
        elif analysis['score'] >= 5:
            advice = "谨慎关注: 部分技术指标显示突破迹象，建议观察确认。"
        else:
            advice = "观望: 技术指标突破信号较弱，建议等待更明确信号。"
        
        report.append(f"   投资建议: {advice}")
        report.append("")
    
    # 其他行业概览
    if len(sorted_analyses) > 3:
        report.append("📈 其他行业概览:")
        report.append("排名 | 行业ETF | 代码 | 突破强度 | 得分 | 价格 | 涨跌")
        report.append("----|---------|------|----------|------|------|------")
        
        for i, analysis in enumerate(sorted_analyses[3:8], 4):
            name = analysis['etf_name'][:10] if analysis['etf_name'] else analysis['etf_code']
            report.append(f"{i:2d} | {name:10} | {analysis['etf_code']} | {analysis['strength']:8} | {analysis['score']:4} | {analysis['current_price']:5} | {analysis['price_change']:5}%")
    
    report.append("")
    report.append("⚠️ 风险提示:")
    report.append("1. 数据延迟: 本分析基于公开市场数据，可能存在延迟")
    report.append("2. 技术分析局限性: 技术指标仅为辅助工具，不能保证未来表现")
    report.append("3. 市场风险: 投资有风险，入市需谨慎")
    report.append("4. ETF流动性: 部分ETF流动性较差，需注意交易成本")
    report.append("")
    report.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(report)

def main():
    """主函数"""
    print("🚀 开始A股行业ETF量化分析 (方案A: 行业ETF替代)...")
    
    # 初始化baostock
    if not init_baostock():
        return None
    
    # 设置时间范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    print(f"📅 数据时间范围: {start_date} 至 {end_date}")
    print(f"📊 分析样本: {len(ETF_MAPPING)} 个行业ETF")
    print("")
    
    # 分析每个ETF
    analyses = []
    
    for etf_code, etf_name in ETF_MAPPING.items():
        print(f"正在分析 {etf_name} ({etf_code})...")
        
        # 获取数据
        df = get_etf_data(etf_code, start_date, end_date)
        if df is None or len(df) < 60:
            print(f"  ⚠️ 数据不足，跳过")
            continue
        
        # 计算技术指标
        df = calculate_technical_indicators(df)
        
        # 分析突破特征
        analysis = analyze_breakout(df)
        if analysis:
            analysis['etf_name'] = etf_name
            analyses.append(analysis)
            
            # 打印简要结果
            icon = "🟢" if analysis['strength'] == "强突破" else "🟡" if analysis['strength'] == "中等突破" else "🔴"
            print(f"  {icon} {analysis['strength']} (得分: {analysis['score']})")
    
    # 生成报告
    if analyses:
        print(f"\n✅ 分析完成，共分析 {len(analyses)} 个有效ETF")
        report = generate_text_report(analyses)
        
        # 保存报告文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        report_filename = f"reports/A股行业ETF分析_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 报告已保存: {report_filename}")
        
        # 输出报告摘要
        print("\n" + "=" * 60)
        print("📋 分析结果摘要")
        print("=" * 60)
        
        sorted_analyses = sorted(analyses, key=lambda x: x['score'], reverse=True)
        
        print(f"\n🏆 推荐前3名:")
        for i, analysis in enumerate(sorted_analyses[:3], 1):
            print(f"{i}. {analysis['etf_name']} ({analysis['etf_code']})")
            print(f"   突破强度: {analysis['strength']} | 得分: {analysis['score']}/10")
            print(f"   当前价格: {analysis['current_price']}元 | 涨跌: {analysis['price_change']}%")
        
        return report_filename
    else:
        print("❌ 没有获取到有效的ETF数据")
        return None
    
    # 登出baostock
    bs.logout()

if __name__ == "__main__":
    main()