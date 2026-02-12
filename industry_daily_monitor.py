#!/usr/bin/env python3
"""
A股行业每日监控脚本 - 简化版
基于现有industry_breakout_analysis.py和etf_breakout_analysis.py
先确保基本功能可用，后续可逐步完善
"""

import os
import sys
import json
import subprocess
import warnings
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_industry_breakout_analysis():
    """运行行业突破分析"""
    try:
        print("📊 运行行业突破分析...")
        
        # 运行现有脚本
        import subprocess
        script_path = os.path.join(os.path.dirname(__file__), 'industry_breakout_analysis.py')
        result = subprocess.run([sys.executable, script_path], 
                               capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"⚠️  脚本执行失败: {result.stderr[:200]}")
        
        # 读取生成的JSON文件
        json_file = "industry_breakout_results.json"
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            if results:
                # 找到突破行业（all_conditions_met为True的）
                breakout_industries = [r for r in results if r.get('all_conditions_met', False)]
                
                # 按得分排序
                results.sort(key=lambda x: x.get('score', 0), reverse=True)
                top_industries = results[:5]
                
                print(f"✅ 分析完成，分析 {len(results)} 个行业，找到 {len(breakout_industries)} 个突破行业")
                return {
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_analyzed': len(results),
                    'breakout_industries': breakout_industries,
                    'top_industries': top_industries,
                    'all_results': results,
                    'status': 'success'
                }
        
        print("⚠️  未找到突破行业")
        return {
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'top_industries': [],
            'status': 'no_breakouts'
        }
    except Exception as e:
        print(f"❌ 行业突破分析失败: {e}")
        return {
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'top_industries': [],
            'status': f'error: {str(e)}'
        }

def run_etf_breakout_analysis():
    """运行ETF突破分析"""
    try:
        print("📈 运行ETF突破分析...")
        
        # 运行现有脚本
        import subprocess
        script_path = os.path.join(os.path.dirname(__file__), 'etf_breakout_analysis.py')
        result = subprocess.run([sys.executable, script_path], 
                               capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"⚠️  脚本执行失败: {result.stderr[:200]}")
        
        # 读取生成的JSON文件
        json_file = "etf_breakout_results.json"
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            if results:
                # 找到突破ETF（all_conditions_met为True的）
                breakout_etfs = [r for r in results if r.get('all_conditions_met', False)]
                
                # 按得分排序
                results.sort(key=lambda x: x.get('score', 0), reverse=True)
                top_etfs = results[:5]
                
                print(f"✅ 分析完成，分析 {len(results)} 个ETF，找到 {len(breakout_etfs)} 个突破ETF")
                return {
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_analyzed': len(results),
                    'breakout_etfs': breakout_etfs,
                    'top_etfs': top_etfs,
                    'all_results': results,
                    'status': 'success'
                }
        
        print("⚠️  未找到突破ETF")
        return {
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'top_etfs': [],
            'status': 'no_breakouts'
        }
    except Exception as e:
        print(f"❌ ETF突破分析失败: {e}")
        return {
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'top_etfs': [],
            'status': f'error: {str(e)}'
        }

def search_news_for_industry(industry_name):
    """搜索行业新闻（使用Tavily API）"""
    try:
        tavily_api_key = os.environ.get('TAVILY_API_KEY')
        if not tavily_api_key:
            print(f"⚠️  TAVILY_API_KEY未设置，跳过新闻搜索")
            return []
        
        # 使用Node.js脚本搜索
        search_script = os.path.join(os.path.dirname(__file__), 
                                    'skills/tavily-search/scripts/search.mjs')
        
        if not os.path.exists(search_script):
            print(f"⚠️  Tavily搜索脚本不存在: {search_script}")
            return []
        
        # 构建搜索查询
        query = f"{industry_name} 最新动态 新闻"
        print(f"🔍 搜索新闻: {query}")
        
        cmd = ['node', search_script, query, '-n', '3', '--topic', 'news']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                news_data = json.loads(result.stdout)
                if news_data and 'results' in news_data:
                    return news_data['results'][:3]  # 返回前3条新闻
            except:
                # 如果不是JSON格式，返回原始输出
                return [{'title': '新闻搜索结果', 'content': result.stdout[:200]}]
        else:
            print(f"⚠️  新闻搜索失败: {result.stderr}")
            
        return []
    except Exception as e:
        print(f"⚠️  新闻搜索异常: {e}")
        return []

