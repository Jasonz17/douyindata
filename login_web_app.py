import os
import time
import base64
import threading
import queue
from flask import Flask, render_template, jsonify, request, url_for
from DrissionPage import ChromiumPage, ChromiumOptions
# 导入 DrissionPage 中可能抛出的错误类，现在我们知道它们是存在的
from DrissionPage.errors import PageDisconnectedError, BrowserConnectError, ElementNotFoundError

app = Flask(__name__)

# --- 配置 DrissionPage 用户数据路径 ---
# 获取当前脚本文件所在的目录
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# 定义一个用于保存浏览器用户资料的目录路径
# 它将会在当前脚本文件的目录下创建一个 'drissionpage' 文件夹
user_data_dir = os.path.join(current_script_dir, 'drissionpage') # 调整为 'drissionpage'
# 确保目录存在，如果不存在则创建
os.makedirs(user_data_dir, exist_ok=True)


# 全局变量，用于控制登录流程和存储状态
login_process_queue = queue.Queue()
browser_instance = None
current_login_status = "idle"  # "idle", "processing", "success", "failed"
current_screenshot_base64 = ""
current_log_messages = []
current_qr_code_image = None # 用于存储二维码图片数据

# --- 辅助函数：更新状态和日志 ---
def update_status_and_log(status, message):
    """更新全局状态和日志消息。"""
    global current_login_status
    global current_log_messages

    if status:
        current_login_status = status
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    log_message = f"[{timestamp}] [{status.upper() if status else 'INFO'}]: {message}"
    current_log_messages.append(log_message)
    print(log_message) # 也打印到控制台，方便 nohup 重定向到日志文件查看

# --- DrissionPage 登录逻辑 ---
def run_drissionpage_login_no_socketio():
    """
    在单独线程中运行 DrissionPage 登录逻辑。
    通过全局变量更新状态和截图。
    """
    global browser_instance
    global current_screenshot_base64
    global current_qr_code_image

    update_status_and_log("processing", "【DrissionPage】: 正在启动登录流程线程...")
    browser_instance = None # 确保每次启动前都重置
    current_qr_code_image = None # 每次启动清空二维码数据

    try:
        co = ChromiumOptions()
        co.set_user_data_path(user_data_dir)

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
        co.set_argument('--v=1') # 设置详细级别

        # 额外参数，尝试解决兼容性问题
        co.set_argument('--headless=new') # 明确指定为“新无头”模式
        co.set_argument('--disable-accelerated-2d-canvas') # 禁用 2D Canvas 加速
        co.set_argument('--disable-webgl') # 禁用 WebGL
        co.set_argument('--disable-features=NetworkService') # 禁用网络服务（激进，如果好了再考虑）
        co.set_argument('--disable-features=VizDisplayCompositor') # 禁用 Viz 显示合成器


        update_status_and_log("processing", "【DrissionPage】: 正在创建浏览器实例 (有头模式，依赖 Xvfb)...")
        
        # 增加启动超时时间，给 Chromium 更多时间启动
        browser = ChromiumPage(co, timeout=30) # 默认10秒，这里增加到30秒
        update_status_and_log("processing", "【DrissionPage】: 浏览器实例创建成功。")

        update_status_and_log("processing", "【DrissionPage】: 导航到抖音登录页...")
        browser.get('https://www.douyin.com/')
        # 等待页面加载，或者找到登录按钮
        browser.wait.ele_loaded('xpath=//a[text()="登录"]', timeout=10)
        browser.ele('xpath=//a[text()="登录"]').click()
        update_status_and_log("processing", "【DrissionPage】: 点击登录按钮，等待登录框出现...")

        # 等待二维码出现
        try:
            browser.wait.ele_loaded('xpath=//img[@alt="扫码登录"]', timeout=15)
            qr_code_ele = browser.ele('xpath=//img[@alt="扫码登录"]')
            update_status_and_log("processing", "【DrissionPage】: 找到二维码元素，尝试获取截图...")
            
            # 直接获取二维码图片数据
            qr_code_data = qr_code_ele.ele_attr('src')
            if qr_code_data.startswith('data:image/png;base64,'):
                qr_code_data = qr_code_data.replace('data:image/png;base64,', '')
            
            current_qr_code_image = qr_code_data
            update_status_and_log("processing", "【DrissionPage】: 二维码数据已获取，等待扫码...")

        except ElementNotFoundError:
            update_status_and_log("error", "【DrissionPage】: 登录二维码未在指定时间内找到。")
            current_login_status = "failed"
            return
        except Exception as e:
            update_status_and_log("error", f"【DrissionPage】: 获取二维码时发生错误: {e}")
            current_login_status = "failed"
            return


        # 检查登录状态的循环，例如通过判断特定元素的存在
        max_attempts = 60 # 尝试检查60次，每次1秒，总共等待1分钟
        for i in range(max_attempts):
            time.sleep(1)
            # 假设登录成功后页面会重定向，并且某个元素会消失或出现
            # 这里简单判断URL是否不再是登录页面
            if "login" not in browser.url and "passport" not in browser.url:
                update_status_and_log("success", "【DrissionPage】: 检测到页面跳转，可能已登录成功！")
                break
            
            update_status_and_log("processing", f"【DrissionPage】: 等待扫码... ({i+1}/{max_attempts}秒)")
            
        else:
            update_status_and_log("failed", "【DrissionPage】: 扫码超时，未检测到登录成功。")
            current_login_status = "failed"
            return
        
        # 登录成功后的截图
        update_status_and_log("processing", "【DrissionPage】: 登录成功，正在截取最终页面截图...")
        try:
            screenshot_bytes = browser.get_screenshot()
            current_screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            update_status_and_log("success", "【DrissionPage】: 登录成功，截图已获取。")
            current_login_status = "success"
        except PageDisconnectedError:
            update_status_and_log("error", "【DrissionPage】: 获取截图时页面已断开连接。")
            current_login_status = "failed"
        except Exception as e:
            update_status_and_log("error", f"【DrissionPage】: 获取截图时发生未知错误: {e}")
            current_login_status = "failed"

    except PageDisconnectedError as e: # 精确捕获 PageDisconnectedError
        update_status_and_log("error", f"【DrissionPage】: PageDisconnectedError - 页面连接已断开: {e}")
        import traceback
        update_status_and_log("error", traceback.format_exc())
        current_login_status = "failed"
    except BrowserConnectError as e: # 精确捕获 BrowserConnectError
        update_status_and_log("error", f"【DrissionPage】: BrowserConnectError - 浏览器连接失败或无法启动: {e}")
        update_status_and_log("error", "【DrissionPage】: 请检查 Chromium 是否正确安装，Xvfb 是否正常工作，以及服务器依赖是否正确。")
        import traceback
        update_status_and_log("error", traceback.format_exc())
        current_login_status = "failed"
    except Exception as e: # 捕获其他所有未预料的错误
        update_status_and_log("error", f"【DrissionPage】: 浏览器操作过程中发生其他异常: {e}")
        import traceback
        update_status_and_log("error", traceback.format_exc())
        current_login_status = "failed"
    finally:
        if browser:
            update_status_and_log("info", "【DrissionPage】: 正在关闭浏览器...")
            try:
                browser.quit()
                update_status_and_log("info", "【DrissionPage】: 浏览器已关闭。")
            except Exception as e:
                update_status_and_log("error", f"【DrissionPage】: 关闭浏览器时发生错误: {e}")
                import traceback
                update_status_and_log("error", traceback.format_exc())


