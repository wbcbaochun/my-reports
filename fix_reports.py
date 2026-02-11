#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复现有报告文件的HTML格式
将纯文本报告转换为格式良好的HTML
"""

import os
import html
import re
from pathlib import Path

REPORTS_DIR = Path(__file__).parent / "reports"

def escape_html_content(text):
    """转义HTML特殊字符，同时保留Unicode表情符号"""
    # 首先进行HTML转义
    escaped = html.escape(text)
    # 恢复常见的Unicode表情符号（它们不需要被转义）
    # 实际上html.escape不会转义非ASCII字符，所以表情符号应该没问题
    return escaped

def create_html_report(content, title, timestamp):
    """创建HTML格式的报告"""
    # 将时间戳格式化为可读形式：YYYY-MM-DD_HH-MM → YYYY-MM-DD HH:MM
    display_time = timestamp.replace('_', ' ')
    
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - OpenClaw 分析报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .report-container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        }}
        
        .report-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        
        .report-title {{
            font-size: 2.5rem;
            color: #333;
            margin-bottom: 10px;
        }}
        
        .report-meta {{
            color: #666;
            font-size: 1rem;
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }}
        
        .report-content {{
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
            font-size: 0.95rem;
            line-height: 1.8;
            white-space: pre-wrap;
            word-wrap: break-word;
            background: #f8f9fa;
            padding: 30px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
            overflow-x: auto;
        }}
        
        .report-footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }}
        
        .emoji {{
            font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif;
        }}
        
        .back-link {{
            display: inline-block;
            margin-top: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .back-link:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 20px 10px;
            }}
            
            .report-container {{
                padding: 25px 15px;
            }}
            
            .report-title {{
                font-size: 1.8rem;
            }}
            
            .report-content {{
                padding: 20px;
                font-size: 0.85rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <header class="report-header">
            <h1 class="report-title">{title}</h1>
            <div class="report-meta">
                <span>📅 {display_time}</span>
                <span>📊 OpenClaw 自动化生成</span>
            </div>
        </header>
        
        <main>
            <div class="report-content">{content}</div>
        </main>
        
        <footer class="report-footer">
            <p>由 OpenClaw 自动化生成 • 报告时间: {display_time}</p>
            <a href="../" class="back-link">← 返回报告列表</a>
        </footer>
    </div>
</body>
</html>"""
    return html_template

def parse_filename(filename):
    """解析文件名，提取时间戳和标题
    格式: YYYY-MM-DD_HH-MM_title.html
    """
    # 移除扩展名
    name_without_ext = filename[:-5]  # 移除 .html
    parts = name_without_ext.split('_', 2)  # 最多分割成3部分
    if len(parts) >= 3:
        timestamp = f"{parts[0]}_{parts[1]}"  # YYYY-MM-DD_HH-MM
        title = parts[2]
    elif len(parts) == 2:
        timestamp = f"{parts[0]}_{parts[1]}"
        title = "未命名报告"
    else:
        timestamp = "未知时间"
        title = parts[0] if parts else "未命名报告"
    
    # 将标题中的下划线替换回空格
    title = title.replace('_', ' ')
    return timestamp, title

def fix_existing_reports():
    """修复现有的所有报告文件"""
    if not REPORTS_DIR.exists():
        print(f"错误: 报告目录不存在: {REPORTS_DIR}")
        return
    
    html_files = list(REPORTS_DIR.glob("*.html"))
    print(f"找到 {len(html_files)} 个HTML报告文件")
    
    fixed_count = 0
    for filepath in html_files:
        filename = filepath.name
        print(f"处理: {filename}")
        
        # 跳过已经修复的文件（检查是否包含完整的HTML结构）
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 如果文件已经包含完整的HTML标签，跳过
        if '<!DOCTYPE html>' in content or '<html' in content:
            print(f"  ⏭️  已跳过（已经是HTML格式）")
            continue
        
        # 解析文件名获取元数据
        timestamp, title = parse_filename(filename)
        
        # 转义内容中的HTML特殊字符
        escaped_content = escape_html_content(content)
        
        # 生成新的HTML内容
        html_content = create_html_report(escaped_content, title, timestamp)
        
        # 备份原始文件（可选）
        backup_path = filepath.with_suffix('.html.backup')
        if not backup_path.exists():
            filepath.rename(backup_path)
            print(f"  💾 已备份原始文件: {backup_path.name}")
        
        # 写入新的HTML内容
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  ✅ 已修复: {filename}")
        fixed_count += 1
    
    print(f"\n修复完成！总共修复了 {fixed_count} 个文件")
    
    # 更新索引
    print("\n🔄 正在更新索引...")
    os.system(f"cd {REPORTS_DIR.parent} && bash update_index.sh")
    
    # 提交更改到Git
    print("\n📤 正在提交更改到Git...")
    os.chdir(REPORTS_DIR.parent)
    os.system('git add .')
    os.system('git commit -m "修复报告HTML格式" --quiet')
    
    # 推送到远程仓库
    print("🚀 正在推送到GitHub...")
    os.system('git push origin main')
    
    print(f"\n🎉 所有报告已修复！")
    print(f"🌐 GitHub Pages 将在几分钟后更新")

if __name__ == "__main__":
    fix_existing_reports()