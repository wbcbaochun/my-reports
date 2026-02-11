#!/usr/bin/env python3
"""
France-Visas 真实登录验证脚本
谨慎测试：只测试前3个邮箱，重试不超过两次
"""

import pandas as pd
import asyncio
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/real_login_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RealLoginResult:
    """真实登录结果"""
    email: str
    success: bool
    attempts: int
    error_type: Optional[str] = None  # password_error, captcha_required, network_error, etc.
    error_message: Optional[str] = None
    timestamp: Optional[str] = None
    page_title: Optional[str] = None
    redirect_url: Optional[str] = None
    requires_captcha: bool = False
    account_locked: bool = False
    
    def to_dict(self):
        return {
            "email": self.email,
            "success": self.success,
            "attempts": self.attempts,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "page_title": self.page_title,
            "redirect_url": self.redirect_url,
            "requires_captcha": self.requires_captcha,
            "account_locked": self.account_locked
        }

class RealLoginVerifier:
    """真实登录验证器"""
    
    def __init__(self, headless: bool = False, max_attempts: int = 2, delay_between_attempts: int = 3):
        """
        初始化验证器
        
        Args:
            headless: 是否使用无头模式
            max_attempts: 最大尝试次数
            delay_between_attempts: 尝试之间的延迟(秒)
        """
        self.headless = headless
        self.max_attempts = max_attempts
        self.delay_between_attempts = delay_between_attempts
        self.results: List[RealLoginResult] = []
        
    def load_student_emails(self, excel_path: str, limit: int = 3) -> List[str]:
        """
        从Excel文件加载学生邮箱（限制数量）
        
        Args:
            excel_path: Excel文件路径
            limit: 限制测试的邮箱数量
            
        Returns:
            邮箱列表
        """
        logger.info(f"从Excel文件加载学生邮箱: {excel_path} (限制: {limit})")
        
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
                        sample = df[col].dropna().head(3)
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
                if len(emails) >= limit:
                    break
                    
            logger.info(f"找到 {len(emails)} 个有效邮箱进行测试")
            return emails
            
        except Exception as e:
            logger.error(f"加载邮箱失败: {e}")
            raise
    
    async def _attempt_login(self, page: Page, email: str, password: str) -> Dict[str, any]:
        """
        单次登录尝试
        
        Args:
            page: Playwright页面对象
            email: 邮箱
            password: 密码
            
        Returns:
            尝试结果字典
        """
        try:
            # 导航到France-Visas登录页面
            logger.info(f"  导航到登录页面...")
            await page.goto("https://application-form.france-visas.gouv.fr/fv-fo-dde/", timeout=30000)
            
            # 等待页面加载
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # 检查当前URL - 可能已经重定向到Keycloak
            current_url = page.url
            logger.info(f"  当前URL: {current_url}")
            
            # 查找邮箱输入框
            email_input = None
            password_input = None
            login_button = None
            
            # 尝试不同的选择器
            selectors_to_try = [
                'input[type="email"]',
                'input[name="email"]',
                'input[id*="email"]',
                'input[type="text"]',
                'input'
            ]
            
            for selector in selectors_to_try:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    placeholder = await elem.get_attribute("placeholder") or ""
                    id_attr = await elem.get_attribute("id") or ""
                    name_attr = await elem.get_attribute("name") or ""
                    
                    if "email" in placeholder.lower() or "email" in id_attr.lower() or "email" in name_attr.lower():
                        email_input = elem
                        logger.info(f"  找到邮箱输入框: {selector}")
                        break
                if email_input:
                    break
            
            # 查找密码输入框
            for selector in ['input[type="password"]', 'input[name="password"]', 'input[id*="password"]']:
                elem = await page.query_selector(selector)
                if elem:
                    password_input = elem
                    logger.info(f"  找到密码输入框: {selector}")
                    break
            
            # 查找登录按钮
            for selector in ['button[type="submit"]', 'button:has-text("登录")', 'button:has-text("Login")', 'button:has-text("Se connecter")']:
                elem = await page.query_selector(selector)
                if elem:
                    login_button = elem
                    logger.info(f"  找到登录按钮: {selector}")
                    break
            
            if not email_input or not password_input:
                # 截图当前页面以便调试
                screenshot_path = f"debug_login_page_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path)
                logger.warning(f"  未找到登录表单元素，截图已保存: {screenshot_path}")
                
                # 检查页面内容
                page_content = await page.content()
                if "captcha" in page_content.lower() or "验证码" in page_content.lower():
                    return {
                        "success": False,
                        "error_type": "captcha_required",
                        "error_message": "检测到验证码要求",
                        "page_content_preview": page_content[:500]
                    }
                
                return {
                    "success": False,
                    "error_type": "form_not_found",
                    "error_message": "未找到登录表单元素",
                    "page_content_preview": page_content[:500]
                }
            
            # 填写表单
            logger.info(f"  填写邮箱: {email}")
            await email_input.fill(email)
            
            logger.info(f"  填写密码: [隐藏]")
            await password_input.fill(password)
            
            # 等待随机延迟，模拟人工操作
            await asyncio.sleep(1 + (time.time() % 2))  # 1-3秒
            
            # 点击登录
            logger.info("  点击登录按钮")
            if login_button:
                await login_button.click()
            else:
                # 如果没有找到按钮，尝试提交表单
                await page.keyboard.press("Enter")
            
            # 等待响应
            await asyncio.sleep(3)
            
            # 检查结果
            new_url = page.url
            page_title = await page.title()
            page_content = await page.content()
            
            logger.info(f"  登录后URL: {new_url}")
            logger.info(f"  页面标题: {page_title}")
            
            # 分析结果
            if "erreur" in page_content.lower() or "error" in page_content.lower():
                error_text = "检测到错误消息"
                if "mot de passe" in page_content.lower() or "password" in page_content.lower():
                    error_text = "密码错误"
                elif "compte" in page_content.lower() or "account" in page_content.lower():
                    error_text = "账户问题"
                    
                return {
                    "success": False,
                    "error_type": "login_failed",
                    "error_message": error_text,
                    "page_title": page_title,
                    "redirect_url": new_url,
                    "page_content_preview": page_content[:500]
                }
            
            # 检查是否重定向到仪表板或申请表
            if "form" in new_url.lower() or "dashboard" in new_url.lower() or "application" in new_url.lower():
                return {
                    "success": True,
                    "error_type": None,
                    "error_message": None,
                    "page_title": page_title,
                    "redirect_url": new_url
                }
            else:
                # 不确定是否成功
                return {
                    "success": False,
                    "error_type": "unknown_response",
                    "error_message": "未知响应，无法确定登录状态",
                    "page_title": page_title,
                    "redirect_url": new_url,
                    "page_content_preview": page_content[:500]
                }
                
        except Exception as e:
            logger.error(f"  登录尝试异常: {e}")
            return {
                "success": False,
                "error_type": "exception",
                "error_message": str(e)
            }
    
    async def verify_single_email(self, email: str, password: str = "Shanghai2021") -> RealLoginResult:
        """
        验证单个邮箱的登录
        
        Args:
            email: 邮箱
            password: 密码
            
        Returns:
            登录结果
        """
        logger.info(f"开始验证: {email}")
        
        attempts = 0
        final_result = None
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless, slow_mo=100)  # 慢动作模式，便于观察
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            
            try:
                for attempt in range(self.max_attempts):
                    attempts += 1
                    logger.info(f"  尝试 {attempt+1}/{self.max_attempts}")
                    
                    page = await context.new_page()
                    
                    try:
                        # 执行登录尝试
                        attempt_result = await self._attempt_login(page, email, password)
                        
                        # 分析结果
                        success = attempt_result.get("success", False)
                        error_type = attempt_result.get("error_type")
                        error_message = attempt_result.get("error_message")
                        
                        # 检查是否需要验证码
                        requires_captcha = error_type == "captcha_required"
                        
                        # 检查账户锁定迹象
                        account_locked = False
                        if error_message and ("locked" in error_message.lower() or "bloqué" in error_message.lower()):
                            account_locked = True
                        
                        if success:
                            logger.info(f"  登录成功!")
                            final_result = RealLoginResult(
                                email=email,
                                success=True,
                                attempts=attempts,
                                error_type=None,
                                error_message=None,
                                timestamp=datetime.now().isoformat(),
                                page_title=attempt_result.get("page_title"),
                                redirect_url=attempt_result.get("redirect_url"),
                                requires_captcha=requires_captcha,
                                account_locked=account_locked
                            )
                            break
                        else:
                            logger.warning(f"  登录失败: {error_message}")
                            
                            # 如果检测到验证码或账户锁定，停止重试
                            if requires_captcha or account_locked:
                                logger.warning(f"  检测到{error_type}，停止重试")
                                final_result = RealLoginResult(
                                    email=email,
                                    success=False,
                                    attempts=attempts,
                                    error_type=error_type,
                                    error_message=error_message,
                                    timestamp=datetime.now().isoformat(),
                                    page_title=attempt_result.get("page_title"),
                                    redirect_url=attempt_result.get("redirect_url"),
                                    requires_captcha=requires_captcha,
                                    account_locked=account_locked
                                )
                                break
                            
                            # 等待后重试
                            if attempt < self.max_attempts - 1:
                                logger.info(f"  等待 {self.delay_between_attempts} 秒后重试...")
                                await asyncio.sleep(self.delay_between_attempts)
                                
                    finally:
                        await page.close()
                    
                # 如果所有尝试都失败
                if final_result is None:
                    final_result = RealLoginResult(
                        email=email,
                        success=False,
                        attempts=attempts,
                        error_type="all_attempts_failed",
                        error_message=f"所有 {self.max_attempts} 次尝试都失败",
                        timestamp=datetime.now().isoformat(),
                        requires_captcha=False,
                        account_locked=False
                    )
                    
            finally:
                await context.close()
                await browser.close()
        
        self.results.append(final_result)
        return final_result
    
    async def verify_emails(self, emails: List[str], password: str = "Shanghai2021") -> List[RealLoginResult]:
        """
        验证多个邮箱
        
        Args:
            emails: 邮箱列表
            password: 密码
            
        Returns:
            结果列表
        """
        results = []
        
        for i, email in enumerate(emails):
            logger.info(f"[{i+1}/{len(emails)}] 验证邮箱: {email}")
            result = await self.verify_single_email(email, password)
            results.append(result)
            
            # 邮箱之间的延迟，避免过快请求
            if i < len(emails) - 1:
                delay = 5 + (time.time() % 3)  # 5-8秒
                logger.info(f"  等待 {delay:.1f} 秒后继续下一个邮箱...")
                await asyncio.sleep(delay)
        
        return results
    
    def generate_report(self) -> Dict[str, any]:
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
            if result.error_type:
                error_counts[result.error_type] = error_counts.get(result.error_type, 0) + 1
        
        return {
            "summary": {
                "total_emails_tested": total,
                "successful_logins": successful,
                "failed_logins": failed,
                "success_rate": f"{(successful/total)*100:.1f}%" if total > 0 else "0%",
                "requires_captcha": captcha_required,
                "account_locked": locked,
                "average_attempts": f"{sum(r.attempts for r in self.results)/total:.1f}" if total > 0 else "0"
            },
            "error_analysis": error_counts,
            "detailed_results": [r.to_dict() for r in self.results],
            "recommendations": self._generate_recommendations(),
            "timestamp": datetime.now().isoformat()
        }
        
    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recs = []
        
        success_count = sum(1 for r in self.results if r.success)
        captcha_count = sum(1 for r in self.results if r.requires_captcha)
        locked_count = sum(1 for r in self.results if r.account_locked)
        
        if success_count == 0:
            recs.append("所有登录尝试都失败，强烈建议手动验证密码有效性")
            recs.append("密码 'Shanghai2021' 可能已过期或无效")
        elif success_count < len(self.results):
            recs.append(f"{len(self.results) - success_count} 个邮箱登录失败，可能需要密码重置")
            
        if captcha_count > 0:
            recs.append(f"{captcha_count} 个账户需要验证码，自动化需要处理验证码挑战")
            
        if locked_count > 0:
            recs.append(f"检测到 {locked_count} 个账户可能被锁定，建议联系账户所有者")
            
        if success_count > 0:
            recs.append(f"{success_count} 个账户登录成功，可以继续进行表单自动化探索")
            
        # 安全性建议
        recs.append("所有学生使用相同密码存在安全风险，建议考虑密码策略更新")
        recs.append("自动化登录应谨慎进行，避免触发反爬虫机制")
        
        return recs
        
    def save_report(self, report: Dict[str, any], output_path: str = None):
        """保存报告到文件"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"real_login_report_{timestamp}.json"
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"报告已保存到: {output_path}")
        
        # 同时生成简要的文本报告
        txt_report = f"real_login_summary_{timestamp}.txt"
        with open(txt_report, 'w', encoding='utf-8') as f:
            f.write(f"France-Visas 真实登录验证报告\n")
            f.write(f"生成时间: {report['timestamp']}\n")
            f.write(f"=" * 50 + "\n\n")
            
            summary = report['summary']
            f.write(f"测试总结:\n")
            f.write(f"- 测试邮箱数: {summary['total_emails_tested']}\n")
            f.write(f"- 成功登录: {summary['successful_logins']}\n")
            f.write(f"- 失败登录: {summary['failed_logins']}\n")
            f.write(f"- 成功率: {summary['success_rate']}\n")
            f.write(f"- 需要验证码: {summary['requires_captcha']}\n")
            f.write(f"- 账户锁定: {summary['account_locked']}\n")
            f.write(f"- 平均尝试次数: {summary['average_attempts']}\n\n")
            
            if report['error_analysis']:
                f.write(f"错误分析:\n")
                for error_type, count in report['error_analysis'].items():
                    f.write(f"- {error_type}: {count} 次\n")
                f.write("\n")
            
            f.write(f"详细结果:\n")
            for result in report['detailed_results']:
                status = "✓ 成功" if result['success'] else "✗ 失败"
                f.write(f"- {result['email']}: {status}")
                if result['error_message']:
                    f.write(f" ({result['error_message']})")
                f.write(f" [尝试: {result['attempts']}次]\n")
            f.write("\n")
            
            f.write(f"建议:\n")
            for i, rec in enumerate(report['recommendations'], 1):
                f.write(f"{i}. {rec}\n")
        
        logger.info(f"简要报告已保存到: {txt_report}")
        return output_path, txt_report

async def main():
    """主函数"""
    print("=== France-Visas 真实登录验证 ===\n")
    print("注意: 此脚本将实际尝试登录France-Visas网站")
    print("      每个邮箱最多尝试2次，谨慎操作\n")
    
    # 1. 初始化验证器
    verifier = RealLoginVerifier(
        headless=False,  # 使用有界面模式，便于观察
        max_attempts=2,
        delay_between_attempts=3
    )
    print("1. 登录验证器初始化完成")
    print(f"   配置: 最大重试次数={verifier.max_attempts}, 重试延迟={verifier.delay_between_attempts}秒\n")
    
    # 2. 加载学生邮箱（限制数量）
    excel_path = "/Users/yangyan/Downloads/同步空间/HelenOA/eicar/étudiants eicar-Hélène.xlsx"
    try:
        emails = verifier.load_student_emails(excel_path, limit=3)
        print(f"2. 邮箱加载完成: {len(emails)} 个邮箱")
        for i, email in enumerate(emails):
            print(f"   邮箱 {i+1}: {email}")
        print()
        
    except Exception as e:
        print(f"2. 加载邮箱失败: {e}")
        return
    
    # 3. 确认开始测试
    print("3. 即将开始登录测试")
    print(f"   将使用密码: Shanghai2021")
    print(f"   将测试 {len(emails)} 个邮箱")
    print()
    
    confirm = input("是否继续？(y/N): ").strip().lower()
    if confirm != 'y':
        print("测试已取消")
        return
    
    # 4. 执行验证
    print(f"\n4. 开始登录验证...")
    print(f"   注意: 浏览器将打开，请勿操作浏览器窗口\n")
    
    results = await verifier.verify_emails(emails)
    
    # 5. 生成报告
    print(f"\n5. 生成验证报告...")
    report = verifier.generate_report()
    
    summary = report['summary']
    print(f"\n   === 验证总结 ===")
    print(f"   测试邮箱数: {summary['total_emails_tested']}")
    print(f"   成功登录: {summary['successful_logins']}")
    print(f"   失败登录: {summary['failed_logins']}")
    print(f"   成功率: {summary['success_rate']}")
    print(f"   需要验证码: {summary['requires_captcha']}")
    print(f"   账户锁定: {summary['account_locked']}")
    print(f"   平均尝试次数: {summary['average_attempts']}")
    
    if report['error_analysis']:
        print(f"\n   === 错误分析 ===")
        for error_type, count in report['error_analysis'].items():
            print(f"   {error_type}: {count} 次")
    
    # 6. 保存报告
    json_report, txt_report = verifier.save_report(report)
    
    print(f"\n6. 报告已保存:")
    print(f"   详细报告: {json_report}")
    print(f"   简要报告: {txt_report}")
    
    # 7. 显示建议
    print(f"\n7. 建议:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print(f"\n=== 验证完成 ===")
    
    # 8. 重要提醒
    print(f"\n⚠️  重要提醒:")
    print(f"   - 如果检测到验证码或账户锁定，请立即停止自动化测试")
    print(f"   - 建议手动验证密码有效性后再继续")
    print(f"   - 考虑安全风险：所有学生使用相同密码")

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())