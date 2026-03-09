@echo off
echo ========================================
echo  Voice Agent - Windows 安装脚本
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 创建虚拟环境...
python -m venv .venv
if errorlevel 1 (
    echo [错误] 创建虚拟环境失败
    pause
    exit /b 1
)

echo [2/4] 激活虚拟环境...
call .venv\Scripts\activate

echo [3/4] 升级 pip...
python -m pip install --upgrade pip --quiet

echo [4/4] 安装依赖（使用预编译包）...
pip install -r requirements.txt --only-binary :all: --quiet
if errorlevel 1 (
    echo.
    echo [警告] 部分包安装失败，尝试不使用 --only-binary 参数...
    pip install -r requirements.txt
)

echo.
echo ========================================
echo  安装完成！
echo ========================================
echo.
echo 下一步：
echo 1. 复制 .env.example 为 .env
echo 2. 编辑 .env 填入你的 DASHSCOPE_API_KEY
echo 3. 运行 start.bat 启动
echo.
pause
