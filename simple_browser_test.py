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
    
    # 内存优化
    options.set_argument('--memory-pressure-off')
    options.set_argument('--max_old_space_size=4096')
    
    # 用户代理
    options.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 窗口大小
    options.set_argument('--window-size=1920,1080')
    
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
        
        # 使用Chromium类而不是ChromiumPage
        browser = Chromium(options)
        
        print("✅ 浏览器创建成功")
        
        # 3. 访问百度
        print("\n🌐 访问百度首页...")
        browser.get('https://www.baidu.com')
        
        # 等待页面加载
        time.sleep(5)
        
        # 4. 检查页面标题
        title = browser.title
        print(f"📄 页面标题: {title}")
        
        if '百度' in title or 'baidu' in title.lower():
            print("✅ 成功访问百度首页!")
            
            # 5. 获取页面信息
            url = browser.url
            print(f"🔗 当前URL: {url}")
            
            # 6. 尝试查找搜索框
            try:
                search_box = browser.ele('#kw')  # 百度搜索框ID
                if search_box:
                    print("✅ 找到搜索框元素")
                    
                    # 输入测试文本
                    search_box.input('DrissionPage测试')
                    print("✅ 输入测试文本成功")
                    
                    time.sleep(2)
                    
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
    
    # 运行测试
    success = test_basic_browser()
    
    if success:
        print("\n🎉 测试成功！可以继续下一步开发。")
        sys.exit(0)
    else:
        print("\n❌ 测试失败，请检查错误信息。")
        sys.exit(1)
