#!/usr/bin/env python3
"""
探索baostock支持的行业分类和细分行业
"""

import baostock as bs
import pandas as pd

def explore_industry_classification():
    """探索行业分类"""
    
    # 登录baostock
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return
    
    print("✅ Baostock登录成功")
    print("\n=== 探索行业分类 ===")
    
    # 尝试获取行业分类数据
    # baostock可能通过query_all_stock接口获取股票列表，然后按行业筛选
    # 或者有专门的行业分类API
    
    # 方法1: 获取所有A股股票，然后按行业统计
    print("\n1. 获取A股股票列表...")
    rs = bs.query_all_stock('2026-02-11')
    if rs.error_code != '0':
        print(f"获取股票列表失败: {rs.error_msg}")
        bs.logout()
        return
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    print(f"获取到 {len(df)} 只股票")
    
    # 查看股票代码格式
    print(f"\n股票代码示例:")
    print(df['code'].head(10).tolist())
    
    # 方法2: 尝试获取行业板块数据
    print("\n2. 尝试获取行业板块数据...")
    
    # baostock的query_stock_industry接口
    try:
        rs = bs.query_stock_industry()
        if rs.error_code == '0':
            industry_data = []
            while (rs.error_code == '0') & rs.next():
                industry_data.append(rs.get_row_data())
            
            industry_df = pd.DataFrame(industry_data, columns=rs.fields)
            print(f"获取到行业数据 {len(industry_df)} 条")
            print(f"行业字段: {industry_df.columns.tolist()}")
            
            # 查看有哪些行业分类
            if 'industry' in industry_df.columns:
                industries = industry_df['industry'].unique()
                print(f"\n行业分类 ({len(industries)} 种):")
                for i, industry in enumerate(sorted(industries)[:20]):  # 显示前20个
                    print(f"  {i+1:2d}. {industry}")
                if len(industries) > 20:
                    print(f"  ... 等 {len(industries)} 个行业")
            
            if 'industryClassification' in industry_df.columns:
                classifications = industry_df['industryClassification'].unique()
                print(f"\n行业分类标准 ({len(classifications)} 种):")
                for classification in classifications:
                    print(f"  • {classification}")
        else:
            print(f"获取行业数据失败: {rs.error_msg}")
    except Exception as e:
        print(f"查询行业数据异常: {e}")
    
    # 方法3: 尝试获取指数列表
    print("\n3. 尝试获取指数列表...")
    try:
        rs = bs.query_sz50_stocks()
        if rs.error_code == '0':
            sz50_data = []
            while (rs.error_code == '0') & rs.next():
                sz50_data.append(rs.get_row_data())
            sz50_df = pd.DataFrame(sz50_data, columns=rs.fields)
            print(f"上证50成分股: {len(sz50_df)} 只")
        
        # 还有其他指数：hs300, sz50, zz500等
        indices = ['sz50', 'hs300', 'zz500']
        for idx in indices:
            try:
                rs = getattr(bs, f'query_{idx}_stocks')()
                if rs.error_code == '0':
                    data = []
                    while (rs.error_code == '0') & rs.next():
                        data.append(rs.get_row_data())
                    idx_df = pd.DataFrame(data, columns=rs.fields)
                    print(f"{idx.upper()}成分股: {len(idx_df)} 只")
            except:
                pass
    except Exception as e:
        print(f"获取指数数据异常: {e}")
    
    # 登出
    bs.logout()
    print("\n✅ 探索完成")

if __name__ == "__main__":
    explore_industry_classification()