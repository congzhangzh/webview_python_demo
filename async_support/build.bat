@echo off
chcp 65001 >nul 2>&1

echo 正在检查必要的文件...

rem 检查必要的JS库文件
set MISSING_FILES=0
if not exist preact.min.js set MISSING_FILES=1
if not exist hooks.min.js set MISSING_FILES=1
if not exist htm.min.js set MISSING_FILES=1

rem 检查补丁文件
if not exist asyncio_guest_run.py set MISSING_FILES=1

if %MISSING_FILES%==1 (
    echo 错误: 缺少必要的文件!
    echo 请确保JS库文件和补丁文件存在于当前目录
    exit /b 1
)

echo 检查PyInstaller是否已安装...
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 未安装PyInstaller，正在安装...
    pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo PyInstaller安装失败，请手动安装并重试
        exit /b 1
    )
)

echo 开始构建应用程序...
pyinstaller --name="App Manager" ^
    --windowed ^
    --clean ^
    --noconfirm ^
    --add-data "*.html;." ^
    --add-data "*.js;." ^
    --add-data "asyncio_guest_run.py;." ^
    --add-data "patches;patches" ^
    main_work_example_preact_with_async_support.py

if %ERRORLEVEL% neq 0 (
    echo 构建失败，请检查错误信息
    exit /b 1
)

echo 清理临时文件...
if exist build rmdir /s /q build

echo 构建成功！
echo APP Dir: %CD%\dist\App Manager\
echo 可执行文件: %CD%\dist\App Manager\App Manager.exe 