def combine_results(industry_result, etf_result):
    """结合行业和ETF分析结果"""
    combined = {
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'success',
        'top_industries': [],
        'top_etfs': []
    }
    
    # 添加行业结果
    if industry_result and 'top_industries' in industry_result:
        for industry in industry_result['top_industries'][:5]:  # 最多5个
            # 搜索新闻
            industry_name = industry.get('industry_name', industry.get('name', ''))
            if industry_name:
                industry['news'] = search_news_for_industry(industry_name)
            combined['top_industries'].append(industry)
    
    # 添加ETF结果
    if etf_result and 'top_etfs' in etf_result:
        for etf in etf_result['top_etfs'][:5]:  # 最多5个
            combined['top_etfs'].append(etf)
    
    # 计算综合排名
    all_breakouts = []
    
    # 行业突破
    for idx, industry in enumerate(combined['top_industries']):
        score = industry.get('score', 0)  # 注意：字段是'score'不是'breakout_score'
        industry_name = industry.get('industry_name', industry.get('name', f'行业{idx+1}'))
        industry_code = industry.get('industry_code', industry.get('code', ''))
        
        if 'news' in industry and len(industry['news']) > 0:
            score += 0.5  # 有新闻加分
            
        all_breakouts.append({
            'type': 'industry',
            'name': industry_name,
            'code': industry_code,
            'score': score,
            'breakout_score': score,
            'news_count': len(industry.get('news', [])),
            'all_conditions_met': industry.get('all_conditions_met', False)
        })
    
    # ETF突破
    for idx, etf in enumerate(combined['top_etfs']):
        score = etf.get('score', 0)  # 注意：字段是'score'不是'breakout_score'
        etf_name = etf.get('etf_name', etf.get('name', f'ETF{idx+1}'))
        etf_code = etf.get('etf_code', etf.get('code', ''))
        
        all_breakouts.append({
            'type': 'etf',
            'name': etf_name,
            'code': etf_code,
            'score': score,
            'breakout_score': score,
            'news_count': 0,  # ETF暂时不搜索新闻
            'all_conditions_met': etf.get('all_conditions_met', False)
        })
    
    # 按分数排序
    all_breakouts.sort(key=lambda x: x['score'], reverse=True)
    combined['top_recommendations'] = all_breakouts[:3]  # 前3推荐
    
    return combined

def generate_slack_message(result):
    """生成Slack消息"""
    if not result:
        return "📊 A股行业监控报告\n\n分析失败，请检查日志。"
    
    if 'top_recommendations' not in result or not result['top_recommendations']:
        lines = [
            f"📊 A股行业监控报告 ({result.get('analysis_time', 'N/A')})",
            "",
            "今日未发现明显突破行业。建议继续观察。",
            "",
            "📈 **分析摘要:**"
        ]
        
        if 'top_industries' in result:
            lines.append(f"• 分析行业: {len(result.get('top_industries', []))} 个")
        if 'top_etfs' in result:
            lines.append(f"• 分析ETF: {len(result.get('top_etfs', []))} 个")
        
        lines.append("")
        lines.append("⚠️ **免责声明:** 仅供参考，不构成投资建议。")
        return "\n".join(lines)
    
    lines = [
        f"📊 A股行业监控报告 ({result.get('analysis_time', 'N/A')})",
        "",
        "🏆 **今日推荐关注 (前3名):**",
        ""
    ]
    
    for i, rec in enumerate(result['top_recommendations']):
        stars = "⭐" * (3 - i)  # 第一名3星，第二名2星，第三名1星
        score = rec.get('score', rec.get('breakout_score', 0))
        breakout_info = f"突破强度: {score:.1f}/10"
        
        if rec.get('all_conditions_met', False):
            breakout_info += " 🟢(符合全部条件)"
        
        if rec['type'] == 'industry':
            lines.append(f"{stars} **{rec['name']}** ({rec['code']})")
            lines.append(f"  类型: 行业指数 | {breakout_info}")
            if rec.get('news_count', 0) > 0:
                lines.append(f"  相关新闻: {rec['news_count']} 条")
        else:
            lines.append(f"{stars} **{rec['name']}** ({rec['code']})")
            lines.append(f"  类型: 行业ETF | {breakout_info}")
        
        lines.append("")
    
    # 添加总结
    lines.append("---")
    lines.append("📈 **分析摘要:**")
    
    # 计算突破数量
    if 'top_industries' in result:
        breakout_industries = [ind for ind in result['top_industries'] if ind.get('all_conditions_met', False)]
        lines.append(f"• 突破行业: {len(breakout_industries)} 个 (共分析 {len(result['top_industries'])} 个)")
    
    if 'top_etfs' in result:
        breakout_etfs = [etf for etf in result['top_etfs'] if etf.get('all_conditions_met', False)]
        lines.append(f"• 突破ETF: {len(breakout_etfs)} 个 (共分析 {len(result['top_etfs'])} 个)")
    
    lines.append(f"• 综合推荐: {len(result.get('top_recommendations', []))} 个")
    lines.append("")
    lines.append("⚠️ **免责声明:** 仅供参考，不构成投资建议。")
    
    return "\n".join(lines)

def main():
    """主函数"""
    print("=" * 60)
    print("A股行业每日监控脚本 (简化版)")
    print("=" * 60)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查依赖
    try:
        import baostock as bs
        import pandas as pd
        import numpy as np
        print("✅ 基础依赖检查通过")
    except ImportError as e:
        print(f"❌ 依赖导入失败: {e}")
        print("请安装依赖: pip install baostock pandas numpy")
        return 1
    
    # 运行分析
    industry_result = run_industry_breakout_analysis()
    etf_result = run_etf_breakout_analysis()
    
    # 合并结果
    final_result = combine_results(industry_result, etf_result)
    
    # 保存结果
    output_file = "industry_daily_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 分析结果已保存至: {output_file}")
    
    # 生成Slack消息
    slack_message = generate_slack_message(final_result)
    
    print(f"\n📤 Slack消息已生成:")
    print("-" * 40)
    print(slack_message)
    print("-" * 40)
    
    # 也保存消息到文件
    message_file = "industry_daily_slack_message.txt"
    with open(message_file, 'w', encoding='utf-8') as f:
        f.write(slack_message)
    
    print(f"📝 Slack消息已保存至: {message_file}")
    
    print("\n" + "=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())