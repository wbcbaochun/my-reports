#!/usr/bin/env python3
"""
行业主题ETF映射表
替代申万细分行业指数
"""

INDUSTRY_ETFS = {
    # 科技类
    'sh.512480': '半导体ETF',
    'sh.515000': '科技ETF',
    'sh.515050': '5GETF',
    'sh.515860': '信息技术ETF',
    'sz.159807': '信息技术ETF',
    'sh.515770': '人工智能ETF',
    'sh.515880': '通信ETF',
    'sh.515030': '新能车ETF',
    
    # 医药医疗
    'sh.512170': '医疗ETF',
    'sh.512010': '医药ETF',
    'sz.159929': '医药ETF',
    'sh.515950': '创新药ETF',
    'sh.512290': '生物医药ETF',
    'sh.512220': '医疗器械ETF',
    
    # 消费类
    'sh.512690': '酒ETF',
    'sh.512600': '主要消费ETF',
    'sh.159928': '消费ETF',
    'sz.159996': '家电ETF',
    'sh.515650': '消费50ETF',
    'sh.517080': '食品饮料ETF',
    
    # 金融类
    'sh.512000': '券商ETF',
    'sh.512880': '证券ETF',
    'sz.159993': '证券ETF',
    'sh.515000': '银行ETF',
    'sz.159887': '银行ETF',
    'sh.512070': '保险主题ETF',
    
    # 周期类
    'sh.512400': '有色金属ETF',
    'sh.515220': '煤炭ETF',
    'sh.512800': '银行ETF',
    'sh.512660': '军工ETF',
    'sh.512710': '军工龙头ETF',
    'sh.515210': '钢铁ETF',
    'sh.512170': '医疗ETF',  # 重复
    
    # 新能源
    'sh.516160': '新能源ETF',
    'sh.515700': '新能源车ETF',
    'sh.515790': '光伏ETF',
    'sh.159755': '锂电池ETF',
    'sh.516780': '稀土ETF',
    
    # 基建地产
    'sh.512200': '房地产ETF',
    'sz.159707': '房地产ETF',
    'sh.516950': '基建ETF',
    'sh.516970': '建材ETF',
    
    # 其他主题
    'sh.512980': '传媒ETF',
    'sh.512000': '券商ETF',  # 重复
    'sh.515880': '通信ETF',  # 重复
    'sh.515000': '科技ETF',  # 重复
    'sh.512800': '银行ETF',  # 重复
    
    # 影视院线相关ETF (用户提到的行业)
    'sh.512980': '传媒ETF',  # 包含影视院线
    'sz.159805': '传媒ETF',
    
    # 宽基指数 (参考)
    'sh.510300': '沪深300ETF',
    'sh.510500': '中证500ETF',
    'sz.159919': '沪深300ETF',
    'sz.159922': '中证500ETF',
}

# 按行业分类整理
ETFS_BY_CATEGORY = {
    '科技': ['sh.512480', 'sh.515000', 'sh.515050', 'sh.515860', 'sz.159807', 'sh.515770'],
    '医药': ['sh.512170', 'sh.512010', 'sz.159929', 'sh.515950', 'sh.512290', 'sh.512220'],
    '消费': ['sh.512690', 'sh.512600', 'sz.159928', 'sz.159996', 'sh.515650', 'sh.517080'],
    '金融': ['sh.512000', 'sh.512880', 'sz.159993', 'sh.515000', 'sz.159887', 'sh.512070'],
    '周期': ['sh.512400', 'sh.515220', 'sh.512800', 'sh.512660', 'sh.512710', 'sh.515210'],
    '新能源': ['sh.516160', 'sh.515700', 'sh.515790', 'sz.159755', 'sh.516780'],
    '基建地产': ['sh.512200', 'sz.159707', 'sh.516950', 'sh.516970'],
    '其他主题': ['sh.512980', 'sz.159805'],
}

def get_etf_list():
    """获取ETF列表"""
    return INDUSTRY_ETFS

def get_etf_by_category(category):
    """按分类获取ETF"""
    return ETFS_BY_CATEGORY.get(category, [])

def get_etf_name(code):
    """根据代码获取ETF名称"""
    return INDUSTRY_ETFS.get(code, f"未知ETF({code})")

if __name__ == "__main__":
    print(f"行业主题ETF数量: {len(INDUSTRY_ETFS)}")
    print("\nETF分类统计:")
    for category, codes in ETFS_BY_CATEGORY.items():
        print(f"  {category}: {len(codes)} 个ETF")
    
    print("\n前10个ETF:")
    for i, (code, name) in enumerate(list(INDUSTRY_ETFS.items())[:10]):
        print(f"{i+1:2d}. {code}: {name}")