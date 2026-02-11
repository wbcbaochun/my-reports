#!/usr/bin/env python3
"""测试Playwright基本功能"""

import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    """测试浏览器启动"""
    print("测试Playwright浏览器启动...")
    
    try:
        async with async_playwright() as p:
            # 尝试启动Chromium
            print("启动Chromium浏览器...")
            browser = await p.chromium.launch(headless=False)
            print("✓ Chromium启动成功")
            
            # 创建页面
            page = await browser.new_page()
            print("✓ 页面创建成功")
            
            # 访问测试页面
            await page.goto("https://example.com")
            title = await page.title()
            print(f"✓ 页面访问成功: {title}")
            
            # 截图
            await page.screenshot(path="test_screenshot.png")
            print("✓ 截图保存成功: test_screenshot.png")
            
            # 关闭浏览器
            await browser.close()
            print("✓ 浏览器关闭成功")
            
            return True
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Playwright 功能测试 ===\n")
    
    # 运行异步测试
    success = asyncio.run(test_browser())
    
    if success:
        print("\n✓ Playwright测试通过！可以开始自动化开发")
    else:
        print("\n✗ Playwright测试失败，需要检查安装")
        print("\n可能的解决方案:")
        print("1. 重新安装Playwright: pip install --upgrade playwright")
        print("2. 安装浏览器驱动: python -m playwright install chromium")
        print("3. 检查系统依赖: python -m playwright install-deps")