# --- Flask 路由 ---
@app.route('/')
def index():
    return render_template('login_index.html') # 确保你有这个 HTML 模板文件

@app.route('/start_login', methods=['POST'])
def start_login():
    """触发 DrissionPage 登录流程。"""
    global current_login_status
    if current_login_status != "processing":
        update_status_and_log("idle", "用户请求启动登录流程...")
        # 清空之前的状态和截图
        global current_screenshot_base64, current_log_messages, current_qr_code_image
        current_screenshot_base64 = ""
        current_log_messages = []
        current_qr_code_image = None

        # 在新线程中运行 DrissionPage 登录逻辑，避免阻塞 Flask 主线程
        threading.Thread(target=run_drissionpage_login_no_socketio).start()
        return jsonify({"message": "登录流程已启动，请等待...", "status": "processing"})
    else:
        return jsonify({"message": "登录流程正在进行中，请勿重复操作。", "status": "processing"}), 409

@app.route('/login_status', methods=['GET'])
def get_login_status():
    """获取当前登录状态、日志和截图。"""
    return jsonify({
        "status": current_login_status,
        "screenshot": current_screenshot_base64,
        "logs": current_log_messages,
        "qr_code_image": current_qr_code_image # 返回二维码图片数据
    })

# --- Flask 应用启动 ---
if __name__ == '__main__':
    print("------------------------------------------")
    print(f"Flask Web 服务将在 http://0.0.0.0:3030 启动")
    print(f"浏览器用户资料路径: {user_data_dir}")
    print("------------------------------------------")
    app.run(host='0.0.0.0', port=3030, debug=True, threaded=True) # 确保绑定到 0.0.0.0 和 3030 端口
