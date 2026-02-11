#!/bin/bash
# France-Visas 自动化环境安装脚本

echo "=== 安装 France-Visas 自动化环境 ==="

# 1. 检查Python环境
echo "1. 检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 2. 检查pip
echo "2. 检查pip..."
pip3 --version
if [ $? -ne 0 ]; then
    echo "警告: pip3 未安装，尝试安装..."
    python3 -m ensurepip --upgrade
fi

# 3. 安装必要的Python包
echo "3. 安装Python依赖包..."
pip3 install pandas openpyxl

# 4. 检查Playwright
echo "4. 检查Playwright..."
python3 -c "import playwright" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装Playwright..."
    pip3 install playwright
else
    echo "Playwright 已安装"
fi

# 5. 安装浏览器驱动
echo "5. 安装浏览器驱动..."
python3 -m playwright install chromium
python3 -m playwright install-deps chromium  # Linux可能需要

# 6. 验证安装
echo "6. 验证安装..."
echo "Python包:"
python3 -c "import pandas; import playwright; print('✓ pandas', pandas.__version__); print('✓ playwright', playwright.__version__)"

echo "7. 创建必要的目录..."
mkdir -p logs
mkdir -p data
mkdir -p config

echo "8. 设置完成!"
echo ""
echo "下一步:"
echo "1. 测试环境: python3 test_environment.py"
echo "2. 运行演示: python3 framework.py"
echo "3. 开始开发!"