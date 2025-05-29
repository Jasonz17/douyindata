from flask import Flask, request, jsonify, render_template
from DrissionPage import ChromiumPage, ChromiumOptions
from urllib.parse import urlparse, parse_qs
import json
import os

app = Flask(__name__)

# --- Configuration for DrissionPage (from video_data_final.py) ---
# 定义一个用于保存浏览器用户资料的目录路径
# 注意：在 Docker 部署时，这个路径可能需要调整到容器内部的持久化存储位置
user_data_dir = '/app/drissionpage'
os.makedirs(user_data_dir, exist_ok=True)

# 创建 ChromiumOptions 实例
co = ChromiumOptions()
# 设置浏览器用户资料的保存路径
co.set_user_data_path(user_data_dir)
co.set_argument('--no-sandbox')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--disable-gpu')
# --- End DrissionPage Configuration ---

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
    all_extracted_videos = [] # 存储所有提取到的视频数据

    try:
        browser = ChromiumPage(co)
        browser.listen.start('aweme/v1/web/aweme/post/')

        target_profile_url = page_url # 使用前端传入的 pageurl
        browser.get(target_profile_url)
        print(f"正在访问抖音主页: {browser.url}")

        page_counter = 0 # 用于跟踪采集的“页”数
        should_stop_scrolling = False # 新增标志位，控制是否停止滚动和退出

        while True: # 循环直到遇到停止条件
            page_counter += 1
            print(f'\n正在采集第{page_counter}页的数据')

            # --- 1. 判定停止条件：页面上是否出现“暂时没有更多了” ---
            # 如果检测到停止文本，设置标志位，但当前循环仍要处理数据
            no_more_element = browser.ele('xpath://*[text()="暂时没有更多了"]', timeout=1) # timeout=1 表示非阻塞查找
            if no_more_element:
                print("检测到 '暂时没有更多了' 文本。将处理完当前数据后停止滚动。")
                should_stop_scrolling = True # 设置标志位

            # --- 2. 获取所有数据包 (根据文档，使用 listen.wait(count, timeout, fit_count=False)) ---
            try:
                # 使用你的原始代码中的 listen.wait 参数
                all_captured_responses = browser.listen.wait(count=9999, timeout=10, fit_count=False)

                if not all_captured_responses: # 如果返回的是空列表
                    print("本轮滚动未捕捉到任何新的API响应，可能已到底部或加载失败。")
                    if should_stop_scrolling: # 如果已经检测到停止文本，并且没有新数据包，直接停止
                        break
                    # 如果没有检测到停止文本，但也没有新数据包，也应该停止
                    print("未检测到结束文本，但本轮未捕捉到任何新数据包，也未提取到视频，停止采集。")
                    break # 确保没有捕捉到响应时能停止

                processed_packets_count = 0 # 记录本次滚动获取的数据包数量
                total_videos_this_round = 0 # 记录本次滚动提取的视频数量

                for resp_item in all_captured_responses: # 遍历所有捕获到的响应
                    try:
                        # 再次检查URL，确保只处理目标API响应
                        if 'aweme/v1/web/aweme/post/' in resp_item.url:
                            # 根据您原始代码能运行的逻辑，直接使用 resp_item.response.body
                            json_data = resp_item.response.body
                            processed_packets_count += 1

                            # --- 3. 提取并处理数据 (保持你的原始逻辑) ---
                            video_data = json_data['aweme_list'] # 保持你原始代码的直接访问方式
                            if not video_data:
                                print(f"数据包 {processed_packets_count} (URL: {resp_item.url}) 中没有 aweme_list 数据。")
                                continue # 跳过当前数据包，处理下一个

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
                                all_extracted_videos.append(extracted_video) # 将提取到的视频数据添加到列表中
                                total_videos_this_round += 1
                                print(f"提取并打印视频 (数据包 {processed_packets_count}):  {extracted_video['video_title']}")

                    except Exception as e:
                        # 捕获处理数据包时可能出现的任何错误
                        print(f"处理数据包 {resp_item.url} 时出错: {e}")
                        continue

                if total_videos_this_round == 0 and processed_packets_count > 0:
                    print(f"本轮捕捉到 {processed_packets_count} 个数据包，但未提取到任何视频，可能已到底部。")
                    if should_stop_scrolling: # 如果已经检测到停止文本，并且没有新数据包，直接停止
                        break
                    print("未检测到结束文本，但本轮提取不到视频，停止采集。")
                    break # 如果处理了数据包但没新增视频，也停止

            except Exception as e: # 捕获 listen.wait() 可能的超时或其他异常
                print(f"等待API响应时发生错误或超时: {e}")
                print("这可能意味着没有更多内容加载，或者网络问题。停止采集。")
                break # 退出 while 循环

            # --- 4. 判定是否停止滚动和退出循环 (新的逻辑) ---
            if should_stop_scrolling:
                print("已检测到结束文本，不再执行滚动操作，并准备停止采集。")
                break # 退出外层循环，结束采集

            # --- 5. 定位页面元素并滚动 ---
            tab = browser.ele('xpath://footer[@class="user-page-footer"]/div[1]')

            # 滑动
            if tab:
                browser.scroll.to_see(tab)
            else:
                print("未找到用于滚动的目标元素，可能页面结构已改变或已到底部。停止采集。")
                break # 如果找不到滚动目标，也停止循环


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
    # 确保 templates 文件夹存在，并且 index.html 位于其中
    # 否则 Flask 找不到模板文件
    # 在 Docker 环境中，这个路径也需要正确配置
    app.run(host='0.0.0.0', port=8000, debug=False)