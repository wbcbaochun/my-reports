#!/bin/bash

# save_report.sh - 自动保存报告并更新 GitHub Pages
# 用法: bash save_report.sh "报告内容" "报告标题"
# 或: bash save_report.sh /path/to/report.html "报告标题"

set -e  # 遇到错误立即退出

# 检查参数数量
if [ $# -lt 2 ]; then
    echo "错误: 需要两个参数"
    echo "用法: $0 \"报告内容或文件路径\" \"报告标题\""
    exit 1
fi

CONTENT="$1"
TITLE="$2"
REPORTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/reports"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 生成安全文件名：替换空格为下划线，保留中文字符和其他常用字符
SAFE_TITLE=$(echo "$TITLE" | sed -e 's/[\/:*?"<>|]//g' -e 's/ /_/g')
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
FILENAME="${TIMESTAMP}_${SAFE_TITLE}.html"
FILEPATH="$REPORTS_DIR/$FILENAME"

# 创建reports目录（如果不存在）
mkdir -p "$REPORTS_DIR"

echo "📝 正在保存报告: $TITLE"
echo "📁 文件路径: $FILEPATH"

# 检查第一个参数是文件路径还是内容字符串
if [ -f "$CONTENT" ]; then
    echo "📄 检测到文件路径，正在复制文件..."
    cp "$CONTENT" "$FILEPATH"
else
    echo "📄 检测到内容字符串，正在写入文件..."
    echo "$CONTENT" > "$FILEPATH"
fi

echo "✅ 报告已保存到: $FILEPATH"

# 重新生成 index.html
echo "🔄 正在更新 index.html..."
"$BASE_DIR/update_index.sh"

# Git 操作
echo "📤 正在提交到 Git..."
cd "$BASE_DIR"

# 检查是否在git仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⚠️  警告: 当前目录不是git仓库"
    exit 1
fi

# 添加所有更改
git add .

# 提交更改
COMMIT_MSG="自动添加报告: $TITLE ($TIMESTAMP)"
if git commit -m "$COMMIT_MSG" --quiet; then
    echo "✅ Git 提交成功: $COMMIT_MSG"
else
    echo "ℹ️  没有需要提交的更改"
fi

# 推送到远程仓库（如果已配置）
if git remote | grep -q origin; then
    echo "🚀 正在推送到远程仓库..."
    if git push origin main; then
        echo "✅ 推送成功!"
        echo "🌐 GitHub Pages 将在几分钟后更新"
        echo "🔗 访问地址: https://$(git config --get remote.origin.url | sed -n 's|.*github.com/||p' | sed 's/.git$//' | sed 's|https://||' | sed 's|git@github.com:||')"
    else
        echo "❌ 推送失败，请检查网络连接和GitHub Token配置"
        echo "ℹ️  本地提交已完成，请手动推送或配置远程仓库"
    fi
else
    echo "ℹ️  未配置远程仓库，跳过推送"
    echo "📋 请按照以下步骤配置GitHub Pages:"
    echo "   1. 在GitHub上创建仓库: https://github.com/new"
    echo "   2. 运行: git remote add origin https://github.com/你的用户名/my-reports.git"
    echo "   3. 运行: git branch -M main"
    echo "   4. 获取GitHub Token并配置免密推送"
fi

echo ""
echo "🎉 报告发布完成!"
echo "📊 标题: $TITLE"
echo "📅 时间: $TIMESTAMP"
echo "📁 文件: $FILENAME"
echo "🌐 请等待几分钟后访问 GitHub Pages"