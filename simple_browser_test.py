#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import signal
from DrissionPage import Chromium, ChromiumOptions

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
            
            # 启动Xvfb
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

def create_chrome_options():
    """创建Chrome选项配置"""
    options = ChromiumOptions()
    
    # 基础选项
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--disable-gpu')
    options.set_argument('--disable-web-security')
    options.set_argument('--disable-features=VizDisplayCompositor')
    options.set_argument('--disable-extensions')
    options.set_argument('--disable-plugins')
    options.set_argument('--disable-images')  # 加速加载
    
    # 添加更多稳定性参数
    options.set_argument('--no-first-run')
    options.set_argument('--no-default-browser-check')
    options.set_argument('--disable-default-apps')
    options.set_argument('--disable-popup-blocking')
    options.set_argument('--disable-translate')
    options.set_argument('--disable-background-timer-throttling')
    options.set_argument('--disable-renderer-backgrounding')
    options.set_argument('--disable-backgrounding-occluded-windows')
    
    # 内存优化
    options.set_argument('--memory-pressure-off')
    options.set_argument('--max_old_space_size=4096')
    
    # 用户代理
    options.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 窗口大小
    options.set_argument('--window-size=1920,1080')
    
    # 设置远程调试端口
    options.set_argument('--remote-debugging-port=9222')
    
    # 指定Chrome路径（如果需要）
    chrome_path = '/usr/bin/google-chrome'
    if os.path.exists(chrome_path):
        options.set_browser_path(chrome_path)
    
    # 重要：不设置headless，让Xvfb处理显示
    # options.headless()  # 不调用这个方法
    
    return options

def test_basic_browser():
    """基础浏览器测试"""
    xvfb = None
    browser = None
    page = None
    
    try:
        print("="*50)
        print("开始DrissionPage + Xvfb 测试")
        print("="*50)
        
        # 1. 启动Xvfb
        xvfb = XvfbManager()
        if not xvfb.start():
            print("❌ Xvfb启动失败，退出测试")
            return False
        
        # 2. 创建浏览器实例
        print("\n🚀 创建浏览器实例...")
        options = create_chrome_options()
        
        # 创建Chromium浏览器管理器
        browser = Chromium(options)
        
        # 获取页面对象 - 这是关键修复点！
        page = browser.latest_tab  # 或者使用 browser.get_tab() 或 browser.new_tab()
        
        print("✅ 浏览器创建成功")
        
        # 3. 访问百度
        print("\n🌐 访问百度首页...")
        page.get('https://www.baidu.com')
        
        # 等待页面加载
        time.sleep(5)
        
        # 4. 检查页面标题
        title = page.title
        print(f"📄 页面标题: {title}")
        
        if '百度' in title or 'baidu' in title.lower():
            print("✅ 成功访问百度首页!")
            
            # 5. 获取页面信息
            url = page.url
            print(f"🔗 当前URL: {url}")
            
            # 6. 尝试查找搜索框
            try:
                search_box = page.ele('#kw')  # 百度搜索框ID
                if search_box:
                    print("✅ 找到搜索框元素")
                    
                    # 输入测试文本
                    search_box.input('DrissionPage测试')
                    print("✅ 输入测试文本成功")
                    
                    time.sleep(2)
                    
                    # 尝试点击搜索按钮
                    search_btn = page.ele('#su')  # 百度搜索按钮ID
                    if search_btn:
                        search_btn.click()
                        print("✅ 点击搜索按钮成功")
                        time.sleep(3)
                        
                        # 检查搜索结果页面
                        new_title = page.title
                        print(f"📄 搜索后页面标题: {new_title}")
                    
                else:
                    print("⚠️  未找到搜索框，可能页面结构有变化")
                    
            except Exception as e:
                print(f"⚠️  操作搜索框时出错: {e}")
            
            return True
        else:
            print(f"❌ 页面标题异常: {title}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        if browser:
            try:
                browser.quit()
                print("✅ 浏览器已关闭")
            except:
                pass
                
        if xvfb:
            xvfb.stop()
            print("✅ Xvfb已停止")
        
        print("测试完成!")

def test_alternative_approach():
    """测试另一种创建页面的方法"""
    xvfb = None
    browser = None
    
    try:
        print("="*50)
        print("测试备用方法：直接创建新标签页")
        print("="*50)
        
        # 1. 启动Xvfb
        xvfb = XvfbManager()
        if not xvfb.start():
            print("❌ Xvfb启动失败，退出测试")
            return False
        
        # 2. 创建浏览器和新标签页
        print("\n🚀 创建浏览器实例和新标签页...")
        options = create_chrome_options()
        browser = Chromium(options)
        
        # 创建新标签页
        page = browser.new_tab()
        
        print("✅ 新标签页创建成功")
        
        # 3. 访问网站
        print("\n🌐 访问测试网站...")
        page.get('https://httpbin.org/get')  # 使用一个简单的测试网站
        
        time.sleep(3)
        
        # 检查页面内容
        title = page.title
        print(f"📄 页面标题: {title}")
        
        # 获取页面文本内容
        try:
            body_text = page.ele('body').text
            if 'httpbin' in body_text.lower() or 'origin' in body_text.lower():
                print("✅ 成功访问测试网站并获取内容!")
                print(f"页面内容预览: {body_text[:200]}...")
                return True
            else:
                print(f"⚠️  页面内容异常: {body_text[:100]}")
        except Exception as e:
            print(f"⚠️  获取页面内容时出错: {e}")
            
        return False
        
    except Exception as e:
        print(f"❌ 备用测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        if browser:
            try:
                browser.quit()
                print("✅ 浏览器已关闭")
            except:
                pass
                
        if xvfb:
            xvfb.stop()
            print("✅ Xvfb已停止")

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
        from DrissionPage import Chromium, ChromiumOptions
        import DrissionPage
        print(f"✅ DrissionPage版本: {DrissionPage.__version__}")
    except ImportError:
        print("❌ DrissionPage未安装")
    except:
        print("✅ DrissionPage已安装")
    
    print("-" * 50)

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
    print("运行主测试")
    success1 = test_basic_browser()
    
    # 运行备用测试
    print("\n" + "="*50)
    print("运行备用测试")
    success2 = test_alternative_approach()
    
    if success1 or success2:
        print("\n🎉 至少一个测试成功！可以继续下一步开发。")
        sys.exit(0)
    else:
        print("\n❌ 所有测试都失败，请检查错误信息。")
        sys.exit(1)
