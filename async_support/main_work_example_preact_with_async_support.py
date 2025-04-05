#
# Copyright 2020 Richard J. Sheridan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse

"""解析命令行参数"""
parser = argparse.ArgumentParser(description='本地程序管理助手')
parser.add_argument('--kill', '-k', action='store_true', 
                    help='杀死该程序的其他实例后退出')
parser.add_argument('--check', '-c', action='store_true',
                    help='检查该程序的其他实例但不杀死它们')
    # 解析命令行参数
args = parser.parse_args()

# it's very slow after hook import, do it just when needed
if not args.kill and not args.check:
    from asyncio_guest_run import asyncio_guest_run, schedule_on_asyncio

import pathlib
import traceback
from queue import Queue

import win32api
import win32con
import win32gui

import asyncio
from webview import Webview, SizeHint, Size

import os
import psutil
import sys

ASYNCIO_MSG = win32con.WM_APP + 3

# 使用线程安全的 Queue 代替 deque
trio_functions = Queue()

def do_trio():
    """Process all pending trio tasks in the queue"""
    while not trio_functions.empty():
        try:
            # 获取并执行一个任务
            func = trio_functions.get()
            func()
        except Exception as e:
            print(rf"{__file__}:{do_trio.__name__} e: {e}")
            print(traceback.format_exc())
            raise e

class WebviewHost:
    def __init__(self, webview):
        self.webview = webview
        self.mainthreadid = win32api.GetCurrentThreadId()
        # create event queue with null op
        win32gui.PeekMessage(
            win32con.NULL, win32con.WM_USER, win32con.WM_USER, win32con.PM_NOREMOVE
        )
        self.create_message_window()

    def create_message_window(self):
        # 注册窗口类
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.trio_wndproc_func
        wc.lpszClassName = "TrioMessageWindow"
        win32gui.RegisterClass(wc)
        
        # 创建隐藏窗口
        self.msg_hwnd = win32gui.CreateWindowEx(
            0, "TrioMessageWindow", "Trio Message Window",
            0, 0, 0, 0, 0, 0, 0, None, None
        )

    def trio_wndproc_func(self, hwnd, msg, wparam, lparam):
        if msg == ASYNCIO_MSG:
            # 处理所有排队的 trio 任务
            do_trio()
            return 0
        # elif msg == DESTROY_WINDOW_MSG:
        #     # 在正确的线程中销毁窗口
        #     win32gui.DestroyWindow(hwnd)
        #     return 0
        else:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def run_sync_soon_threadsafe(self, func):
        """先添加函数到队列，后发送消息"""
        trio_functions.put(func)
        win32api.PostMessage(self.msg_hwnd, ASYNCIO_MSG, 0, 0)

    def run_sync_soon_not_threadsafe(self, func):
        """与 threadsafe 相同，保持一致性"""
        trio_functions.put(func)
        win32api.PostMessage(self.msg_hwnd, ASYNCIO_MSG, 0, 0)

    def done_callback(self, outcome):
        """non-blocking request to end the main loop"""
        print(f"Outcome: {outcome}")
        print(f"大功告成: {outcome}")
        if isinstance(outcome, Error):
            exc = outcome.error
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            exitcode = 1
        else:
            exitcode = 0
        self.display.dialog.PostMessage(win32con.WM_CLOSE, 0, 0)
        self.display.dialog.close()
        # 通过消息请求主线程销毁窗口
        # win32api.PostMessage(self.msg_hwnd, DESTROY_WINDOW_MSG, 0, 0)
        win32gui.PostQuitMessage(exitcode)

    def mainloop(self):
        self.webview.run()

import os
import subprocess
import json
import sys
import logging
import datetime
from logging.handlers import RotatingFileHandler

from pathlib import Path
from webview.webview import Webview, Size, SizeHint
from urllib.parse import quote

# 工具路径配置
USER_HOME = str(Path.home())
VS_CODE_PATH = os.path.join(USER_HOME, ".vscode")
VS_CONTINUE_PATH = os.path.join(VS_CODE_PATH, "extensions", "continue")
CONAN_HOME = os.path.join(USER_HOME, ".conan")

