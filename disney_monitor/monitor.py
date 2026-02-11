#!/usr/bin/env python3
"""
东京迪士尼乐园排队时间监测脚本
每小时抓取前5大热门项目的排队数据并保存到CSV文件
仅在监测时段内执行(08:00-20:00 Asia/Shanghai)
"""

import json
import csv
import os
import sys
import time
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

# 配置
PARK_ID = 274  # 东京迪士尼乐园
DATA_URL = f"https://queue-times.com/parks/{PARK_ID}/queue_times.json"
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(DATA_DIR, "wait_times.csv")

# 监测时段配置 (Asia/Shanghai时间)
MONITOR_START_HOUR = 8   # 早上8点开始
MONITOR_END_HOUR = 20    # 晚上8点结束

# 前5大热门项目定义 (ID, 名称)
TOP_ATTRACTIONS = [
    {"id": 8255, "name": "Enchanted Tale of Beauty and the Beast", "chinese_name": "美女与野兽的魔法物语"},
    {"id": 7996, "name": "Splash Mountain", "chinese_name": "飞溅山"},
    {"id": 7994, "name": "Big Thunder Mountain", "chinese_name": "巨雷山"},
    {"id": 8008, "name": "Pooh's Hunny Hunt", "chinese_name": "小熊维尼猎蜜记"},
    {"id": 8005, "name": "Haunted Mansion", "chinese_name": "幽灵公馆"}
]

def is_within_monitor_hours():
    """检查当前时间是否在监测时段内"""
    # 获取Asia/Shanghai当前时间
    # 注意: datetime.now()默认是本地时间，如果系统时区设置正确就是上海时间
    now = datetime.now()
    current_hour = now.hour
    
    # 检查是否在监测时段内
    if MONITOR_START_HOUR <= current_hour < MONITOR_END_HOUR:
        return True
    else:
        print(f"当前时间 {now.strftime('%Y-%m-%d %H:%M:%S')} 不在监测时段内 ({MONITOR_START_HOUR}:00-{MONITOR_END_HOUR}:00)")
        return False

def fetch_wait_times():
    """获取排队时间数据"""
    try:
        # 添加请求头避免被拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        req = urllib.request.Request(DATA_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except urllib.error.URLError as e:
        print(f"网络错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None
    except Exception as e:
        print(f"未知错误: {e}")
        return None

def extract_top_attractions(data):
    """提取前5大热门项目的数据"""
    if not data or 'rides' not in data:
        return []
    
    # 创建ID到项目的映射
    rides_dict = {}
    for ride in data['rides']:
        rides_dict[ride['id']] = ride
    
    # 提取前5大项目数据
    results = []
    for attraction in TOP_ATTRACTIONS:
        ride_id = attraction['id']
        if ride_id in rides_dict:
            ride = rides_dict[ride_id]
            results.append({
                'id': ride_id,
                'name': attraction['name'],
                'chinese_name': attraction['chinese_name'],
                'wait_time': ride.get('wait_time', 0),
                'is_open': ride.get('is_open', False),
                'last_updated': ride.get('last_updated', '')
            })
        else:
            # 如果没找到，添加默认值
            results.append({
                'id': ride_id,
                'name': attraction['name'],
                'chinese_name': attraction['chinese_name'],
                'wait_time': 0,
                'is_open': False,
                'last_updated': ''
            })
    
    return results

def save_to_csv(attractions_data):
    """保存数据到CSV文件"""
    # 检查文件是否存在，如果不存在则创建并写入表头
    file_exists = os.path.exists(CSV_FILE)
    
    # 当前时间戳
    timestamp = datetime.now(timezone.utc).isoformat()
    local_time = datetime.now().isoformat()
    
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp_utc', 'timestamp_local', 'attraction_id', 'attraction_name', 
                     'chinese_name', 'wait_time', 'is_open', 'last_updated']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for attraction in attractions_data:
            writer.writerow({
                'timestamp_utc': timestamp,
                'timestamp_local': local_time,
                'attraction_id': attraction['id'],
                'attraction_name': attraction['name'],
                'chinese_name': attraction['chinese_name'],
                'wait_time': attraction['wait_time'],
                'is_open': attraction['is_open'],
                'last_updated': attraction['last_updated']
            })
    
    print(f"数据已保存到 {CSV_FILE}")

def main():
    print(f"开始获取东京迪士尼乐园排队数据... (时间: {datetime.now().isoformat()})")
    
    # 检查是否在监测时段内
    if not is_within_monitor_hours():
        print(f"跳过执行: 当前时间不在监测时段内 ({MONITOR_START_HOUR}:00-{MONITOR_END_HOUR}:00)")
        sys.exit(0)
    
    # 获取数据
    data = fetch_wait_times()
    if not data:
        print("获取数据失败")
        sys.exit(1)
    
    # 提取前5大项目数据
    attractions = extract_top_attractions(data)
    if not attractions:
        print("提取项目数据失败")
        sys.exit(1)
    
    # 打印结果
    print("\n前5大热门项目当前状态:")
    print("-" * 80)
    for attr in attractions:
        status = "开放" if attr['is_open'] else "关闭"
        print(f"{attr['chinese_name']} ({attr['name']}):")
        print(f"  等待时间: {attr['wait_time']} 分钟 | 状态: {status}")
        if attr['last_updated']:
            print(f"  最后更新: {attr['last_updated']}")
        print()
    
    # 保存到CSV
    save_to_csv(attractions)
    
    # 检查是否有项目等待时间异常（比如超过120分钟）
    for attr in attractions:
        if attr['is_open'] and attr['wait_time'] > 120:
            print(f"警告: {attr['chinese_name']} 等待时间超过120分钟 ({attr['wait_time']}分钟)")
    
    print("监测完成")

if __name__ == "__main__":
    main()