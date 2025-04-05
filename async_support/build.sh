#!/bin/bash

echo "正在检查必要的文件..."

# 检查必要的JS库文件和补丁文件
MISSING_FILES=0
[ ! -f preact.min.js ] && MISSING_FILES=1 && echo "缺少 preact.min.js"
[ ! -f hooks.min.js ] && MISSING_FILES=1 && echo "缺少 hooks.min.js"
[ ! -f htm.min.js ] && MISSING_FILES=1 && echo "缺少 htm.min.js"
[ ! -f asyncio_guest_run.py ] && MISSING_FILES=1 && echo "缺少 asyncio_guest_run.py"

if [ $MISSING_FILES -eq 1 ]; then
    echo "错误: 缺少必要的文件!"
    echo "请确保JS库文件和补丁文件存在于当前目录"
    exit 1
fi

echo "检查PyInstaller是否已安装..."
pip show pyinstaller > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "未安装PyInstaller，正在安装..."
    pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "PyInstaller安装失败，请手动安装并重试"
        exit 1
    fi
fi

echo "开始构建应用程序..."
# 注意：Linux/macOS中使用冒号(:)作为路径分隔符
pyinstaller --name="App Manager" \
    --windowed \
    --clean \
    --noconfirm \
    --add-data "*.html:." \
    --add-data "*.js:." \
    --add-data "*.css:." \
    --add-data "asyncio_guest_run.py;." \
    --add-data "patches;patches" \
    main_work_example_preact_with_async_support.py

if [ $? -ne 0 ]; then
    echo "构建失败，请检查错误信息"
    exit 1
fi

echo "清理临时文件..."
[ -d build ] && rm -rf build

echo "构建成功！"
echo "应用程序位置: $(pwd)/dist/App Manager/"
echo "可执行文件: $(pwd)/dist/App Manager/App Manager"

# 使脚本在Linux/macOS上可执行
chmod +x "$(pwd)/dist/App Manager/App Manager"
