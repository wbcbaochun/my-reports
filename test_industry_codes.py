#!/usr/bin/env python3
"""
测试baostock是否支持申万行业指数代码
"""

import baostock as bs
import pandas as pd
from datetime import datetime, timedelta

def test_industry_codes():
    """测试行业指数代码"""
    
    # 登录baostock
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return
    
    print("✅ Baostock登录成功")
    
    # 测试几个行业指数代码
    test_codes = [
        '881236',  # 影视院线（用户提到的）
        '881101',  # 煤炭开采
        '881175',  # 白酒
        '881226',  # 半导体
        'sh.000016',  # 上证公用（已知可用的）
        'sz.399001',  # 深证成指
    ]
    
    end_date = '2026-02-11'
    start_date = '2025-08-11'  # 6个月前
    
    for code in test_codes:
        print(f"\n测试代码: {code}")
        try:
            # 尝试获取日线数据
            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,volume",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"
            )
            
            if rs.error_code == '0':
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                df = pd.DataFrame(data_list, columns=rs.fields)
                print(f"  成功获取数据: {len(df)} 条记录")
                if len(df) > 0:
                    print(f"  日期范围: {df['date'].iloc[0]} 至 {df['date'].iloc[-1]}")
                    print(f"  最新收盘价: {df['close'].iloc[-1]}")
            else:
                print(f"  获取失败: {rs.error_msg}")
                
        except Exception as e:
            print(f"  异常: {e}")
    
    # 尝试搜索行业指数
    print("\n\n尝试搜索行业指数...")
    try:
        # 查询股票行业信息
        rs = bs.query_stock_industry()
        if rs.error_code == '0':
            industry_data = []
            while (rs.error_code == '0') & rs.next():
                industry_data.append(rs.get_row_data())
            
            industry_df = pd.DataFrame(industry_data, columns=rs.fields)
            print(f"股票行业数据: {len(industry_df)} 条")
            
            # 查看行业分布
            if 'industry' in industry_df.columns:
                industries = industry_df['industry'].unique()
                print(f"行业数量: {len(industries)}")
                print("前10个行业:")
                for i, industry in enumerate(sorted(industries)[:10]):
                    count = (industry_df['industry'] == industry).sum()
                    print(f"  {industry}: {count} 只股票")
    except Exception as e:
        print(f"搜索行业指数异常: {e}")
    
    # 登出
    bs.logout()
    print("\n✅ 测试完成")

if __name__ == "__main__":
    test_industry_codes()