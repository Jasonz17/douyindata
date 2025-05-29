import os
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys

# 获取当前脚本的目录
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# 定义一个用于保存浏览器用户资料的目录路径
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

    print("DEBUG: 尝试创建浏览器实例...", file=sys.stderr)
    browser = ChromiumPage(co)
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

except Exception as e:
    print(f"ERROR: 发生错误: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
finally:
    if browser:
        print("DEBUG: 正在关闭浏览器...", file=sys.stderr)
        browser.quit()
        print("DEBUG: 浏览器已关闭。", file=sys.stderr)
    else:
        print("DEBUG: 浏览器未成功启动，无需关闭。", file=sys.stderr)

print("DEBUG: 脚本执行结束。", file=sys.stderr)
