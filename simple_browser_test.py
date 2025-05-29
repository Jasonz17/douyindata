import os
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys
from DrissionPage.errors import PageDisconnectedError, BrowserConnectError, ElementNotFoundError


current_script_dir = os.path.dirname(os.path.abspath(__file__))
user_data_dir = os.path.join(current_script_dir, 'drissionpage_test_data')
os.makedirs(user_data_dir, exist_ok=True)

print(f"DEBUG: 用户数据目录设置为: {user_data_dir}", file=sys.stderr)

browser = None
try:
    co = ChromiumOptions()
    co.set_user_data_path(user_data_dir)

    # 核心参数，禁用沙盒和 /dev/shm
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')

    # 强制禁用所有 GPU 相关的参数
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-setuid-sandbox')
    co.set_argument('--disable-seccomp-filter-sandbox')
    co.set_argument('--no-zygote')
    co.set_argument('--single-process')
    co.set_argument('--disable-site-isolation-trials')
    co.set_argument('--disable-speech-api')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--disable-features=IsolateOrigins,site-per-process')
    co.set_argument('--enable-automation')
    co.set_argument('--disable-features=OnDevicePersonalization')
    co.set_argument('--disable-features=WebRtcHideLocalIpsWithMdns')

    # 强制 Chromium 输出更多日志到 stderr
    co.set_argument('--enable-logging=stderr')
    co.set_argument('--v=2') # 增加详细级别到 2，希望能捕获更多崩溃前的信息

    # 确保没有 --headless=new，我们就是要真·有头
    # co.set_argument('--headless=new') # 确保此行被注释掉或删除！

    # 额外参数，尝试解决兼容性问题
    co.set_argument('--disable-accelerated-2d-canvas') # 禁用 2D Canvas 加速
    co.set_argument('--disable-webgl') # 禁用 WebGL
    co.set_argument('--disable-features=NetworkService') # 禁用网络服务（激进，如果好了再考虑）
    co.set_argument('--disable-features=VizDisplayCompositor') # 禁用 Viz 显示合成器

    # ****** 新增一些尝试性参数 ******
    co.set_argument('--no-first-run') # 避免首次运行向导
    co.set_argument('--no-default-browser-check') # 避免检查是否为默认浏览器
    co.set_argument('--disable-background-networking') # 禁用背景网络活动
    co.set_argument('--disable-background-timer-throttling') # 禁用背景计时器节流
    co.set_argument('--disable-backgrounding-occluded-windows') # 禁用后台遮挡窗口
    co.set_argument('--disable-breakpad') # 禁用崩溃报告
    co.set_argument('--disable-client-side-phishing-detection') # 禁用客户端钓鱼检测
    co.set_argument('--disable-sync') # 禁用同步
    co.set_argument('--disable-extensions') # 禁用扩展
    co.set_argument('--disable-component-update') # 禁用组件更新
    co.set_argument('--disable-infobars') # 禁用信息条
    co.set_argument('--disable-translate') # 禁用翻译
    co.set_argument('--disable-setuid-sandbox') # 再次确认禁用
    co.set_argument('--disable-web-security') # 禁用web安全策略（谨慎使用，但测试时可能有用）
    # ********************************

    print("DEBUG: 尝试创建浏览器实例 (真·有头模式，依赖 Xvfb 完整功能，并安装更多依赖)...", file=sys.stderr)
    # 增加启动超时时间
    browser = ChromiumPage(co, timeout=30)
    print("DEBUG: 浏览器实例创建成功！", file=sys.stderr)

    print("DEBUG: 尝试访问百度...", file=sys.stderr)
    browser.get('https://www.baidu.com')
    print("DEBUG: 成功访问百度！页面标题:", browser.title, file=sys.stderr)

    time.sleep(5)

    screenshot_path = os.path.join(current_script_dir, 'baidu_screenshot.png')
    browser.get_screenshot(path=screenshot_path)
    print(f"DEBUG: 截图已保存到: {screenshot_path}", file=sys.stderr)

except PageDisconnectedError as e:
    print(f"ERROR: PageDisconnectedError - 页面连接已断开: {e}", file=sys.stderr)
    print("ERROR: 这通常意味着 Chromium 在 Xvfb 环境中无法正常启动其图形界面，即使所有 ldd 依赖都已满足。", file=sys.stderr)
    print("ERROR: 可能是 Xvfb 提供的功能不足，或 Chromium 版本与 Xvfb 不兼容。", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
except BrowserConnectError as e:
    print(f"ERROR: BrowserConnectError - 浏览器连接失败或无法启动: {e}", file=sys.stderr)
    print("ERROR: 请检查是否缺少必要的 X11 运行时库，或尝试不同的 Chromium 版本。", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
except Exception as e:
    print(f"ERROR: 发生其他错误: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
finally:
    if browser:
        print("DEBUG: 正在关闭浏览器...", file=sys.stderr)
        try:
            browser.quit()
            print("DEBUG: 浏览器已关闭。", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: 关闭浏览器时发生错误: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
    else:
        print("DEBUG: 浏览器未成功启动，无需关闭。", file=sys.stderr)

print("DEBUG: 脚本执行结束。", file=sys.stderr)
