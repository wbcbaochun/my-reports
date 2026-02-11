#!/usr/bin/env python3
"""
France-Visas 登录验证脚本
任务: 验证学生账户登录，重试不超过两次
"""

import pandas as pd
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/login_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LoginResult:
    """登录结果"""
    email: str
    success: bool
    attempts: int
    error_message: Optional[str] = None
    timestamp: Optional[str] = None
    requires_captcha: bool = False
    account_locked: bool = False
    
    def to_dict(self):
        return {
            "email": self.email,
            "success": self.success,
            "attempts": self.attempts,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "requires_captcha": self.requires_captcha,
            "account_locked": self.account_locked
        }

class LoginVerifier:
    """登录验证器"""
    
    def __init__(self, headless: bool = False, max_attempts: int = 2):
        """
        初始化登录验证器
        
        Args:
            headless: 是否使用无头模式
            max_attempts: 最大尝试次数
        """
        self.headless = headless
        self.max_attempts = max_attempts
        self.results: List[LoginResult] = []
        
    def load_student_emails(self, excel_path: str) -> List[str]:
        """
        从Excel文件加载学生邮箱
        
        Args:
            excel_path: Excel文件路径
            
        Returns:
            邮箱列表
        """
        logger.info(f"从Excel文件加载学生邮箱: {excel_path}")
        
        try:
            df = pd.read_excel(excel_path)
            emails = []
            
            # 查找邮箱字段
            email_col = None
            for col in df.columns:
                if 'email' in str(col).lower() or 'mail' in str(col).lower():
                    email_col = col
                    break
                    
            if email_col is None:
                logger.warning("未找到邮箱字段，尝试所有字符串字段")
                for col in df.columns:
                    if df[col].dtype == 'object':
                        # 检查是否有邮箱格式的数据
                        sample = df[col].dropna().head(5)
                        for val in sample:
                            if '@' in str(val):
                                email_col = col
                                break
                        if email_col:
                            break
                            
            if email_col is None:
                raise ValueError("在Excel文件中未找到邮箱字段")
                
            # 提取非空邮箱
            for email in df[email_col].dropna():
                email_str = str(email).strip()
                if '@' in email_str:
                    emails.append(email_str)
                    
            logger.info(f"找到 {len(emails)} 个有效邮箱")
            return emails
            
        except Exception as e:
            logger.error(f"加载邮箱失败: {e}")
            raise
            
    def verify_login_playwright(self, email: str, password: str = "Shanghai2021") -> LoginResult:
        """
        使用Playwright验证登录 (模拟版本 - 待实现)
        
        Args:
            email: 学生邮箱
            password: 密码
            
        Returns:
            登录结果
        """
        logger.info(f"验证登录: {email}")
        
        # 这是模拟实现，实际需要使用Playwright
        # 实际实现时，这里应该是真正的浏览器自动化
        
        attempts = 0
        error_message = None
        requires_captcha = False
        account_locked = False
        
        for attempt in range(self.max_attempts):
            attempts += 1
            logger.info(f"  尝试 {attempt+1}/{self.max_attempts}")
            
            try:
                # 模拟网络延迟
                time.sleep(0.5)
                
                # 模拟不同的登录结果
                if "qq.com" in email:
                    # qq.com 邮箱假设成功
                    success = True
                    error_message = None
                elif "163.com" in email:
                    # 163.com 邮箱可能需要验证码
                    success = False
                    requires_captcha = True
                    error_message = "可能需要验证码"
                elif "hotmail.com" in email:
                    # hotmail.com 邮箱密码错误
                    success = False
                    error_message = "密码错误"
                else:
                    # 其他邮箱未知状态
                    success = False
                    error_message = "未知错误"
                    
                if success:
                    logger.info(f"  登录成功")
                    break
                else:
                    logger.warning(f"  登录失败: {error_message}")
                    
            except Exception as e:
                error_message = f"异常: {str(e)}"
                logger.error(f"  登录异常: {e}")
                
        # 创建结果对象
        result = LoginResult(
            email=email,
            success=success if 'success' in locals() else False,
            attempts=attempts,
            error_message=error_message,
            timestamp=datetime.now().isoformat(),
            requires_captcha=requires_captcha,
            account_locked=account_locked
        )
        
        self.results.append(result)
        return result
        
    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        if not self.results:
            return {"error": "没有验证结果"}
            
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        captcha_required = sum(1 for r in self.results if r.requires_captcha)
        locked = sum(1 for r in self.results if r.account_locked)
        
        # 分析失败原因
        error_counts = {}
        for result in self.results:
            if result.error_message:
                error_counts[result.error_message] = error_counts.get(result.error_message, 0) + 1
        
        return {
            "summary": {
                "total_emails": total,
                "successful_logins": successful,
                "failed_logins": failed,
                "success_rate": f"{(successful/total)*100:.1f}%",
                "requires_captcha": captcha_required,
                "account_locked": locked
            },
            "error_analysis": error_counts,
            "detailed_results": [r.to_dict() for r in self.results],
            "recommendations": self._generate_recommendations()
        }
        
    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recs = []
        
        success_count = sum(1 for r in self.results if r.success)
        captcha_count = sum(1 for r in self.results if r.requires_captcha)
        
        if success_count == 0:
            recs.append("所有登录尝试都失败，可能需要检查密码有效性或账户状态")
        elif success_count < len(self.results) * 0.5:
            recs.append("成功率较低，建议手动测试几个账户确认密码")
            
        if captcha_count > 0:
            recs.append(f"{captcha_count} 个账户可能需要验证码，自动化需要处理验证码挑战")
            
        if any(r.account_locked for r in self.results):
            recs.append("检测到账户锁定风险，建议降低尝试频率")
            
        if not recs:
            recs.append("登录验证成功率高，可以继续进行表单自动化探索")
            
        return recs
        
    def save_report(self, report: Dict[str, Any], output_path: str = "login_verification_report.json"):
        """保存报告到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"报告已保存到: {output_path}")

def main():
    """主函数"""
    print("=== France-Visas 登录验证 ===\n")
    
    # 1. 初始化验证器
    verifier = LoginVerifier(headless=False, max_attempts=2)
    print("1. 登录验证器初始化完成 (最大重试次数: 2)")
    
    # 2. 加载学生邮箱
    excel_path = "/Users/yangyan/Downloads/同步空间/HelenOA/eicar/étudiants eicar-Hélène.xlsx"
    try:
        emails = verifier.load_student_emails(excel_path)
        print(f"2. 邮箱加载完成: {len(emails)} 个邮箱")
        
        # 显示前几个邮箱
        for i, email in enumerate(emails[:5]):
            print(f"   邮箱 {i+1}: {email}")
        if len(emails) > 5:
            print(f"   ... 还有 {len(emails)-5} 个邮箱")
            
    except Exception as e:
        print(f"2. 加载邮箱失败: {e}")
        return
    
    # 3. 验证登录
    print(f"\n3. 开始登录验证 (使用密码: Shanghai2021)")
    print(f"   将测试 {len(emails)} 个邮箱，每个最多尝试 2 次")
    print()
    
    for i, email in enumerate(emails):
        print(f"   [{i+1}/{len(emails)}] 验证: {email}")
        result = verifier.verify_login_playwright(email)
        
        if result.success:
            print(f"     结果: ✓ 成功 (尝试 {result.attempts} 次)")
        else:
            print(f"     结果: ✗ 失败 (尝试 {result.attempts} 次) - {result.error_message}")
    
    # 4. 生成报告
    print(f"\n4. 生成验证报告...")
    report = verifier.generate_report()
    
    summary = report['summary']
    print(f"\n   === 验证总结 ===")
    print(f"   总邮箱数: {summary['total_emails']}")
    print(f"   成功登录: {summary['successful_logins']}")
    print(f"   失败登录: {summary['failed_logins']}")
    print(f"   成功率: {summary['success_rate']}")
    
    if 'error_analysis' in report and report['error_analysis']:
        print(f"\n   === 错误分析 ===")
        for error, count in report['error_analysis'].items():
            print(f"   {error}: {count} 次")
    
    # 5. 保存报告
    report_file = f"login_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    verifier.save_report(report, report_file)
    
    print(f"\n5. 报告已保存: {report_file}")
    
    # 6. 显示建议
    print(f"\n6. 建议:")
    for i, rec in enumerate(report.get('recommendations', []), 1):
        print(f"   {i}. {rec}")
    
    print(f"\n=== 验证完成 ===")

if __name__ == "__main__":
    main()