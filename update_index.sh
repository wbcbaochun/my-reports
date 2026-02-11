#!/bin/bash

# update_index_simple.sh - 重新生成 index.html 文件（简化版）

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="$BASE_DIR/reports"
INDEX_FILE="$BASE_DIR/index.html"

echo "📊 正在扫描报告文件..."

# 检查reports目录是否存在
if [ ! -d "$REPORTS_DIR" ]; then
    echo "⚠️  reports 目录不存在，创建空目录"
    mkdir -p "$REPORTS_DIR"
fi

# 获取所有HTML文件，按时间倒序排序（最新的在前）
REPORT_FILES=$(find "$REPORTS_DIR" -name "*.html" -type f 2>/dev/null | sort -r)

# 统计信息
TOTAL_REPORTS=$(echo "$REPORT_FILES" | wc -l | tr -d ' ')
LATEST_DATE="无"

if [ $TOTAL_REPORTS -gt 0 ]; then
    # 获取最新文件的日期（第一个文件）
    latest_file=$(echo "$REPORT_FILES" | head -1)
    filename=$(basename "$latest_file")
    # 文件名格式: YYYY-MM-DD_HH-MM_title.html
    LATEST_DATE=$(echo "$filename" | cut -d'_' -f1)
fi

echo "✅ 找到 $TOTAL_REPORTS 个报告文件"
echo "🕒 最新报告日期: $LATEST_DATE"

# 生成报告列表的HTML
REPORT_LIST_HTML=""

if [ $TOTAL_REPORTS -eq 0 ]; then
    REPORT_LIST_HTML='<div id="empty-state" class="empty-state"><h3>暂无报告</h3><p>还没有任何分析报告发布到这里。</p><p>OpenClaw 会在生成新报告后自动更新此页面。</p></div>'
else
    REPORT_LIST_HTML='<ul id="reports-list">'
    
    while IFS= read -r file; do
        filename=$(basename "$file")
        
        # 解析文件名格式: YYYY-MM-DD_HH-MM_title.html
        filedate=$(echo "$filename" | cut -d'_' -f1)
        filetime=$(echo "$filename" | cut -d'_' -f2)
        filetitle=$(echo "$filename" | cut -d'_' -f3- | sed 's/\.html$//' | sed 's/_/ /g')
        
        # 格式化日期和时间
        display_date="${filedate}"
        display_time=$(echo "$filetime" | sed 's/-/:/')
        
        # 创建报告描述（基于标题）
        if [[ "$filetitle" == *"迪士尼"* ]]; then
            description="东京迪士尼乐园排队时间趋势分析报告，包含游玩建议和图表。"
        elif [[ "$filetitle" == *"A股"* ]] || [[ "$filetitle" == *"行业"* ]]; then
            description="基于技术分析的A股行业板块研究报告，识别潜在投资机会。"
        elif [[ "$filetitle" == *"新闻"* ]]; then
            description="每日自动搜集的日本、IT、投资领域最新新闻动向。"
        else
            description="OpenClaw 自动生成的详细分析报告。"
        fi
        
        REPORT_LIST_HTML+="
        <li class=\"report-item\">
            <div class=\"report-title\">${filetitle}</div>
            <div class=\"report-meta\">
                <span>📅 ${display_date}</span>
                <span>🕒 ${display_time}</span>
                <span>📄 ${filename}</span>
            </div>
            <p>${description}</p>
            <a href=\"reports/${filename}\" class=\"report-link\" target=\"_blank\">查看完整报告 →</a>
        </li>"
    done <<< "$REPORT_FILES"
    
    REPORT_LIST_HTML+='</ul>'
fi

# 生成完整的 index.html
cat > "$INDEX_FILE" << EOF
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>分析报告中心</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        header {
            text-align: center;
            margin-bottom: 50px;
            color: white;
        }
        
        h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 300;
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 40px 0;
            flex-wrap: wrap;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            min-width: 200px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            display: block;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }
        
        .reports-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .section-title {
            font-size: 2rem;
            color: #333;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }
        
        #reports-list {
            list-style: none;
        }
        
        .report-item {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            border-left: 5px solid #667eea;
            transition: all 0.3s ease;
        }
        
        .report-item:hover {
            transform: translateX(10px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .report-title {
            font-size: 1.5rem;
            color: #333;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .report-title::before {
            content: "📊";
            font-size: 1.2rem;
        }
        
        .report-meta {
            display: flex;
            gap: 20px;
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 15px;
        }
        
        .report-meta span {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .report-link {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .report-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        
        .empty-state h3 {
            font-size: 1.8rem;
            margin-bottom: 15px;
            color: #333;
        }
        
        .footer {
            text-align: center;
            margin-top: 50px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            h1 {
                font-size: 2.2rem;
            }
            
            .stat-card {
                min-width: 150px;
            }
            
            .reports-section {
                padding: 25px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📈 分析报告中心</h1>
            <p class="subtitle">OpenClaw 自动生成的报告聚合页面</p>
            
            <div class="stats">
                <div class="stat-card">
                    <span class="stat-number" id="total-reports">${TOTAL_REPORTS}</span>
                    <span class="stat-label">总报告数</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="recent-reports">${TOTAL_REPORTS}</span>
                    <span class="stat-label">报告总数</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="latest-date">${LATEST_DATE}</span>
                    <span class="stat-label">最新报告</span>
                </div>
            </div>
        </header>
        
        <main class="reports-section">
            <h2 class="section-title">📋 所有报告列表</h2>
            
            ${REPORT_LIST_HTML}
        </main>
        
        <div class="footer">
            <p>由 OpenClaw 自动化生成 • 最后更新: $(date '+%Y年%m月%d日 %H:%M')</p>
            <p>GitHub Pages 自动部署 • 访问 <a href="https://github.com/wbcbaochun/my-reports" style="color: white; text-decoration: underline;">仓库</a></p>
        </div>
    </div>

    <script>
        // 简单的交互效果
        document.addEventListener('DOMContentLoaded', function() {
            // 为所有报告链接添加点击动画
            const links = document.querySelectorAll('.report-link');
            links.forEach(link => {
                link.addEventListener('click', function(e) {
                    this.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        this.style.transform = '';
                    }, 200);
                });
            });
            
            // 为报告项添加悬停效果增强
            const reportItems = document.querySelectorAll('.report-item');
            reportItems.forEach(item => {
                item.addEventListener('mouseenter', function() {
                    this.style.boxShadow = '0 15px 35px rgba(0,0,0,0.15)';
                });
                
                item.addEventListener('mouseleave', function() {
                    this.style.boxShadow = '0 5px 15px rgba(0,0,0,0.05)';
                });
            });
        });
    </script>
</body>
</html>
EOF

echo "✅ index.html 已重新生成"
echo "📊 总报告数: $TOTAL_REPORTS"
echo "📁 索引文件: $INDEX_FILE"