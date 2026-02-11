#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股行业ETF量化分析脚本 (方案A: 行业ETF替代)
使用baostock获取ETF数据，分析底部突破特征
"""

import baostock as bs
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def init_baostock():
    """初始化baostock连接"""
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return None
    print("✅ baostock登录成功")
    return True

def get_etf_data(etf_code, start_date, end_date):
    """获取ETF日线数据"""
    rs = bs.query_history_k_data_plus(
        etf_code,
        "date,code,open,high,low,close,volume,amount,turn,pctChg",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="3"
    )
    
    if rs.error_code != '0':
        print(f"❌ 获取{etf_code}数据失败: {rs.error_msg}")
        return None
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    if df.empty:
        return None
    
    # 转换数据类型
    for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 'pctChg']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df

def calculate_technical_indicators(df):
    """计算技术指标"""
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # 移动平均线
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA60'] = df['close'].rolling(window=60).mean()
    
    # 价格相对位置
    recent_high = df['high'].rolling(window=60).max()
    recent_low = df['low'].rolling(window=60).min()
    df['price_position'] = (df['close'] - recent_low) / (recent_high - recent_low + 1e-8)
    
    # 成交量指标
    df['volume_ma5'] = df['volume'].rolling(window=5).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma5']
    
    # RSI
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

def analyze_breakout(df, lookback_days=120):
    """分析底部突破特征"""
    if df is None or len(df) < lookback_days:
        return {}
    
    latest = df.iloc[-1]
    prev_day = df.iloc[-2]
    
    # 获取最近lookback_days的数据
    recent_data = df.iloc[-lookback_days:]
    
    # 计算回调幅度
    recent_high = recent_data['high'].max()
    recent_low = recent_data['low'].min()
    current_price = latest['close']
    
    # 回调幅度（从高点回撤）
    drawdown_from_high = (recent_high - current_price) / recent_high if recent_high > 0 else 0
    
    # 从低点反弹幅度
    rebound_from_low = (current_price - recent_low) / recent_low if recent_low > 0 else 0
    
    # 是否处于低位（价格位置<30%）
    in_low_position = latest['price_position'] < 0.3 if not pd.isna(latest['price_position']) else False
    
    # 成交量放大（最近5天平均成交量 vs 前20天）
    if len(df) >= 25:
        recent_volume_avg = df.iloc[-5:]['volume'].mean()
        prev_volume_avg = df.iloc[-25:-5]['volume'].mean()
        volume_surge = recent_volume_avg / (prev_volume_avg + 1e-8)
    else:
        volume_surge = 1.0
    
    # 突破判断
    # 1. 价格突破20日均线
    price_above_ma20 = current_price > latest['MA20']
    
    # 2. 成交量放大（>1.5倍）
    volume_surge_significant = volume_surge > 1.5
    
    # 3. RSI从超卖区域回升（<30回升）
    rsi_recovering = (prev_day['RSI'] < 30) and (latest['RSI'] > prev_day['RSI'])
    
    # 4. MACD金叉
    macd_golden_cross = (prev_day['MACD'] < prev_day['MACD_signal']) and (latest['MACD'] > latest['MACD_signal'])
    
    # 综合得分（0-10分）
    score = 0
    
    # 回调充分（回调>20%）
    if drawdown_from_high > 0.2:
        score += 2
    elif drawdown_from_high > 0.15:
        score += 1
    
    # 价格低位
    if in_low_position:
        score += 1
    
    # 价格突破MA20
    if price_above_ma20:
        score += 1
    
    # 成交量放大
    if volume_surge_significant:
        score += 2
    elif volume_surge > 1.2:
        score += 1
    
    # RSI回升
    if rsi_recovering:
        score += 1
    
    # MACD金叉
    if macd_golden_cross:
        score += 2
    
    # 反弹幅度
    if rebound_from_low > 0.05:
        score += 1
    
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
        'etf_code': latest['code'] if 'code' in latest else '',
        'current_price': round(current_price, 3),
        'price_change_pct': round(latest['pctChg'], 2) if not pd.isna(latest['pctChg']) else 0,
        'drawdown_from_high': round(drawdown_from_high * 100, 2),
        'rebound_from_low': round(rebound_from_low * 100, 2),
        'price_position': round(latest['price_position'] * 100, 2) if not pd.isna(latest['price_position']) else 0,
        'volume_surge': round(volume_surge, 2),
        'above_ma20': price_above_ma20,
        'rsi': round(latest['RSI'], 2) if not pd.isna(latest['RSI']) else 50,
        'macd_golden_cross': macd_golden_cross,
        'breakout_score': score,
        'breakout_strength': strength,
        'analysis_date': latest['date'].strftime('%Y-%m-%d') if isinstance(latest['date'], datetime) else str(latest['date'])
    }

def generate_report(etf_analyses):
    """生成分析报告"""
    if not etf_analyses:
        return "❌ 没有可分析的数据"
    
    # 按突破得分排序
    sorted_analyses = sorted(etf_analyses, key=lambda x: x['breakout_score'], reverse=True)
    
    report = "# A股行业ETF技术分析报告\n\n"
    report += f"**分析时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    report += f"**分析样本:** {len(etf_analyses)} 个行业ETF\n\n"
    
    # 总体统计
    strong_count = sum(1 for a in etf_analyses if a['breakout_strength'] == "强突破")
    medium_count = sum(1 for a in etf_analyses if a['breakout_strength'] == "中等突破")
    weak_count = sum(1 for a in etf_analyses if a['breakout_strength'] == "弱突破")
    
    report += f"## 📊 总体市场状况\n\n"
    report += f"- **强突破行业:** {strong_count} 个\n"
    report += f"- **中等突破行业:** {medium_count} 个\n"
    report += f"- **弱突破行业:** {weak_count} 个\n"
    report += f"- **无突破行业:** {len(etf_analyses) - strong_count - medium_count - weak_count} 个\n\n"
    
    # 推荐前3名
    report += f"## 🏆 推荐关注行业 (按突破强度排名)\n\n"
    
    top3 = sorted_analyses[:3]
    for i, analysis in enumerate(top3, 1):
        etf_name = ETF_MAPPING.get(analysis['etf_code'], analysis['etf_code'])
        
        report += f"### {i}. {etf_name} ({analysis['etf_code']})\n\n"
        report += f"**突破强度:** {analysis['breakout_strength']} (得分: {analysis['breakout_score']}/10)\n\n"
        report += f"**技术指标:**\n"
        report += f"- 当前价格: {analysis['current_price']}元\n"
        report += f"- 当日涨跌: {analysis['price_change_pct']}%\n"
        report += f"- 从高点回调: {analysis['drawdown_from_high']}%\n"
        report += f"- 从低点反弹: {analysis['rebound_from_low']}%\n"
        report += f"- 价格相对位置: {analysis['price_position']}% (0%=最低, 100%=最高)\n"
        report += f"- 成交量放大: {analysis['volume_surge']}倍\n"
        report += f"- 站上20日线: {'✅' if analysis['above_ma20'] else '❌'}\n"
        report += f"- RSI指标: {analysis['rsi']} ({'超卖回升' if analysis['rsi'] < 35 else '中性' if analysis['rsi'] < 65 else '超买'})\n"
        report += f"- MACD金叉: {'✅' if analysis['macd_golden_cross'] else '❌'}\n\n"
        
        # 投资建议
        if analysis['breakout_score'] >= 7:
            advice = "**强烈关注**: 多重技术指标显示明确突破信号，成交量配合良好，建议重点关注。"
        elif analysis['breakout_score'] >= 5:
            advice = "**谨慎关注**: 部分技术指标显示突破迹象，但信号不够强烈，建议观察确认。"
        else:
            advice = "**观望**: 技术指标突破信号较弱，建议等待更明确信号。"
        
        report += f"**投资建议:** {advice}\n\n"
        report += "---\n\n"
    
    # 其他行业概览
    if len(sorted_analyses) > 3:
        report += f"## 📈 其他行业概览\n\n"
        report += f"| 排名 | 行业ETF | 代码 | 突破强度 | 得分 | 当前价格 | 涨跌幅 |\n"
        report += f"|------|---------|------|----------|------|----------|--------|\n"
        
        for i, analysis in enumerate(sorted_analyses[3:10], 4):
            etf_name = ETF_MAPPING.get(analysis['etf_code'], analysis['etf_code'])[:15]
            report += f"| {i} | {etf_name} | {analysis['etf_code']} | {analysis['breakout_strength']} | {analysis['breakout_score']} | {analysis['current_price']} | {analysis['price_change_pct']}% |\n"
    
    # 风险提示
    report += f"\n## ⚠️ 风险提示\n\n"
    report += f"1. **数据延迟**: 本分析基于公开市场数据，可能存在延迟\n"
    report += f"2. **技术分析局限性**: 技术指标仅为辅助工具，不能保证未来表现\n"
    report += f"3. **市场风险**: 投资有风险，入市需谨慎\n"
    report += f"4. **ETF流动性**: 部分ETF流动性较差，需注意交易成本\n\n"
    
    report += f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    return report

# 行业ETF映射表
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
    'sh.512100': '中证1000ETF',
    'sh.512500': '中证500ETF',
    'sh.512010': '医药ETF',
    'sh.512000': '券商ETF',
    'sh.512580': '环保ETF',
    'sh.512380': '银行ETF',
    'sh.512800': '银行ETF(规模)',
    'sh.512660': '军工ETF(龙头)',
    'sh.512690': '酒ETF',
    'sh.512880': '证券ETF(龙头)',
    'sh.512980': '传媒ETF',
    'sh.515050': '5GETF',
    'sh.515030': '新能源汽车ETF',
    'sh.515790': '光伏ETF',
    'sh.515170': '食品饮料ETF',
    'sh.518800': '黄金ETF'
}

def main():
    """主函数"""
    print("🚀 开始A股行业ETF量化分析 (方案A: 行业ETF替代)...")
    
    # 初始化baostock
    if not init_baostock():
        return
    
    # 设置时间范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    print(f"📅 数据时间范围: {start_date} 至 {end_date}")
    print(f"📊 分析样本: {len(ETF_MAPPING)} 个行业ETF")
    
    # 分析每个ETF
    etf_analyses = []
    
    for i, (etf_code, etf_name) in enumerate(ETF_MAPPING.items(), 1):
        print(f"[{i}/{len(ETF_MAPPING)}] 正在分析 {etf_name} ({etf_code})...")
        
        # 获取数据
        df = get_etf_data(etf_code, start_date, end_date)
        if df is None or len(df) < 60:
            print(f"   ⚠️  {etf_name} 数据不足，跳过")
            continue
        
        # 计算技术指标
        df = calculate_technical_indicators(df)
        
        # 分析突破特征
        analysis = analyze_breakout(df)
        if analysis:
            analysis['etf_name'] = etf_name
            etf_analyses.append(analysis)
            
            # 打印简要结果
            strength_icon = "🟢" if analysis['breakout_strength'] == "强突破" else "🟡" if analysis['breakout_strength'] == "中等突破" else "🔴"
            print(f"   {strength_icon} {etf_name}: {analysis['breakout_strength']} (得分: {analysis['breakout_score']})")
    
    # 生成报告
    if etf_analyses:
        print(f"\n📈 分析完成，共分析 {len(etf_analyses)} 个有效ETF")
        report = generate_report(etf_analyses)
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        report_filename = f"reports/行业ETF技术分析_{timestamp}.html"
        
        # 创建HTML报告
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>A股行业ETF技术分析报告</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 1000px; margin: 0 auto; padding: 20px; color: #333; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #3498db; margin-top: 30px; }}
                h3 {{ color: #2c3e50; }}
                .strong {{ color: #27ae60; font-weight: bold; }}
                .medium {{ color: #f39c12; }}
                .weak {{ color: #e74c3c; }}
                .advice {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background: #f2f2f2; }}
                .summary {{ background: #e8f4fc; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            {report.replace('\n', '<br>').replace('## ', '<h2>').replace('### ', '<h3>').replace('**', '<strong>').replace('**', '</strong>')}
        </body>
        </html>
        """
        
        # 保存报告文件
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ 报告已保存: {report_filename}")
        
        # 输出摘要到控制台
        print("\n" + "="*60)
        print("📋 分析结果摘要")
        print("="*60)
        
        # 按得分排序
        sorted_analyses = sorted(etf_analyses, key=lambda x: x['breakout_score'], reverse=True)
        
        print(f"\n🏆 推荐前3名:")
        for i, analysis in enumerate(sorted_analyses[:3], 1):
            print(f"{i}. {analysis['etf_name']} ({analysis['etf_code']})")
            print(f"   突破强度: {analysis['breakout_strength']} | 得分: {analysis['breakout_score']}/10")
            print(f"   当前价格: {analysis['current_price']}元 | 涨跌: {analysis['price_change_pct']}%")
            print(f"   回调: {analysis['drawdown_from_high']}% | 成交量放大: {analysis['volume_surge']}倍")
            print()
        
        print(f"📊 总体市场状况:")
        strong = sum(1 for a in etf_analyses if a['breakout_strength'] == "强突破")
        medium = sum(1 for a in etf_analyses if a['breakout_strength'] == "中等突破")
        weak = sum(1 for a in etf_analyses if a['breakout_strength'] == "弱突破")
        print(f"   强突破: {strong}个 | 中等突破: {medium}个 | 弱突破: {weak}个 | 总计: {len(etf_analyses)}个")
        
        return report
    else:
        print("❌ 没有获取到有效的ETF数据")
        return None
    
    # 登出baostock
    bs.logout()

if __name__ == "__main__":
    main()