# Python函数 - Conan管理
def get_conan_status():
    """获取Conan安装状态"""
    try:
        result = subprocess.run(["conan", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return {
                "installed": True,
                "version": result.stdout.strip()
            }
        return {"installed": False}
    except FileNotFoundError:
        return {"installed": False}

def install_conan():
    """安装Conan"""
    try:
        result = subprocess.run(["pip", "install", "conan"], capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "message": "Conan安装成功"}
        return {"success": False, "message": f"安装失败: {result.stderr}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def uninstall_conan():
    """卸载Conan"""
    try:
        result = subprocess.run(["pip", "uninstall", "-y", "conan"], capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "message": "Conan卸载成功"}
        return {"success": False, "message": f"卸载失败: {result.stderr}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_conan_cache_settings():
    """获取Conan缓存设置"""
    settings_path = os.path.join(CONAN_HOME, "settings.yml")
    if not os.path.exists(settings_path):
        return {"exists": False}
    
    try:
        with open(settings_path, 'r') as f:
            return {"exists": True, "content": f.read()}
    except Exception as e:
        return {"exists": False, "error": str(e)}

def update_conan_cache_settings(settings):
    """更新Conan缓存设置"""
    settings_path = os.path.join(CONAN_HOME, "settings.yml")
    try:
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, 'w') as f:
            f.write(settings)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Python函数 - VS Code Continue管理
def get_vscode_continue_status():
    """获取VS Code Continue状态"""
    if os.path.exists(VS_CONTINUE_PATH):
        try:
            with open(os.path.join(VS_CONTINUE_PATH, "package.json"), 'r') as f:
                data = json.load(f)
                version = data.get("version", "未知")
            return {
                "installed": True,
                "version": version
            }
        except:
            return {"installed": True, "version": "未知"}
    return {"installed": False}

def install_vscode_continue():
    """安装VS Code Continue"""
    try:
        result = subprocess.run(["code", "--install-extension", "continue.continue"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "message": "VS Code Continue安装成功"}
        return {"success": False, "message": f"安装失败: {result.stderr}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def uninstall_vscode_continue():
    """卸载VS Code Continue"""
    try:
        result = subprocess.run(["code", "--uninstall-extension", "continue.continue"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "message": "VS Code Continue卸载成功"}
        return {"success": False, "message": f"卸载失败: {result.stderr}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Python函数 - VS Code Cppcheck插件管理
def get_cppcheck_status():
    """获取Cppcheck插件状态"""
    try:
        result = subprocess.run(["code", "--list-extensions"], capture_output=True, text=True)
        if "jbenden.c-cpp-flylint" in result.stdout:
            return {"installed": True}
        return {"installed": False}
    except Exception:
        return {"installed": False, "error": "无法检查状态"}

def install_cppcheck():
    """安装Cppcheck插件"""
    try:
        result = subprocess.run(["code", "--install-extension", "jbenden.c-cpp-flylint"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "message": "Cppcheck插件安装成功"}
        return {"success": False, "message": f"安装失败: {result.stderr}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def uninstall_cppcheck():
    """卸载Cppcheck插件"""
    try:
        result = subprocess.run(["code", "--uninstall-extension", "jbenden.c-cpp-flylint"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "message": "Cppcheck插件卸载成功"}
        return {"success": False, "message": f"卸载失败: {result.stderr}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Python functions that can be called from JavaScript
def hello():
    #webview.eval("updateFromPython('Hello from Python!')")
    return "Hello from Python!"

def add(a, b):
    return a + b

def demo():
    return "demo"

async def counter():
    count = 0   
    while True:
        await asyncio.sleep(5)
        count += 1
        #print(f"I am alive: {count}")

def kill_other_instances(check_only=False):
    """查找并终止与当前程序相同的其他实例
    
    Args:
        check_only: 如果为True，只检查不杀死进程
    
    Returns:
        tuple: (是否找到实例, 找到的PID列表)
    """
    current_pid = os.getpid()
    current_script_name = os.path.basename(__file__)
    
    found_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        try:
            # 跳过当前进程
            if proc.info['pid'] == current_pid:
                continue
                
            # 检查是否是Python进程
            if proc.info['name'].lower() in ('python.exe', 'pythonw.exe', 'python', 'python3'):
                # 获取命令行参数
                cmdline = proc.info['cmdline']
                
                # 检查命令行参数中是否包含当前脚本名
                if cmdline and len(cmdline) > 1:
                    # 判断脚本名称是否匹配，而不是完整路径
                    script_arg = os.path.basename(cmdline[1])
                    if script_arg == current_script_name:
                        # 打印找到的进程信息（包括工作目录）
                        print(f"发现程序的另一个实例 (PID: {proc.info['pid']}), 运行于: {proc.info['cwd']}")
                        found_processes.append(proc.info['pid'])
                        
                        # 只在非check_only模式下杀死进程
                        if not check_only:
                            print(f"正在终止进程 (PID: {proc.info['pid']})")
                            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"访问进程时出错: {e}")
            continue
    
    # 等待被终止的进程
    if found_processes and not check_only:
        psutil.wait_procs([psutil.Process(pid) for pid in found_processes if psutil.pid_exists(pid)], timeout=3)
    
    return bool(found_processes), found_processes


# 全局日志设置
def setup_file_logging():
    """设置简单的全局文件日志"""
    # 创建日志目录(用户文档目录下)
    log_dir = '.'
    os.makedirs(log_dir, exist_ok=True)
    
    # 日志文件路径
    log_file = os.path.join(log_dir, 'app.log')
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 创建文件处理器(最大5MB，保留3个备份)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    
    # 记录启动信息
    logging.info("=" * 50)
    logging.info(f"程序启动 - {datetime.datetime.now()}")
    logging.info(f"版本: 1.0.0")
    logging.info(f"运行路径: {os.path.abspath('.')}")
    logging.info("=" * 50)
    
    return logger

logger = setup_file_logging()

# 主函数
def main():
    # 如果指定了--kill参数，杀死其他实例并退出
    if args.kill:
        killed, pids = kill_other_instances(check_only=False)
        if killed:
            print(f"已终止 {len(pids)} 个其他程序实例: {pids}")
        else:
            print("未发现其他程序实例")
        return
        
    # 如果指定了--check参数，只检查其他实例
    if args.check:
        found, pids = kill_other_instances(check_only=True)
        if found:
            print(f"发现 {len(pids)} 个其他程序实例: {pids}")
        else:
            print("未发现其他程序实例")
        return
    
    # 正常启动前，先杀死其他实例
    # killed, pids = kill_other_instances(check_only=False)
    # if killed:
    #     print(f"已终止 {len(pids)} 个其他程序实例: {pids}")
    
    # use WEBVIEW_VERSION, WEBVIEW_DOWNLOAD_BASE to custom where to download webview
    # refs:
    #   https://github.com/congzhangzh/webview_python?tab=readme-ov-file#environment-variables
    webview = Webview(debug=True)

    # Bind Python functions
    webview.bind("hello", hello)
    webview.bind("add", add)
    webview.bind("demo", demo)

    # Configure window
    webview.title = "Python-JavaScript Binding Demo"
    webview.size = Size(640, 480, SizeHint.FIXED)
    
    # 绑定Python函数
    webview.bind("getConanStatus", get_conan_status)
    webview.bind("installConan", install_conan)
    webview.bind("uninstallConan", uninstall_conan)
    webview.bind("getConanCacheSettings", get_conan_cache_settings)
    webview.bind("updateConanCacheSettings", update_conan_cache_settings)
    
    webview.bind("getVSCodeContinueStatus", get_vscode_continue_status)
    webview.bind("installVSCodeContinue", install_vscode_continue)
    webview.bind("uninstallVSCodeContinue", uninstall_vscode_continue)
    
    webview.bind("getCppcheckStatus", get_cppcheck_status)
    webview.bind("installCppcheck", install_cppcheck)
    webview.bind("uninstallCppcheck", uninstall_cppcheck)
    
    # 检查JS库是否已下载
    current_dir = os.path.dirname(os.path.abspath(__file__))
    required_libs = ['preact.min.js', 'hooks.min.js', 'htm.min.js']
    missing_libs = [lib for lib in required_libs if not os.path.exists(os.path.join(current_dir, lib))]

    if missing_libs:
        # 提示用户运行下载脚本
        script_name = 'download_libs.bat' if sys.platform == 'win32' else 'download_libs.sh'
        print(f"错误: 缺少必要的JavaScript库文件: {', '.join(missing_libs)}")
        print(f"请运行 {os.path.join(current_dir, script_name)} 下载所需库文件")
        sys.exit(1)
    
    # 配置窗口
    webview.title = "本地程序管理助手"
    webview.size = Size(1024, 768, SizeHint.NONE)
    
    html_path=str(Path(__file__).resolve().with_suffix('.html'))
    print(f"html_path: {html_path}")
    webview.navigate(f"file://{html_path}")
        # --begin-- guest run
    host = WebviewHost(webview)
    asyncio_guest_run(
        counter,
        run_sync_soon_threadsafe=host.run_sync_soon_threadsafe,
        run_sync_soon_not_threadsafe=host.run_sync_soon_not_threadsafe,
        done_callback=host.done_callback,
    )
    host.mainloop()
    # --end-- guest run

if __name__ == "__main__":
    main()
