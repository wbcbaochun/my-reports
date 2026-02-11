#!/usr/bin/env python3
"""
测试baostock对ETF代码的支持
"""

import baostock as bs
import pandas as pd

def test_etf_codes():
    """测试ETF代码"""
    
    # 登录baostock
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return
    
    print("✅ Baostock登录成功")
    
    # 测试不同类型的ETF代码
    test_codes = [
        # 股票ETF
        'sh.510300',  # 沪深300ETF
        'sh.510500',  # 中证500ETF
        'sz.159919',  # 沪深300ETF(深市)
        
        # 行业ETF
        'sh.512480',  # 半导体ETF
        'sh.512170',  # 医疗ETF
        
        # 债券ETF
        'sh.511010',  # 国债ETF
        
        # 黄金ETF
        'sh.518880',  # 黄金ETF
        
        # 货币ETF
        'sh.511990',  # 华宝添益
    ]
    
    end_date = '2026-02-11'
    start_date = '2026-01-11'  # 1个月数据
    
    for code in test_codes:
        print(f"\n测试ETF代码: {code}")
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
            
            print(f"  错误代码: {rs.error_code}")
            print(f"  错误信息: {rs.error_msg}")
            
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
                print(f"  获取失败")
                
        except Exception as e:
            print(f"  异常: {e}")
    
    # 登出
    bs.logout()
    print("\n✅ 测试完成")

if __name__ == "__main__":
    test_etf_codes()