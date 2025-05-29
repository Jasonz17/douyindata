import os
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys
# 导入 PageDisconnectedError 用于更精确的捕获
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

    # ****** 新增额外参数 ******
    co.set_argument('--headless=new') # 虽然我们是有头模式测试，但有时候明确指定为“新无头”模式可以绕过一些旧的Xvfb/GPU问题，即使它会创建虚拟屏幕。
                                     # 这是一个尝试，如果成功，我们再讨论是否保留。
    co.set_argument('--disable-dev-shm-usage') # 确保禁用共享内存
    co.set_argument('--disable-accelerated-2d-canvas') # 禁用 2D Canvas 加速
    co.set_argument('--disable-webgl') # 禁用 WebGL
    co.set_argument('--disable-features=NetworkService') # 禁用网络服务（激进，如果好了再考虑）
    co.set_argument('--disable-features=VizDisplayCompositor') # 禁用 Viz 显示合成器
    # **************************

    print("DEBUG: 尝试创建浏览器实例...", file=sys.stderr)
    # 增加启动超时时间，给Chromium更多时间启动
    browser = ChromiumPage(co, timeout=30) # 默认10秒，这里增加到30秒
    print("DEBUG: 浏览器实例创建成功！", file=sys.stderr)

    # ... (后续代码保持不变) ...

except PageDisconnectedError as e: # 精确捕获 PageDisconnectedError
    print(f"ERROR: PageDisconnectedError - 页面连接已断开: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
except Exception as e: # 捕获其他所有错误
    print(f"ERROR: 发生其他错误: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
finally:
    # ... (关闭浏览器实例的逻辑) ...

print("DEBUG: 脚本执行结束。", file=sys.stderr)
