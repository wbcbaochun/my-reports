#!/usr/bin/env python3
"""
A股行业每日监控脚本 - 增强版
包含细分行业ETF分析，修复ETF数据获取问题
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

def run_etf_breakout_analysis_enhanced():
    """运行增强版ETF突破分析（支持细分行业）"""
    try:
        print("📈 运行细分行业ETF突破分析...")
        
        # 运行修复版脚本
        script_path = os.path.join(os.path.dirname(__file__), 'etf_breakout_analysis_fixed.py')
        
        # 检查脚本是否存在
        if not os.path.exists(script_path):
            print(f"⚠️  修复版脚本不存在，使用原始版本")
            return run_etf_breakout_analysis_original()
        
        result = subprocess.run([sys.executable, script_path], 
                               capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"⚠️  脚本执行失败: {result.stderr[:200]}")
        
        # 读取生成的JSON文件
        json_file = "etf_breakout_results_fixed.json"
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            if results:
                # 找到突破ETF（all_conditions_met为True的）
                breakout_etfs = [r for r in results if r.get('all_conditions_met', False)]
                
                # 按得分排序
                results.sort(key=lambda x: x.get('score', 0), reverse=True)
                top_etfs = results[:10]  # 取前10个，因为ETF数量多
                
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

def run_etf_breakout_analysis_original():
    """运行原始ETF突破分析"""
    try:
        print("📈 运行原始ETF突破分析...")
        
        # 运行原始脚本
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

def search_news_for_item(name, item_type="行业"):
    """搜索新闻（使用Tavily API）"""
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
        if item_type == "ETF":
            query = f"{name} ETF 最新动态 投资机会"
        else:
            query = f"{name} 最新动态 新闻"
        
        print(f"🔍 搜索{name}新闻: {query}")
        
        cmd = ['node', search_script, query, '-n', '2', '--topic', 'news']  # 只搜索2条
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                news_data = json.loads(result.stdout)
                if news_data and 'results' in news_data:
                    return news_data['results'][:2]  # 返回前2条新闻
            except:
                # 如果不是JSON格式，返回原始输出
                if result.stdout.strip():
                    return [{'title': f'{name}相关新闻', 'content': result.stdout[:200]}]
        else:
            print(f"⚠️  新闻搜索失败: {result.stderr}")
            
        return []
    except Exception as e:
        print(f"⚠️  新闻搜索异常: {e}")
        return []

def categorize_etf(etf_name):
    """对ETF进行行业分类"""
    etf_name_lower = etf_name.lower()
    
    category_map = [
        ('半导体', '半导体/芯片'),
        ('芯片', '半导体/芯片'),
        ('医药', '医药医疗'),
        ('医疗', '医药医疗'),
        ('健康', '医药医疗'),
        ('创新药', '医药医疗'),
        ('生物医药', '医药医疗'),
        ('器械', '医药医疗'),
        ('新能源', '新能源'),
        ('光伏', '新能源'),
        ('电池', '新能源'),
        ('锂电池', '新能源'),
        ('碳中和', '新能源'),
        ('消费', '消费'),
        ('酒', '消费'),
        ('食品', '消费'),
        ('饮料', '消费'),
        ('家电', '消费'),
        ('科技', '科技'),
        ('信息', '科技'),
        ('5g', '科技'),
        ('通信', '科技'),
        ('人工', '科技'),
        ('传媒', '传媒娱乐'),
        ('游戏', '传媒娱乐'),
        ('影视', '传媒娱乐'),
        ('娱乐', '传媒娱乐'),
        ('金融', '金融'),
        ('证券', '金融'),
        ('银行', '金融'),
        ('保险', '金融'),
        ('军工', '军工'),
        ('有色', '周期资源'),
        ('煤炭', '周期资源'),
        ('钢铁', '周期资源'),
        ('资源', '周期资源'),
        ('地产', '基建地产'),
        ('基建', '基建地产'),
        ('建筑', '基建地产'),
        ('建材', '基建地产'),
        ('环保', '环保'),
        ('旅游', '旅游'),
        ('教育', '教育'),
        ('体育', '体育'),
    ]
    
    for keyword, category in category_map:
        if keyword in etf_name_lower:
            return category
    
    return '其他'

def combine_results(industry_result, etf_result):
    """结合行业和ETF分析结果，支持细分行业分类"""
    combined = {
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'success',
        'top_industries': [],
        'top_etfs': [],
        'etf_categories': {},
        'top_recommendations': []
    }
    
    # 添加行业结果
    if industry_result and 'top_industries' in industry_result:
        for industry in industry_result['top_industries'][:5]:  # 最多5个
            # 搜索新闻
            industry_name = industry.get('industry_name', industry.get('name', ''))
            if industry_name:
                industry['news'] = search_news_for_item(industry_name, "行业")
                industry['category'] = '行业指数'
            combined['top_industries'].append(industry)
    
    # 添加ETF结果
    if etf_result and 'top_etfs' in etf_result:
        for etf in etf_result['top_etfs'][:15]:  # 取前15个，因为ETF数量多
            etf_name = etf.get('etf_name', etf.get('name', ''))
            
            # 对ETF进行分类
            etf_category = categorize_etf(etf_name)
            etf['category'] = etf_category
            
            # 搜索新闻（只对高分ETF）
            score = etf.get('score', 0)
            if score >= 6:
                etf['news'] = search_news_for_item(etf_name, "ETF")
            else:
                etf['news'] = []
            
            combined['top_etfs'].append(etf)
            
            # 按分类统计
            if etf_category not in combined['etf_categories']:
                combined['etf_categories'][etf_category] = {
                    'count': 0,
                    'total_score': 0,
                    'top_etfs': []
                }
            
            combined['etf_categories'][etf_category]['count'] += 1
            combined['etf_categories'][etf_category]['total_score'] += score
            
            # 保存该分类下的前3个ETF
            category_etfs = combined['etf_categories'][etf_category]['top_etfs']
            category_etfs.append(etf)
            category_etfs.sort(key=lambda x: x.get('score', 0), reverse=True)
            combined['etf_categories'][etf_category]['top_etfs'] = category_etfs[:3]
    
    # 计算分类平均分
    for category, data in combined['etf_categories'].items():
        if data['count'] > 0:
            data['avg_score'] = data['total_score'] / data['count']
    
    # 计算综合推荐
    all_candidates = []
    
    # 行业候选
    for idx, industry in enumerate(combined['top_industries']):
        score = industry.get('score', 0)
        industry_name = industry.get('industry_name', industry.get('name', f'行业{idx+1}'))
        industry_code = industry.get('industry_code', industry.get('code', ''))
        
        # 新闻加分
        news_bonus = 0.5 if 'news' in industry and len(industry['news']) > 0 else 0
        
        all_candidates.append({
            'type': 'industry',
            'name': industry_name,
            'code': industry_code,
            'score': min(10, score + news_bonus),
            'original_score': score,
            'category': '行业指数',
            'news_count': len(industry.get('news', [])),
            'all_conditions_met': industry.get('all_conditions_met', False),
            'data_days': industry.get('data_days', 'N/A')
        })
    
    # ETF候选（只取前10个高分ETF）
    top_etfs_sorted = sorted(combined['top_etfs'], key=lambda x: x.get('score', 0), reverse=True)[:10]
    
    for etf in top_etfs_sorted:
        score = etf.get('score', 0)
        etf_name = etf.get('etf_name', etf.get('name', ''))
        etf_code = etf.get('etf_code', etf.get('code', ''))
        etf_category = etf.get('category', '其他')
        
        # 新闻加分（已在高分ETF中搜索）
        news_bonus = 0.5 if 'news' in etf and len(etf['news']) > 0 else 0
        
        all_candidates.append({
            'type': 'etf',
            'name': etf_name,
            'code': etf_code,
            'score': min(10, score + news_bonus),
            'original_score': score,
            'category': etf_category,
            'news_count': len(etf.get('news', [])),
            'all_conditions_met': etf.get('all_conditions_met', False),
            'data_days': etf.get('data_days', 'N/A')
        })
    
    # 按分数排序，确保行业和ETF公平竞争
    all_candidates.sort(key=lambda x: x['score'], reverse=True)
    combined['top_recommendations'] = all_candidates[:5]  # 前5推荐
    
    # 按分类生成推荐
    category_recommendations = {}
    for candidate in all_candidates:
        category = candidate['category']
        if category not in category_recommendations:
            category_recommendations[category] = []
        category_recommendations[category].append(candidate)
    
    # 每个分类取前2个
    combined['category_recommendations'] = {}
    for category, items in category_recommendations.items():
        combined['category_recommendations'][category] = items[:2]
    
    return combined

def generate_slack_message(result):
    """生成Slack消息，包含细分行业ETF分析"""
    if not result:
        return "📊 A股行业监控报告\n\n分析失败，请检查日志。"
    
    lines = [
        f"📊 A股行业监控报告 - 含细分行业ETF ({result.get('analysis_time', 'N/A')})",
        "",
    ]
    
    # 如果有推荐
    if 'top_recommendations' in result and result['top_recommendations']:
        lines.append("🏆 **综合推荐 (前5名):**")
        lines.append("")
        
        for i, rec in enumerate(result['top_recommendations']):
            stars = "⭐" * (5 - i)  # 第一名5星，递减
            score = rec.get('score', 0)
            breakout_info = f"综合评分: {score:.1f}/10"
            
            if rec.get('all_conditions_met', False):
                breakout_info += " 🟢(符合全部条件)"
            
            lines.append(f"{stars} **{rec['name']}** ({rec['code']})")
            lines.append(f"  类型: {rec['type']} | 分类: {rec['category']} | {breakout_info}")
            
            if rec.get('news_count', 0) > 0:
                lines.append(f"  相关新闻: {rec['news_count']} 条")
            
            if rec.get('data_days') and rec['data_days'] != 'N/A':
                lines.append(f"  数据天数: {rec['data_days']}")
            
            lines.append("")
    else:
        lines.append("今日未发现明显突破机会。建议继续观察。")
        lines.append("")
    
    # 添加细分行业分类推荐
    if 'category_recommendations' in result and result['category_recommendations']:
        lines.append("📋 **细分行业分类推荐:**")
        lines.append("")
        
        for category, items in result['category_recommendations'].items():
            if items:
                lines.append(f"**{category}**:")
                for item in items:
                    score = item.get('score', 0)
                    item_type = "🟦行业" if item['type'] == 'industry' else "🟩ETF"
                    lines.append(f"  {item_type} {item['name']} - 评分: {score:.1f}/10")
                lines.append("")
    
    # 添加分析摘要
    lines.append("---")
    lines.append("📈 **分析摘要:**")
    
    if 'top_industries' in result:
        breakout_industries = [ind for ind in result['top_industries'] if ind.get('all_conditions_met', False)]
        lines.append(f"• 分析行业: {len(result['top_industries'])} 个，突破行业: {len(breakout_industries)} 个")
    
    if 'top_etfs' in result:
        breakout_etfs = [etf for etf in result['top_etfs'] if etf.get('all_conditions_met', False)]
        lines.append(f"• 分析ETF: {len(result['top_etfs'])} 个（含细分行业），突破ETF: {len(breakout_etfs)} 个")
    
    if 'etf_categories' in result:
        lines.append(f"• 覆盖细分行业: {len(result['etf_categories'])} 个类别")
    
    if 'top_recommendations' in result:
        lines.append(f"• 综合推荐: {len(result['top_recommendations'])} 个")
    
    lines.append("")
    lines.append("⚠️ **免责声明:** 仅供参考，不构成投资建议。")
    lines.append("🔍 **数据说明:** ETF分析已适配不同数据量，部分新ETF数据较少。")
    
    return "\n".join(lines)

def main():
    """主函数"""
    print("=" * 70)
    print("A股行业每日监控脚本 - 增强版 (含细分行业ETF)")
    print("=" * 70)
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
    print("\n🔍 开始分析...")
    industry_result = run_industry_breakout_analysis()
    
    print("\n🔍 开始细分行业ETF分析...")
    etf_result = run_etf_breakout_analysis_enhanced()
    
    # 合并结果
    print("\n🔧 合并分析结果...")
    final_result = combine_results(industry_result, etf_result)
    
    # 保存结果
    output_file = "industry_daily_results_enhanced.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 分析结果已保存至: {output_file}")
    
    # 生成Slack消息
    slack_message = generate_slack_message(final_result)
    
    print(f"\n📤 Slack消息已生成:")
    print("-" * 60)
    print(slack_message)
    print("-" * 60)
    
    # 也保存消息到文件
    message_file = "industry_daily_slack_message_enhanced.txt"
    with open(message_file, 'w', encoding='utf-8') as f:
        f.write(slack_message)
    
    print(f"📝 Slack消息已保存至: {message_file}")
    
    print("\n" + "=" * 70)
    print("🎯 分析完成！")
    
    # 显示关键统计
    if 'etf_categories' in final_result:
        print("\n📊 细分行业统计:")
        categories_sorted = sorted(final_result['etf_categories'].items(), 
                                  key=lambda x: x[1].get('avg_score', 0), reverse=True)
        
        for category, data in categories_sorted[:5]:  # 显示前5个类别
            top_etf_name = data['top_etfs'][0]['etf_name'] if data['top_etfs'] else '无'
            top_score = data['top_etfs'][0].get('score', 0) if data['top_etfs'] else 0
            print(f"  {category}: {data['count']}个ETF，平均分: {data.get('avg_score', 0):.1f}，最佳: {top_etf_name} ({top_score:.1f})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())