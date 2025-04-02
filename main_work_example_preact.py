import os
import subprocess
import json
import shutil
import time
import sys

from pathlib import Path
from webview.webview import Webview, Size, SizeHint
from urllib.parse import quote

import pathlib

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


# 主函数
def main():
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
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path=str(Path(__file__).with_suffix('.html'))
    #html_path = os.path.join(current_dir, 'index.html')
    webview.navigate(f"file://{html_path}")
    webview.run()

if __name__ == "__main__":
    main()
