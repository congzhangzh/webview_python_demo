import os
import subprocess
import json
import shutil
import time
import sys
import argparse
import pathlib

from pathlib import Path
from webview.webview import Webview, Size, SizeHint
from urllib.parse import quote # Keep quote for potential future use in file paths


# --- Constants and Paths ---
USER_HOME = str(Path.home())
VS_CODE_PATH = os.path.join(USER_HOME, ".vscode")
VS_CONTINUE_PATH = os.path.join(VS_CODE_PATH, "extensions", "continue") # Adjust if needed
CONAN_HOME = os.path.join(USER_HOME, ".conan")
PROJECT_ROOT = Path(__file__).parent.resolve()
REACT_FRONTEND_DIR = PROJECT_ROOT
REACT_BUILD_DIR = REACT_FRONTEND_DIR / 'dist'

# --- Helper Functions (Copied from main_work_example_preact.py) ---

# Python函数 - Conan管理
def get_conan_status():
    """获取Conan安装状态"""
    try:
        # Use shell=True on Windows if conan is in PATH but not directly executable
        is_windows = sys.platform == 'win32'
        result = subprocess.run(["conan", "--version"], capture_output=True, text=True, check=False, shell=is_windows)
        if result.returncode == 0:
            return {
                "installed": True,
                "version": result.stdout.strip()
            }
        print(f"Conan status check failed: {result.stderr}")
        return {"installed": False}
    except FileNotFoundError:
        print("Conan command not found.")
        return {"installed": False}
    except Exception as e:
        print(f"Error checking Conan status: {e}")
        return {"installed": False}

