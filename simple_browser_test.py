import os
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys
# 导入 DrissionPage 中可能抛出的错误类
from DrissionPage.errors import PageDisconnectedError, BrowserConnectError, ElementNotFoundError


# 获取当前脚本文件所在的目录
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# 定义一个用于保存浏览器用户资料的目录路径
# 它将会在当前脚本文件的目录下创建一个 'drissionpage_test_data' 文件夹
user_data_dir = os.path.join(current_script_dir, 'drissionpage_test_data')
# 确保用户数据目录存在，如果不存在则创建
os.makedirs(user_data_dir, exist_ok=True)

# 打印调试信息到标准错误流，方便 nohup 重定向到日志文件
print(f"DEBUG: 用户数据目录设置为: {user_data_dir}", file=sys.stderr)

browser = None # 初始化浏览器实例为 None

try:
    # 创建 ChromiumOptions 实例，用于配置浏览器启动参数
    co = ChromiumOptions()
    co.set_user_data_path(user_data_dir) # 设置用户数据路径

    # 核心参数：禁用沙盒和 /dev/shm 共享内存，这在 Docker 或服务器环境中非常重要
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')

    # 强制禁用所有 GPU 相关的参数，以避免在无 GPU 环境中启动失败
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-setuid-sandbox')
    co.set_argument('--disable-seccomp-filter-sandbox')
    co.set_argument('--no-zygote') # 在某些系统上启动时可能需要
    co.set_argument('--single-process') # 强制单进程模式，有时可以避免某些资源问题
    co.set_argument('--disable-site-isolation-trials') # 禁用网站隔离试验
    co.set_argument('--disable-speech-api') # 禁用语音 API
    co.set_argument('--disable-blink-features=AutomationControlled') # 隐藏自动化控制标识
    co.set_argument('--disable-features=IsolateOrigins,site-per-process') # 禁用网站隔离
    co.set_argument('--enable-automation') # 启用自动化标识（通常用于测试框架）
    co.set_argument('--disable-features=OnDevicePersonalization') # 禁用设备上的个性化功能
    co.set_argument('--disable-features=WebRtcHideLocalIpsWithMdns') # 禁用 WebRTC 隐藏本地 IP

    # 强制 Chromium 输出更多日志到标准错误流，帮助调试底层问题
    co.set_argument('--enable-logging=stderr')
    co.set_argument('--v=1') # 设置详细级别，1通常足够，可以尝试2或3 if needed

    # 额外参数，尝试解决兼容性问题
    # 尽管是有头模式测试，但明确指定为“新无头”模式有时可以绕过一些旧的 Xvfb/GPU 问题
    co.set_argument('--headless=new')
    co.set_argument('--disable-accelerated-2d-canvas') # 禁用 2D Canvas 加速
    co.set_argument('--disable-webgl') # 禁用 WebGL
    co.set_argument('--disable-features=NetworkService') # 禁用网络服务（激进，如果好了再考虑）
    co.set_argument('--disable-features=VizDisplayCompositor') # 禁用 Viz 显示合成器

    print("DEBUG: 尝试创建浏览器实例...", file=sys.stderr)
    # 创建 ChromiumPage 实例，并增加启动超时时间，给 Chromium 更多时间启动
    browser = ChromiumPage(co, timeout=30) # 默认10秒，这里增加到30秒
    print("DEBUG: 浏览器实例创建成功！", file=sys.stderr)

    print("DEBUG: 尝试访问抖音...", file=sys.stderr)
    browser.get('https://v.douyin.com/IAqLrgefUPA/') # 访问百度页面
    print("DEBUG: 成功访问抖音！页面标题:", browser.title, file=sys.stderr)

    # 等待一小段时间，以便截图或观察页面状态
    time.sleep(5)

    # 尝试截图保存到项目目录下
    screenshot_path = os.path.join(current_script_dir, 'douyin_screenshot.png')
    browser.get_screenshot(path=screenshot_path)
    print(f"DEBUG: 截图已保存到: {screenshot_path}", file=sys.stderr)

# 捕获 DrissionPage 特定的 PageDisconnectedError
except PageDisconnectedError as e:
    print(f"ERROR: PageDisconnectedError - 页面连接已断开: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
# 捕获 DrissionPage 特定的 BrowserConnectError
except BrowserConnectError as e:
    print(f"ERROR: BrowserConnectError - 浏览器连接失败或无法启动: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
# 捕获其他所有未预料的错误
except Exception as e:
    print(f"ERROR: 发生其他错误: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
finally:
    # 确保在任何情况下都尝试关闭浏览器实例，避免资源泄露
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

print("DEBUG: 脚本执行结束。", file=sys.stderr) # 这行代码与 try/except/finally 块在同一缩进级别
