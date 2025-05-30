import os
import time
# 确保导入了 DrissionPage 的 ChromiumPage 和 ChromiumOptions
from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage.common import By

# 确保导入 xvfb-display 库
from xvfb_display import XvfbDisplay

# --- create_chrome_options 函数（请替换为你修正后的，包含 set_pref 的版本）---
def create_chrome_options():
    """创建Chrome选项配置"""
    options = ChromiumOptions()

    # 设置无头模式，确保在没有显示器的服务器上运行
    options.set_headless(True)

    # 禁用沙箱，解决一些环境下的权限问题
    options.set_argument('--no-sandbox')
    # 禁用GPU硬件加速
    options.set_argument('--disable-gpu')
    # 禁用 /dev/shm 使用，避免内存不足问题
    options.set_argument('--disable-dev-shm-usage')
    # 禁用弹窗，确保自动化流程不受干扰
    options.set_pref('profile.default_content_settings.popups', 0)
    # 隐藏是否保存密码的提示
    options.set_pref('credentials_enable_service', False)

    # 设置一个常见的User-Agent
    options.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
    
    # !!! 关键设置：通过 set_pref 设置 Accept-Language !!!
    options.set_pref('intl.accept_languages', 'zh-CN,zh;q=0.9,en;q=0.8')

    # 可选：设置浏览器窗口大小
    options.set_size(1920, 1080)

    # 如果浏览器路径不是默认，需要指定
    # options.set_browser_path('/usr/bin/google-chrome') # 根据你的实际安装路径调整

    return options

# --- test_douyin_page 函数 ---
def test_douyin_page():
    print("🚀 创建浏览器实例...")
    page = None # 初始化 page 变量
    try:
        options = create_chrome_options()
        page = ChromiumPage(options) # 创建 ChromiumPage 实例

        # 定义截图路径
        screenshot_path = './douyin_screenshot.png'

        # --- 新增步骤：检查 Accept-Language 头是否正确发送 ---
        print("\n🔍 正在检查 Accept-Language 头是否发送正确...")
        # 访问一个专门显示 HTTP 请求头的网站
        page.get('https://httpbin.org/headers')
        time.sleep(3) # 等待页面加载，确保所有头信息都已显示
        
        # 获取页面 body 的文本内容，其中包含所有发送的请求头
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

        # 抖音的最终访问 URL，与你提供的一致
        douyin_url = "https://www.douyin.com/?vid=7497916567561309466&recommend=1"
        print(f"\n🔗 正在访问抖音页面: {douyin_url}")
        page.get(douyin_url)

        # 确保页面加载完成，可以等待某个元素出现，或者简单地等待几秒
        print("⏳ 等待抖音页面加载...")
        time.sleep(8) # 增加等待时间，确保页面元素和内容完全加载，包括异步加载的内容

        print(f"✅ 成功访问抖音页面！")

        print(f"\n📸 正在截图并保存到: {screenshot_path}")
        page.get_screenshot(path=screenshot_path)
        print("✅ 截图成功！")
        return True

    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback # 导入 traceback 模块以便打印完整错误栈
        traceback.print_exc() # 打印详细的错误信息
        return False
    finally:
        if page: # 确保 page 对象存在才执行 quit
            print("\n🧹 清理资源...")
            page.quit() # 关闭浏览器
            print("✅ 浏览器已关闭")

# --- 主执行块（保持不变）---
if __name__ == "__main__":
    xvfb = None
    try:
        print("启动Xvfb进程...")
        # 启动 Xvfb
        xvfb = XvfbDisplay(width=1920, height=1080, colordepth=24)
        xvfb.start()
        print("✅ Xvfb已启动")

        # 运行测试
        if test_douyin_page():
            print("\n🎉 抖音页面测试成功！截图已保存到 douyin_screenshot.png。")
        else:
            print("\n😭 抖音页面测试失败。")

    except Exception as e:
        print(f"\n❌ 启动Xvfb或测试过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if xvfb:
            print("停止Xvfb进程...")
            xvfb.stop()
            print("✅ Xvfb已停止")
        print("测试完成!")
