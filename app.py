from flask import Flask, request, jsonify, render_template
from DrissionPage import ChromiumPage, ChromiumOptions
from urllib.parse import urlparse, parse_qs
import json
import os
import sys
import time
import subprocess
import signal

app = Flask(__name__)

# --- XvfbManager 类定义 (从 login.py 复制) ---
user_data_dir = os.path.join(os.path.expanduser('~'), 'drissionpagedata')
os.makedirs(user_data_dir, exist_ok=True)

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
# --- XvfbManager 类定义结束 ---


# --- Configuration for DrissionPage (from video_data_final.py and adjusted for Xvfb) ---
# 定义一个用于保存浏览器用户资料的目录路径
user_data_dir = os.path.join(os.path.expanduser('~'), 'drissionpagedata')
os.makedirs(user_data_dir, exist_ok=True)

# 创建 ChromiumOptions 实例
co = ChromiumOptions()
# 设置浏览器用户资料的保存路径
co.set_user_data_path(user_data_dir)
co.set_argument('--no-sandbox')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--disable-gpu')
co.set_argument('--window-size=1920,1080') # Consistent with login.py's resolution
co.set_argument('--remote-debugging-port=9222')
co.set_argument('--accept-lang','zh-CN')
co.set_argument('--no-first-run')
co.set_argument('--no-default-browser-check')
co.set_argument('--disable-default-apps')
co.set_argument('--disable-popup-blocking')
co.set_argument('--disable-translate')
co.set_argument('--disable-background-timer-throttling')
co.set_argument('--disable-renderer-backgrounding')
co.set_argument('--disable-backgrounding-occluded-windows')
co.set_argument('--disable-extensions')
co.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
chrome_path = '/usr/bin/google-chrome'
if os.path.exists(chrome_path):
    co.set_browser_path(chrome_path)
# ！！！重要：不设置headless()，让Xvfb处理显示！！！
# co.headless()
# --- End DrissionPage Configuration ---


# --- Xvfb Manager Initialization and Lifecycle Functions ---
xvfb_manager = None

def start_xvfb_for_app():
    """Starts Xvfb when the application initializes."""
    global xvfb_manager
    print("Initializing Xvfb for app...")
    xvfb_manager = XvfbManager()
    if not xvfb_manager.start():
        print("❌ Xvfb failed to start. Exiting application.")
        sys.exit(1)
    print("✅ Xvfb started successfully for app.")

def stop_xvfb_for_app(signum=None, frame=None):
    """Stops Xvfb gracefully."""
    global xvfb_manager
    if xvfb_manager:
        print("Stopping Xvfb for app...")
        xvfb_manager.stop()
        print("✅ Xvfb stopped for app.")
    sys.exit(0) # Exit the application after stopping Xvfb


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, stop_xvfb_for_app)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, stop_xvfb_for_app) # Handle termination signals
# --- End Xvfb Manager Initialization and Lifecycle Functions ---


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_video_url', methods=['GET'])
def get_single_video_url():
    """
    处理获取单个抖音视频下载链接的请求。
    此函数直接来自原始的 app.py。
    参数：url (单个视频链接)
    """
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    url = url.strip()

    browser = None
    try:
       
        print("已配置浏览器参数：--no-sandbox, --disable-dev-shm-usage, --disable-gpu")

        print("正在创建浏览器实例...")
        # Now ChromiumPage will use the options configured with Xvfb
        browser = ChromiumPage(co)
        print("浏览器实例创建成功")

        print(f"原始输入URL (处理后): {url}")
        browser.get(url)

        current_url = browser.url
        print(f"重定向后的URL: {current_url}")

        video_id = None
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)

        if 'vid' in query_params and query_params['vid']:
            video_id = query_params['vid'][0]
            print(f"提取到视频ID: {video_id}")
        elif 'video' in parsed_url.path:
            path_parts = parsed_url.path.split('/')
            if len(path_parts) > 2 and path_parts[-2] == 'video':
                video_id = path_parts[-1]
                print(f"从路径中提取到视频ID: {video_id}")

        if not video_id:
            raise Exception(f"无法从抖音链接中提取到视频ID。当前URL: {current_url}")

        detail_url = f"https://www.douyin.com/video/{video_id}"
        print(f"构造详情页URL: {detail_url}")

        print("开始监听网络请求...")
        browser.listen.start(r'/aweme/v1/web/aweme/detail/')
        print("网络监听已启动")

        print(f"正在访问详情页: {detail_url}")
        browser.get(detail_url)
        print("详情页访问完成，等待API响应...")

        resp = browser.listen.wait()

        json_data = resp.response.body

        aweme_detail = json_data.get('aweme_detail')
        video_info = aweme_detail.get('video', {})
        play_addr = video_info.get('play_addr', {})
        url_list = play_addr.get('url_list', [])

        if not url_list:
            raise Exception("未找到视频播放地址 (url_list)。")

        video_url = ''
        if len(url_list) > 2:
            video_url = url_list[2].replace('playwm', 'play')
        elif len(url_list) > 0:
            video_url = url_list[0].replace('playwm', 'play')

        if not video_url:
            raise Exception("无法获取有效的视频播放地址。")

        print(f"成功获取视频URL: {video_url}")
        return jsonify({'video_url': video_url})

    except Exception as e:
        error_msg = str(e)
        print(f"解析过程中出错: {error_msg}")
        return jsonify({'error': f'解析失败: {error_msg}'}), 500

    finally:
        if browser:
            try:
                print("正在关闭浏览器...")
                browser.quit()
                print("浏览器已关闭")
            except Exception as close_error:
                print(f"关闭浏览器时出错: {close_error}")
                pass

