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
    """测试访问抖音页面并截图"""
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
        
        # --- 新增步骤：检查 Accept-Language 头是否正确发送 ---
        print("\n🔍 正在检查 Accept-Language 头是否发送正确...")
        page.get('https://httpbin.org/headers')
        time.sleep(3) # 等待页面加载，确保所有头信息都已显示
        
        headers_content = page.ele('tag:body').text
        print("--- 浏览器发送的 HTTP 请求头 (来自 httpbin.org) ---")
        print(headers_content)
        print("-------------------------------------------------")

        # 3. 访问抖音页面
        douyin_url = 'https://v.douyin.com/IAqLrgefUPA/'
        print(f"\n🌐 访问抖音页面: {douyin_url} ...")
        page.get(douyin_url)

        # 等待页面加载，抖音页面内容动态较多，需要较长等待
        print("⏳ 等待页面内容加载... (建议等待10-15秒或更长)")
        time.sleep(15) # 增加等待时间，确保动态内容加载完成

        # 4. 检查页面是否成功加载抖音内容
        title = page.title
        current_url = page.url
        print(f"📄 页面标题: {title}")
        print(f"🔗 当前URL: {current_url}")

        # 检查是否成功加载，抖音页面标题通常包含“抖音”或重定向后的信息
        if '抖音' in title or 'douyin' in title.lower() or 'aweme' in current_url.lower():
            print("✅ 成功访问抖音页面！")

            # 5. 截图并保存
            screenshot_path = './douyin_screenshot.png'
            print(f"\n📸 正在截图并保存到: {screenshot_path}")
            try:
                page.get_screenshot(path=screenshot_path)
                print("✅ 截图成功！")
            except Exception as e:
                print(f"❌ 截图失败: {e}")
                return False
                
            # 6. 开始登录流程
            print("\n🔐 开始登录流程...")
            
            # 先等待一下，确保登录框完全加载
            print("⏳ 等待登录框加载...")
            time.sleep(5)
            
            # 打印当前页面标题和URL，确认我们在正确的页面
            print(f"当前页面标题: {page.title}")
            print(f"当前页面URL: {page.url}")
            
            # 尝试查找登录框元素
            print("🔍 尝试查找登录框元素...")
            
            # 定位并设置国家代码
            try:
                country_code_input = page.ele('css:.B7N1ZHMr')
                print(f"国家代码输入框查找结果: {'找到' if country_code_input else '未找到'}")
                if country_code_input:
                    country_code_input.input('86')
                    print("✅ 已设置国家代码为+86")
                else:
                    print("❌ 未找到国家代码输入框")
                    # 尝试截图记录当前页面状态
                    debug_screenshot_path = './debug_screenshot.png'
                    page.get_screenshot(path=debug_screenshot_path)
                    print(f"已保存调试截图到 {debug_screenshot_path}")
                    return False
            except Exception as e:
                print(f"❌ 设置国家代码时出错: {e}")
                # 尝试截图记录当前页面状态
                debug_screenshot_path = './debug_screenshot.png'
                page.get_screenshot(path=debug_screenshot_path)
                print(f"已保存调试截图到 {debug_screenshot_path}")
                return False

            # 获取用户手机号
            try:
                print("🔍 尝试查找手机号输入框...")
                phone_input = page.ele('xpath://*[@placeholder="请输入手机号"]')
                print(f"手机号输入框查找结果: {'找到' if phone_input else '未找到'}")
                
                if phone_input:
                    # 尝试其他定位方式，以防万一
                    print("尝试其他定位方式查找手机号输入框...")
                    try:
                        # 尝试通过CSS选择器定位
                        alt_phone_input = page.ele('css:input[placeholder="请输入手机号"]')
                        print(f"通过CSS选择器查找手机号输入框: {'找到' if alt_phone_input else '未找到'}")
                    except:
                        pass
                    
                    phone_number = input("请输入手机号: ")
                    phone_input.input(phone_number)
                    print("✅ 已输入手机号")
                    
                    # 输入手机号后截图
                    phone_screenshot_path = './phone_screenshot.png'
                    print(f"\n📸 正在保存手机号输入后的截图到: {phone_screenshot_path}")
                    try:
                        page.get_screenshot(path=phone_screenshot_path)
                        print(f"✅ 手机号输入后截图成功！已保存到 {phone_screenshot_path}")
                    except Exception as e:
                        print(f"❌ 手机号输入后截图失败: {e}")
                else:
                    print("❌ 未找到手机号输入框")
                    # 尝试截图记录当前页面状态
                    debug_screenshot_path = './debug_phone_input.png'
                    page.get_screenshot(path=debug_screenshot_path)
                    print(f"已保存调试截图到 {debug_screenshot_path}")
                    
                    # 尝试获取页面源码，看看有什么元素
                    print("尝试分析页面元素...")
                    try:
                        # 查找所有输入框
                        inputs = page.eles('tag:input')
                        print(f"页面上找到 {len(inputs)} 个输入框元素")
                        for i, inp in enumerate(inputs[:5]):  # 只显示前5个
                            try:
                                placeholder = inp.attr('placeholder')
                                print(f"输入框 {i+1}: placeholder='{placeholder}'")
                            except:
                                print(f"输入框 {i+1}: 无法获取placeholder")
                    except Exception as e:
                        print(f"分析页面元素时出错: {e}")
                    
                    return False
            except Exception as e:
                print(f"❌ 查找手机号输入框时出错: {e}")
                debug_screenshot_path = './debug_phone_error.png'
                page.get_screenshot(path=debug_screenshot_path)
                print(f"已保存调试截图到 {debug_screenshot_path}")
                return False

            # 等待一下，确保手机号输入完成后页面有响应
        print("⏳ 等待页面响应...")
        time.sleep(3)
        
        # 点击获取验证码
        verify_button = page.ele('xpath://span[text()="获取验证码"]')
        if verify_button:
            # 截图记录点击验证码按钮前的状态
            verify_before_screenshot_path = './verify_before_screenshot.png'
            print(f"\n📸 正在保存点击验证码按钮前的截图到: {verify_before_screenshot_path}")
            try:
                page.get_screenshot(path=verify_before_screenshot_path)
                print(f"✅ 验证码按钮点击前截图成功！已保存到 {verify_before_screenshot_path}")
            except Exception as e:
                print(f"❌ 验证码按钮点击前截图失败: {e}")
                
            # 点击验证码按钮
            verify_button.click()
            print("✅ 已点击获取验证码按钮")
            
            # 等待一下，确保验证码发送请求已经触发
            print("⏳ 等待验证码发送...")
            time.sleep(3)
            
            # 截图记录点击验证码按钮后的状态
            verify_after_screenshot_path = './verify_after_screenshot.png'
            print(f"\n📸 正在保存点击验证码按钮后的截图到: {verify_after_screenshot_path}")
            try:
                page.get_screenshot(path=verify_after_screenshot_path)
                print(f"✅ 验证码按钮点击后截图成功！已保存到 {verify_after_screenshot_path}")
            except Exception as e:
                print(f"❌ 验证码按钮点击后截图失败: {e}")
            else:
                print("❌ 未找到验证码按钮")
                return False

            # 获取用户输入的验证码
            verify_code = input("请输入收到的验证码: ")
            verify_input = page.ele('xpath://*[@placeholder="请输入验证码"]')
            if verify_input:
                verify_input.input(verify_code)
                print("✅ 已输入验证码")
            else:
                print("❌ 未找到验证码输入框")
                return False

            # 点击登录按钮
            login_button = page.ele('xpath://div[text()="登录/注册"]')
            if login_button:
                login_button.click()
                print("✅ 已点击登录按钮")
                # 等待登录完成
                time.sleep(5)
            else:
                print("❌ 未找到登录按钮")
                return False

            # 登录后截图
            login_screenshot_path = './login_screenshot.png'
            print(f"\n📸 正在保存登录后截图到: {login_screenshot_path}")
            try:
                page.get_screenshot(path=login_screenshot_path)
                print("✅ 登录后截图成功！")
                return True
            except Exception as e:
                print(f"❌ 登录后截图失败: {e}")
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
        print("\n🎉 抖音页面测试成功！登录截图已保存到 login_screenshot.png。")
        sys.exit(0)
    else:
        print("\n❌ 抖音页面测试失败，请检查错误信息。")
        sys.exit(1)
