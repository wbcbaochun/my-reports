#!/usr/bin/env python3
"""
调试ETF数据获取
"""

import baostock as bs
import pandas as pd

def debug_etf_data():
    """调试ETF数据"""
    
    # 登录
    lg = bs.login()
    if lg.error_code != '0':
        print("登录失败")
        return
    
    print("✅ 登录成功")
    
    # 测试一个ETF
    code = 'sh.512480'  # 半导体ETF
    start_date = '2025-08-01'
    end_date = '2026-02-10'
    
    print(f"\n获取 {code} 数据")
    print(f"时间范围: {start_date} 至 {end_date}")
    
    try:
        rs = bs.query_history_k_data_plus(
            code,
            "date,code,open,high,low,close,volume,amount",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"
        )
        
        print(f"错误代码: {rs.error_code}")
        print(f"错误信息: {rs.error_msg}")
        
        if rs.error_code == '0':
            data = []
            count = 0
            while (rs.error_code == '0') & rs.next():
                data.append(rs.get_row_data())
                count += 1
            
            print(f"获取到 {count} 条数据")
            
            if data:
                df = pd.DataFrame(data, columns=rs.fields)
                print(f"数据形状: {df.shape}")
                print("\n前5行数据:")
                print(df.head())
                
                # 检查数据类型
                print("\n数据类型:")
                print(df.dtypes)
                
                # 检查是否有缺失值
                print(f"\n缺失值统计:")
                for col in df.columns:
                    missing = df[col].isnull().sum()
                    if missing > 0:
                        print(f"  {col}: {missing} 个缺失值")
        else:
            print("数据获取失败")
            
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 登出
    bs.logout()
    print("\n✅ 调试完成")

if __name__ == "__main__":
    debug_etf_data()