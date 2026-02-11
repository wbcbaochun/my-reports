#!/usr/bin/env python3
"""
运行France-Visas登录验证测试（非交互式）
用户已选择方案A，自动执行验证
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_login_test import RealLoginVerifier
import json
from datetime import datetime

async def run_test():
    """运行登录测试"""
    print("=== 开始France-Visas登录验证测试 ===\n")
    
    # 1. 初始化验证器
    verifier = RealLoginVerifier(
        headless=False,  # 使用有界面模式，便于调试
        max_attempts=2,
        delay_between_attempts=3
    )
    
    print("配置:")
    print(f"- 最大重试次数: {verifier.max_attempts}")
    print(f"- 重试延迟: {verifier.delay_between_attempts}秒")
    print(f"- 有界面模式: {'是' if not verifier.headless else '否'}")
    print()
    
    # 2. 加载学生邮箱（只测试前3个）
    excel_path = "/Users/yangyan/Downloads/同步空间/HelenOA/eicar/étudiants eicar-Hélène.xlsx"
    try:
        emails = verifier.load_student_emails(excel_path, limit=3)
        print(f"加载 {len(emails)} 个测试邮箱:")
        for i, email in enumerate(emails):
            print(f"  {i+1}. {email}")
        print()
    except Exception as e:
        print(f"加载邮箱失败: {e}")
        return None
    
    # 3. 执行验证
    print("开始登录验证...")
    print(f"密码: Shanghai2021")
    print(f"注意: 浏览器窗口将打开，请勿手动操作\n")
    
    try:
        results = await verifier.verify_emails(emails)
        print(f"\n验证完成!\n")
    except Exception as e:
        print(f"\n验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # 4. 生成报告
    report = verifier.generate_report()
    
    # 5. 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_report = f"login_test_results_{timestamp}.json"
    txt_report = f"login_test_summary_{timestamp}.txt"
    
    with open(json_report, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成简要报告
    summary = report['summary']
    with open(txt_report, 'w', encoding='utf-8') as f:
        f.write(f"France-Visas登录验证测试报告\n")
        f.write(f"测试时间: {report['timestamp']}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("测试总结:\n")
        f.write(f"- 测试邮箱数: {summary['total_emails_tested']}\n")
        f.write(f"- 成功登录: {summary['successful_logins']}\n")
        f.write(f"- 失败登录: {summary['failed_logins']}\n")
        f.write(f"- 成功率: {summary['success_rate']}\n")
        f.write(f"- 需要验证码: {summary['requires_captcha']}\n")
        f.write(f"- 账户锁定: {summary['account_locked']}\n")
        f.write(f"- 平均尝试次数: {summary['average_attempts']}\n\n")
        
        if report['error_analysis']:
            f.write("错误分析:\n")
            for error_type, count in report['error_analysis'].items():
                f.write(f"- {error_type}: {count} 次\n")
            f.write("\n")
        
        f.write("详细结果:\n")
        for result in report['detailed_results']:
            status = "✓ 成功" if result['success'] else "✗ 失败"
            error_info = f" ({result['error_message']})" if result['error_message'] else ""
            f.write(f"- {result['email']}: {status}{error_info} [尝试: {result['attempts']}次]\n")
        f.write("\n")
        
        f.write("建议:\n")
        for i, rec in enumerate(report['recommendations'], 1):
            f.write(f"{i}. {rec}\n")
    
    print(f"报告已保存:")
    print(f"- 详细报告: {json_report}")
    print(f"- 简要报告: {txt_report}")
    
    # 6. 控制台输出总结
    print(f"\n=== 测试总结 ===")
    print(f"测试邮箱数: {summary['total_emails_tested']}")
    print(f"成功登录: {summary['successful_logins']}")
    print(f"失败登录: {summary['failed_logins']}")
    print(f"成功率: {summary['success_rate']}")
    
    if summary['requires_captcha'] > 0:
        print(f"⚠️  需要验证码: {summary['requires_captcha']} 个账户")
    
    if summary['account_locked'] > 0:
        print(f"🚨  账户锁定: {summary['account_locked']} 个账户")
    
    print(f"\n=== 建议 ===")
    for i, rec in enumerate(report['recommendations'][:5], 1):  # 只显示前5条
        print(f"{i}. {rec}")
    
    return {
        "json_report": json_report,
        "txt_report": txt_report,
        "summary": summary,
        "detailed_results": report['detailed_results']
    }

if __name__ == "__main__":
    print("France-Visas登录验证测试")
    print("用户已选择方案A，开始执行...\n")
    
    # 运行测试
    result = asyncio.run(run_test())
    
    if result:
        print(f"\n✅ 测试完成!")
        print(f"请查看报告文件获取详细信息")
    else:
        print(f"\n❌ 测试失败")
        sys.exit(1)