@app.route('/get_user_videos', methods=['GET'])
def get_user_videos():
    """
    处理获取抖音用户主页所有视频数据的请求。
    此函数直接来自你提供的 video_data_final.py 的最新版本。
    参数：pageurl (主页链接)
    """
    page_url = request.args.get('pageurl')
    if not page_url:
        return jsonify({'error': 'Missing pageurl parameter'}), 400

    browser = None
    all_extracted_videos = []

    try:
        browser = ChromiumPage(co)
        browser.listen.start('aweme/v1/web/aweme/post/')

        target_profile_url = page_url
        browser.get(target_profile_url)
        print(f"正在访问抖音主页: {browser.url}")

        page_counter = 0
        should_stop_scrolling = False

        while True:
            page_counter += 1
            print(f'\n正在采集第{page_counter}页的数据')

            no_more_element = browser.ele('xpath://*[text()="暂时没有更多了"]', timeout=1)
            if no_more_element:
                print("检测到 '暂时没有更多了' 文本。将处理完当前数据后停止滚动。")
                should_stop_scrolling = True

            try:
                all_captured_responses = browser.listen.wait(count=9999, timeout=10, fit_count=False)

                if not all_captured_responses:
                    print("本轮滚动未捕捉到任何新的API响应，可能已到底部或加载失败。")
                    if should_stop_scrolling:
                        break
                    print("未检测到结束文本，但本轮未捕捉到任何新数据包，也未提取到视频，停止采集。")
                    break

                processed_packets_count = 0
                total_videos_this_round = 0

                for resp_item in all_captured_responses:
                    try:
                        if 'aweme/v1/web/aweme/post/' in resp_item.url:
                            json_data = resp_item.response.body
                            processed_packets_count += 1

                            video_data = json_data['aweme_list']
                            if not video_data:
                                print(f"数据包 {processed_packets_count} (URL: {resp_item.url}) 中没有 aweme_list 数据。")
                                continue

                            for index in video_data:
                                extracted_video = {
                                    "video_id": index["aweme_id"],
                                    "video_url": f'https://www.douyin.com/video/{index["aweme_id"]}',
                                    "video_title": index['desc'],
                                    "create_time": index['create_time'],
                                    "video_duration": index['duration'],
                                    "video_like": index['statistics']['digg_count'],
                                    "video_comment": index['statistics']['comment_count'],
                                    "video_collect": index['statistics']['collect_count'],
                                    "video_share": index['statistics']['share_count'],
                                    "video_download_url": index['video']['play_addr']['url_list'][2]
                                }
                                all_extracted_videos.append(extracted_video)
                                total_videos_this_round += 1
                                print(f"提取并打印视频 (数据包 {processed_packets_count}):  {extracted_video['video_title']}")

                    except Exception as e:
                        print(f"处理数据包 {resp_item.url} 时出错: {e}")
                        continue

                if total_videos_this_round == 0 and processed_packets_count > 0:
                    print(f"本轮捕捉到 {processed_packets_count} 个数据包，但未提取到任何视频，可能已到底部。")
                    if should_stop_scrolling:
                        break
                    print("未检测到结束文本，但本轮提取不到视频，停止采集。")
                    break

            except Exception as e:
                print(f"等待API响应时发生错误或超时: {e}")
                print("这可能意味着没有更多内容加载，或者网络问题。停止采集。")
                break

            if should_stop_scrolling:
                print("已检测到结束文本，不再执行滚动操作，并准备停止采集。")
                break

            tab = browser.ele('xpath://footer[@class="user-page-footer"]/div[1]')

            if tab:
                browser.scroll.to_see(tab)
            else:
                print("未找到用于滚动的目标元素，可能页面结构已改变或已到底部。停止采集。")
                break


        print("\n--- 采集流程结束 ---")
        return jsonify({'videos': all_extracted_videos})

    except Exception as e:
        error_msg = str(e)
        print(f"采集过程中出错: {error_msg}")
        return jsonify({'error': f'采集失败: {error_msg}'}), 500

    finally:
        if browser:
            try:
                print("正在关闭浏览器...")
                browser.quit()
                print("浏览器已关闭")
            except Exception as close_error:
                print(f"关闭浏览器时出错: {close_error}")
                pass

if __name__ == '__main__':
    start_xvfb_for_app() # Start Xvfb when the app runs

    # You might want to consider running Flask in a production-ready WSGI server like Gunicorn
    # in a real deployment, rather than directly using app.run()
    app.run(host='0.0.0.0', port=8000, debug=False)
    # The following line will only be reached if app.run() somehow exits without sys.exit
    stop_xvfb_for_app() # Ensure Xvfb is stopped if app.run exits for some reason