def install_conan():
    """安装Conan"""
    try:
        # Consider using pip installed in a virtual environment if possible
        result = subprocess.run([sys.executable, "-m", "pip", "install", "conan"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return {"success": True, "message": "Conan安装成功"}
        return {"success": False, "message": f"安装失败: {result.stderr or result.stdout}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def uninstall_conan():
    """卸载Conan"""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "conan"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return {"success": True, "message": "Conan卸载成功"}
        return {"success": False, "message": f"卸载失败: {result.stderr or result.stdout}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_conan_cache_settings():
    """获取Conan缓存设置"""
    settings_path = os.path.join(CONAN_HOME, "settings.yml")
    if not os.path.exists(settings_path):
        return {"exists": False, "content": "# Conan settings.yml not found."}

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return {"exists": True, "content": f.read()}
    except Exception as e:
        return {"exists": False, "error": str(e), "content": f"# Error reading settings.yml: {e}"}

def update_conan_cache_settings(settings_content):
    """更新Conan缓存设置"""
    settings_path = os.path.join(CONAN_HOME, "settings.yml")
    try:
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(settings_content)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Python函数 - VS Code Continue管理
def get_vscode_continue_status():
    """获取VS Code Continue状态"""
    # This path might vary depending on VS Code installation type (User vs System)
    # A more robust check might involve listing extensions via `code --list-extensions`
    extensions_dir = VS_CODE_PATH / "extensions"
    try:
        continue_dirs = [d for d in extensions_dir.iterdir() if d.is_dir() and d.name.startswith('continue.continue-')]
        if not continue_dirs:
            return {"installed": False}

        # Assume the latest version is the installed one if multiple exist
        latest_continue_dir = max(continue_dirs, key=lambda d: d.stat().st_mtime)
        package_json_path = latest_continue_dir / "package.json"

        if package_json_path.exists():
            with open(package_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                version = data.get("version", "未知")
            return {"installed": True, "version": version, "path": str(latest_continue_dir)}
        else:
            return {"installed": True, "version": "未知 (package.json missing)", "path": str(latest_continue_dir)}
    except FileNotFoundError:
         # extensions dir might not exist
         return {"installed": False}
    except Exception as e:
        print(f"Error checking VSCode Continue status: {e}")
        return {"installed": False, "error": str(e)}


def _run_code_command(args):
    """Helper to run VS Code command line"""
    try:
        # Use shell=True on Windows if 'code' is in PATH but needs shell resolution
        is_windows = sys.platform == 'win32'
        result = subprocess.run(["code"] + args, capture_output=True, text=True, check=False, shell=is_windows)
        if result.returncode == 0:
            return {"success": True, "message": result.stdout.strip() or f"Command '{' '.join(['code'] + args)}' executed successfully."}
        else:
            # Combine stdout and stderr for potentially more informative error messages
            error_message = f"Command failed (code {result.returncode}): {result.stderr.strip() or result.stdout.strip()}"
            print(error_message)
            return {"success": False, "message": error_message}
    except FileNotFoundError:
         error_message = "VS Code command 'code' not found in PATH. Is VS Code installed and added to PATH?"
         print(error_message)
         return {"success": False, "message": error_message}
    except Exception as e:
        error_message = f"Failed to run VS Code command: {e}"
        print(error_message)
        return {"success": False, "message": error_message}


def install_vscode_continue():
    """安装VS Code Continue"""
    return _run_code_command(["--install-extension", "continue.continue", "--force"]) # Add --force to overwrite if needed

def uninstall_vscode_continue():
    """卸载VS Code Continue"""
    return _run_code_command(["--uninstall-extension", "continue.continue"])

# Python函数 - VS Code Cppcheck插件管理 (using C/C++ Flylint)
def get_cppcheck_status():
    """获取Cppcheck插件状态 (jbenden.c-cpp-flylint)"""
    ext_id = "jbenden.c-cpp-flylint"
    result = _run_code_command(["--list-extensions"])
    if result["success"] and ext_id in result["message"]:
         return {"installed": True}
    # Even if command failed, we know it's not installed this way
    return {"installed": False, "error": result.get("message") if not result["success"] else None}


def install_cppcheck():
    """安装Cppcheck插件 (jbenden.c-cpp-flylint)"""
    return _run_code_command(["--install-extension", "jbenden.c-cpp-flylint", "--force"])

def uninstall_cppcheck():
    """卸载Cppcheck插件 (jbenden.c-cpp-flylint)"""
    return _run_code_command(["--uninstall-extension", "jbenden.c-cpp-flylint"])


# --- Main Application Logic ---
def main():
    # os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = " --remote-debugging-port=9222 "
    parser = argparse.ArgumentParser(description="Local App Management Helper with React Frontend")
    parser.add_argument('--debug-frontend', action='store_true',
                        help='Load frontend from Vite dev server (requires `npm run dev` in react-frontend)')
    parser.add_argument('--vite-url', default='http://localhost:5173',
                        help='URL of the Vite dev server')
    args = parser.parse_args()

    # --- Create Webview Window ---
    # Pass pythonnet flags for potential C# integration if needed later
    # webview.config.use_pythonnet = True
    #window = Webview(debug=True)
    window = Webview(debug=True)
    window.title = "本地程序管理助手 (React)"
    # window.size = Size(1024, 768, SizeHint.NONE) # Set size if needed

    # --- Bind Python functions to JS API ---
    # Note: JS will call these via `window.pywebview.api.<func_name>(...)`
    api = {
        "getConanStatus": get_conan_status,
        "installConan": install_conan,
        "uninstallConan": uninstall_conan,
        "getConanCacheSettings": get_conan_cache_settings,
        "updateConanCacheSettings": update_conan_cache_settings,
        "getVSCodeContinueStatus": get_vscode_continue_status,
        "installVSCodeContinue": install_vscode_continue,
        "uninstallVSCodeContinue": uninstall_vscode_continue,
        "getCppcheckStatus": get_cppcheck_status,
        "installCppcheck": install_cppcheck,
        "uninstallCppcheck": uninstall_cppcheck,
        # Add simple test functions if needed
        "hello": lambda: "Hello from Python backend!",
        "add": lambda a, b: a + b,
    }
    [window.bind(name, impl) for name, impl in api.items()]


    # --- Determine Frontend URL ---
    if args.debug_frontend:
        frontend_url = args.vite_url
        print(f"--- React Debug Mode: Loading frontend from Vite Dev Server @ {frontend_url} ---")
        print("--- Ensure 'npm run dev' is running in the 'react-frontend' directory! ---")
    else:
        # Production mode: Load from build directory
        index_html_path = REACT_BUILD_DIR / 'index.html'
        if not index_html_path.exists():
            print(f"[ERROR] Production build file not found: {index_html_path}")
            print(f"[ERROR] Please run 'npm run build' inside the '{REACT_FRONTEND_DIR.name}' directory.")
            print("[ERROR] Or, run this script with '--debug-frontend' to use the Vite dev server.")
            sys.exit(1)
        # Use file URI scheme for local files
        frontend_url = index_html_path.as_uri()
        print(f"--- React Production Mode: Loading frontend from {frontend_url} ---")


    # --- Start Webview ---
    print(f"Starting pywebview window with URL: {frontend_url}")
    window.navigate(frontend_url)
    window.run() # Blocks until the window is closed


if __name__ == "__main__":
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"React Frontend Dir: {REACT_FRONTEND_DIR}")
    print(f"React Build Dir: {REACT_BUILD_DIR}")
    main()
