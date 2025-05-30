#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import signal
from DrissionPage import Chromium, ChromiumOptions

class XvfbManager:
    """Xvfb虚拟显示器管理器"""

    def __init__(self, display=':99', screen='0', resolution='1920x1080x24'):
        self.display = display
        self.screen = screen
        self.resolution = resolution
        self.xvfb_process = None

    def start(self):
        """启动Xvfb虚拟显示器"""
        try:
            # 清理可能存在的Xvfb进程
            self.cleanup()

            print(f"启动Xvfb虚拟显示器: DISPLAY={self.display}")

            # 启动Xvfb，加上了GLX扩展，这可能是之前成功的关键
            cmd = ['Xvfb', self.display, '-screen', self.screen, self.resolution, '-ac', '+extension', 'GLX']
            self.xvfb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )

            # 设置环境变量
            os.environ['DISPLAY'] = self.display

            # 等待Xvfb启动
            time.sleep(3)

            # 检查Xvfb是否正常运行
            if self.xvfb_process.poll() is None:
                print(f"✅ Xvfb启动成功，DISPLAY={self.display}")
                return True
            else:
                stderr_output = self.xvfb_process.stderr.read().decode()
                print(f"❌ Xvfb启动失败: {stderr_output}")
                return False

        except Exception as e:
            print(f"❌ 启动Xvfb时出错: {e}")
            return False

    def stop(self):
        """停止Xvfb"""
        if self.xvfb_process and self.xvfb_process.poll() is None:
            print("停止Xvfb进程...")
            self.xvfb_process.terminate()
            try:
                self.xvfb_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.xvfb_process.kill()

    def cleanup(self):
        """清理残留的Xvfb进程"""
        try:
            subprocess.run(['pkill', '-f', f'Xvfb.*{self.display}'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
            time.sleep(1)
        except:
            pass

def create_chrome_options():
    """创建Chrome选项配置"""
    options = ChromiumOptions()

    # 基础选项（保留有助于稳定性和反检测的）
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-dev-shm-usage') # 避免共享内存问题
    options.set_argument('--disable-gpu') # 因为没有物理GPU
    options.set_argument('--window-size=1920,1080') # 截图所需分辨率
    options.set_argument('--remote-debugging-port=9222') # 用于DrissionPage连接
    options.set_argument('--accept-lang','zh-CN,zh;q=0.9,en;q=0.8')

    # 其他一些有助于稳定性的参数
    options.set_argument('--no-first-run')
    options.set_argument('--no-default-browser-check')
    options.set_argument('--disable-default-apps')
    options.set_argument('--disable-popup-blocking')
    options.set_argument('--disable-translate')
    options.set_argument('--disable-background-timer-throttling')
    options.set_argument('--disable-renderer-backgrounding')
    options.set_argument('--disable-backgrounding-occluded-windows')
    options.set_argument('--disable-extensions') # 禁用扩展，减少指纹

    # 伪装User-Agent，保持与Chrome版本一致
    options.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # 注意：这里的Chrome版本是120.0.0.0，而你的实际是137。
    # 为了更真实，你可以尝试将 User-Agent 中的版本号改成你的实际Chrome版本，如 137.0.0.0
    # options.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')


    # 指定Chrome路径（如果需要），确保路径正确
    chrome_path = '/usr/bin/google-chrome'
    if os.path.exists(chrome_path):
        options.set_browser_path(chrome_path)

    # ！！！重要：不设置headless()，让Xvfb处理显示！！！
    # options.headless()

    return options

def test_douyin_page():
    """测试访问抖音页面并执行登录流程"""
    xvfb = None
    browser = None
    page = None

    try:
        print("="*50)
        print("开始 DrissionPage + Xvfb 访问抖音页面测试")
        print("="*50)

        # 1. 启动Xvfb
        xvfb = XvfbManager()
        if not xvfb.start():
            print("❌ Xvfb启动失败，退出测试")
            return False

        # 2. 创建浏览器实例
        print("\n🚀 创建浏览器实例...")
        options = create_chrome_options()
        browser = Chromium(options)

        # 获取页面对象
        page = browser.latest_tab

        print("✅ 浏览器创建成功")
        
        # --- 检查 Accept-Language 头是否正确发送 ---
        print("\n🔍 正在检查 Accept-Language 头是否发送正确...")
        page.get('https://httpbin.org/headers')
        time.sleep(3) # 等待页面加载，确保所有头信息都已显示
        
        headers_content = page.ele('tag:body').text
        print("--- 浏览器发送的 HTTP 请求头 (来自 httpbin.org) ---")
        print(headers_content)
        print("-------------------------------------------------")

        # 3. 访问抖音页面
        # 按照您的要求，使用此URL，因为它会自动弹出登录框
        douyin_url = 'https://www.douyin.com/?vid=7497916567561309466&recommend=1' 
        print(f"\n🌐 访问抖音页面: {douyin_url} ...")
        page.get(douyin_url)

        # 等待页面加载，抖音页面内容动态较多，需要较长等待
        print("⏳ 等待页面内容加载... (建议等待10-15秒或更长，等待登录框弹出)")
        time.sleep(15) # 增加等待时间，确保动态内容加载完成，包括登录框的弹出

        # 4. 检查页面是否成功加载抖音内容
        title = page.title
        current_url = page.url
        print(f"📄 页面标题: {title}")
        print(f"🔗 当前URL: {current_url}")

        if '抖音' in title or 'douyin' in title.lower() or 'aweme' in current_url.lower():
            print("✅ 成功访问抖音页面！")

            # 在这里，直接开始执行登录流程，因为您已确认登录框会自动弹出
            print("\n--- 开始抖音登录流程 ---")

            # 1. 定位手机号国家组件并输入86
            print("尝试定位手机号国家组件并输入86...")
            # 您提供的input元素：<input size="2" class="B7N1ZHMr" autocomplete="off" role="combobox" tabindex="0" aria-owns="select-ul" aria-activedescendant="areacode_item_0" aria-label="国家/地区" maxlength="5" type="text" value="+1" name="web-login-area-code-input">
            country_code_input = page.ele('xpath://input[@name="web-login-area-code-input"]')
            
            # 使用DrissionPage的等待机制，等待元素出现，增加稳定性
            if not country_code_input:
                print("⚠️ 国家/地区输入框未立即找到，尝试等待...")
                country_code_input = page.wait.ele_appear('xpath://input[@name="web-login-area-code-input"]', timeout=10) # 最多等待10秒

            if country_code_input:
                country_code_input.input('86')
                print("国家/地区已输入86。")
                time.sleep(1) # 短暂等待
            else:
                print("❌ 未找到国家/地区输入框，无法进行下一步。")
                return False

            # 2. 用xpath定位ele('xpath://*[@placeholder="请输入手机号"]')
            # 然后在终端让我输入手机号，并把我输入的手机号填写进去
            print("尝试定位手机号输入框...")
            phone_input = page.ele('xpath://*[@placeholder="请输入手机号"]')
            
            if not phone_input:
                print("⚠️ 手机号输入框未立即找到，尝试等待...")
                phone_input = page.wait.ele_appear('xpath://*[@placeholder="请输入手机号"]', timeout=10) # 最多等待10秒

            if phone_input:
                phone_number = input("请在控制台输入您的手机号并按回车: ")
                phone_input.input(phone_number)
                print("手机号已输入。")
                time.sleep(1) # 短暂等待
            else:
                print("❌ 未找到手机号输入框，无法进行下一步。")
                return False

            # 3. 输入后 定位.ele('xpath://span[text()="获取验证码"]') 按下按钮后 终端等待我输入验证码
            print("尝试定位发送验证码按钮...")
            send_code_button = page.ele('xpath://span[text()="获取验证码"]')
            
            if not send_code_button:
                print("⚠️ 获取验证码按钮未立即找到，尝试等待...")
                send_code_button = page.wait.ele_appear('xpath://span[text()="获取验证码"]', timeout=10) # 最多等待10秒

            if send_code_button:
                send_code_button.click()
                print("已点击获取验证码。")
                time.sleep(3) # 给页面短暂的反应时间，等待验证码发送
            else:
                print("❌ 未找到获取验证码按钮，无法进行下一步。")
                return False

            # 4. 定位ele('xpath://*[@placeholder="请输入验证码"]')  把我的验证码输入进去
            print("尝试定位验证码输入框 (使用 placeholder)...")
            code_input = page.ele('xpath://*[@placeholder="请输入验证码"]')
            
            if not code_input:
                print("⚠️ 验证码输入框未立即找到，尝试等待...")
                code_input = page.wait.ele_appear('xpath://*[@placeholder="请输入验证码"]', timeout=10) # 最多等待10秒

            if code_input:
                print("验证码输入框已定位到！")
                verification_code = input("请在控制台输入您收到的验证码并按回车: ")
                code_input.input(verification_code)
                print("验证码已输入。")
                time.sleep(1) # 短暂等待
            else:
                print("❌ 验证码输入框仍然无法被DrissionPage定位到，无法进行下一步。")
                return False

            # 5. 最后定位ele('xpath://div[text()="登录/注册"]') 并点击
            print("尝试定位登录/注册按钮...")
            login_register_button = page.ele('xpath://div[text()="登录/注册"]')
            
            if not login_register_button:
                print("⚠️ 登录/注册按钮未立即找到，尝试等待...")
                login_register_button = page.wait.ele_appear('xpath://div[text()="登录/注册"]', timeout=10) # 最多等待10秒

            if login_register_button:
                login_register_button.click()
                print("已点击登录/注册。等待页面跳转或登录成功...")
                time.sleep(10) # 增加等待时间，确保登录成功并页面跳转
                print("登录流程可能已完成。请检查浏览器界面是否登录成功。")
            else:
                print("❌ 未找到登录/注册按钮，无法进行下一步。")
                return False
            
            # 登录成功后截图
            login_screenshot_path = './login_screenshot.png'
            print(f"\n📸 正在截图并保存登录状态到: {login_screenshot_path}")
            try:
                page.get_screenshot(path=login_screenshot_path)
                print("✅ 登录状态截图成功！")
                return True
            except Exception as e:
                print(f"❌ 登录状态截图失败: {e}")
                return False

        else:
            print(f"❌ 页面标题或URL异常，可能未成功加载抖音内容。")
            return False

    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        if browser:
            try:
                browser.quit()
                print("✅ 浏览器已关闭")
            except:
                pass

        if xvfb:
            xvfb.stop()
            print("✅ Xvfb已停止")

        print("测试完成!")

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")

    # 检查Python版本
    python_version = sys.version
    print(f"Python版本: {python_version}")

    # 检查必要的命令
    commands = ['google-chrome', 'Xvfb']
    for cmd in commands:
        try:
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {cmd}: {result.stdout.strip()}")
            else:
                print(f"❌ {cmd}: 未找到")
        except:
            print(f"❌ {cmd}: 检查失败")

    # 检查Chrome版本
    try:
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Chrome版本: {result.stdout.strip()}")
        else:
            print(f"❌ Chrome版本检查失败")
    except:
        print(f"❌ Chrome版本检查异常")

    # 检查DrissionPage
    try:
        from DrissionPage import Chromium, ChromiumOptions
        import DrissionPage
        print(f"✅ DrissionPage版本: {DrissionPage.__version__}")
    except ImportError:
        print("❌ DrissionPage未安装")
    except:
        print("✅ DrissionPage已安装")

    print("-" * 50)

if __name__ == "__main__":
    # 设置信号处理，确保能够正常退出
    def signal_handler(signum, frame):
        print("\n收到退出信号，正在清理...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 检查环境
    check_environment()

    # 运行主测试
    print("\n" + "="*50)
    print("运行抖音页面测试")
    success = test_douyin_page()

    if success:
        print("\n🎉 抖音页面测试成功！截图已保存到 login_screenshot.png。")
        sys.exit(0)
    else:
        print("\n❌ 抖音页面测试失败，请检查错误信息。")
        sys.exit(1)
