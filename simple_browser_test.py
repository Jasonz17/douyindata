#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import signal
from DrissionPage import ChromiumPage, ChromiumOptions # 修改：从 ChromiumPage 导入，而不是 Chromium
import DrissionPage # 导入用于获取版本号

# --- 你提供的 XvfbManager 类 ---
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

# --- 你提供的 create_chrome_options 函数，并加入 Accept-Language 设置 ---
def create_chrome_options():
    """创建Chrome选项配置"""
    options = ChromiumOptions()

    # 基础选项（保留有助于稳定性和反检测的）
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-dev-shm-usage') # 避免共享内存问题
    options.set_argument('--disable-gpu') # 因为没有物理GPU
    options.set_argument('--window-size=1920,1080') # 截图所需分辨率
    options.set_argument('--remote-debugging-port=9222') # 用于DrissionPage连接

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
    # 根据你的实际Chrome版本 137.0.0.0 更新 User-Agent
    options.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')

    # 指定Chrome路径（如果需要），确保路径正确
    chrome_path = '/usr/bin/google-chrome'
    if os.path.exists(chrome_path):
        options.set_browser_path(chrome_path)

    # ！！！重要：设置 Accept-Language 偏好！！！
    options.set_a_header('Accept-Language', 'zh-CN,zh;q=0.9,en;q=0.8')

    return options

# --- 你提供的 test_douyin_page 函数，并加入 httpbin.org 验证和截图清除 ---
def test_douyin_page():
    """测试访问抖音页面并截图"""
    xvfb = None # 使用你自己的 XvfbManager 实例
    page = None

    try:
        print("="*50)
        print("开始 DrissionPage + Xvfb 访问抖音页面测试")
        print("="*50)

        # 1. 启动Xvfb
        xvfb = XvfbManager() # 使用你自己的 XvfbManager 类
        if not xvfb.start():
            print("❌ Xvfb启动失败，退出测试")
            return False

        # 2. 创建浏览器实例
        print("\n🚀 创建浏览器实例...")
        options = create_chrome_options()
        # 注意：这里 DrissionPage 的使用方式，以前用 Chromium，现在用 ChromiumPage
        # 如果你希望用 browser.latest_tab，则应该实例化 Chromium
        # 根据你的原始代码片段，你用的是 page = browser.latest_tab，所以这里应该实例化 Chromium
        browser = DrissionPage.Chromium(options)
        page = browser.latest_tab # 获取页面对象

        print("✅ 浏览器创建成功")

        # 定义截图路径
        screenshot_path = './douyin_screenshot.png'

        # --- 新增步骤：检查 Accept-Language 头是否正确发送 ---
        print("\n🔍 正在检查 Accept-Language 头是否发送正确...")
        page.get('https://httpbin.org/headers')
        time.sleep(3) # 等待页面加载，确保所有头信息都已显示
        
        headers_content = page.ele('tag:body').text
        print("--- 浏览器发送的 HTTP 请求头 (来自 httpbin.org) ---")
        print(headers_content)
        print("-------------------------------------------------")
        # 你需要仔细查看上面的输出，确认其中是否包含 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        # --- 结束新增步骤 ---

        # 可选：删除旧的截图文件，如果需要的话
        if os.path.exists(screenshot_path):
            try:
                os.remove(screenshot_path)
                print(f"🗑️ 已清除旧截图: {screenshot_path}")
            except Exception as e:
                print(f"⚠️ 清除旧截图失败: {e}")

        # 3. 访问抖音页面
        # 使用你最近提供的最终URL，因为它在有无代理时都可能出现
        douyin_url = "https://www.douyin.com/?vid=7497916567561309466&recommend=1"
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
            print(f"\n📸 正在截图并保存到: {screenshot_path}")
            try:
                page.get_screenshot(path=screenshot_path)
                print("✅ 截图成功！")
                return True
            except Exception as e:
                print(f"❌ 截图失败: {e}")
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
        if page: # 确保 page 对象存在才执行 quit
            try:
                # DrissionPage 的 Chromium 实例有 quit 方法
                if hasattr(page.browser, 'quit'):
                    page.browser.quit()
                else:
                    page.quit() # 如果 page 是独立的 ChromiumPage 实例
                print("✅ 浏览器已关闭")
            except Exception as e:
                print(f"⚠️ 关闭浏览器时出错: {e}")

        if xvfb:
            xvfb.stop()
            print("✅ Xvfb已停止")

        print("测试完成!")

# --- 你提供的 check_environment 函数 ---
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
        from DrissionPage import Chromium, ChromiumOptions # 导入 Chromium 来检查
        import DrissionPage
        print(f"✅ DrissionPage版本: {DrissionPage.__version__}")
    except ImportError:
        print("❌ DrissionPage未安装")
    except Exception as e: # 捕获其他异常，打印信息
        print(f"✅ DrissionPage已安装 (但检查版本时出错: {e})")

    print("-" * 50)

# --- 主执行块 ---
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
        print("\n🎉 抖音页面测试成功！截图已保存到 douyin_screenshot.png。")
        sys.exit(0)
    else:
        print("\n❌ 抖音页面测试失败，请检查错误信息。")
        sys.exit(1)
