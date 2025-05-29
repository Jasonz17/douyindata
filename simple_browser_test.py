import os
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys
# 导入 PageDisconnectedError 和 BrowserConnectError 用于更精确的捕获
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
    co.set_argument('--v=1') # 增加详细级别

    # ****** 关键：这里不再包含 --headless=new ******
    # co.set_argument('--headless=new') # 移除此行！

    # 额外参数，尝试解决兼容性问题
    co.set_argument('--disable-accelerated-2d-canvas') # 禁用 2D Canvas 加速
    co.set_argument('--disable-webgl') # 禁用 WebGL
    co.set_argument('--disable-features=NetworkService') # 禁用网络服务（激进，如果好了再考虑）
    co.set_argument('--disable-features=VizDisplayCompositor') # 禁用 Viz 显示合成器


    print("DEBUG: 尝试创建浏览器实例 (真·有头模式，依赖 Xvfb 完整功能)...", file=sys.stderr)
    # 增加启动超时时间
    browser = ChromiumPage(co, timeout=30) # 默认10秒，这里增加到30秒
    print("DEBUG: 浏览器实例创建成功！", file=sys.stderr)

    print("DEBUG: 尝试访问百度...", file=sys.stderr)
    browser.get('https://www.baidu.com')
    print("DEBUG: 成功访问百度！页面标题:", browser.title, file=sys.stderr)

    # 等待一小段时间，以便截图或观察
    time.sleep(5)

    # 尝试截图保存
    screenshot_path = os.path.join(current_script_dir, 'baidu_screenshot.png')
    browser.get_screenshot(path=screenshot_path)
    print(f"DEBUG: 截图已保存到: {screenshot_path}", file=sys.stderr)

except PageDisconnectedError as e: # 精确捕获 PageDisconnectedError
    print(f"ERROR: PageDisconnectedError - 页面连接已断开: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
except BrowserConnectError as e: # 精确捕获 BrowserConnectError
    print(f"ERROR: BrowserConnectError - 浏览器连接失败或无法启动: {e}", file=sys.stderr)
    print("ERROR: 这通常意味着 Chromium 在 Xvfb 环境中无法正常启动其图形界面。", file=sys.stderr)
    print("ERROR: 请检查是否缺少必要的 X11 运行时库，或尝试不同的 Chromium 版本。", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
except Exception as e: # 捕获其他所有错误
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
