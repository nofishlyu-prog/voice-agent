@echo off
echo ========================================
echo  Voice Agent - 启动菜单
echo ========================================
echo.

REM 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)

echo 激活虚拟环境...
call .venv\Scripts\activate

echo.
echo 请选择运行模式：
echo.
echo  [1] 文本对话模式 (chat_demo)
echo  [2] 语音对话模式 (voice_demo) - 需要麦克风
echo  [3] 测试脚本 (test_agent)
echo  [4] 音频输入测试 (test_audio_input)
echo  [0] 退出
echo.
set /p choice="请输入选项 (0-4): "

if "%choice%"=="1" (
    echo.
    echo 启动文本对话模式...
    python examples\chat_demo.py
) else if "%choice%"=="2" (
    echo.
    echo 启动语音对话模式...
    python examples\voice_demo.py
) else if "%choice%"=="3" (
    echo.
    echo 运行测试脚本...
    python tests\test_agent.py
) else if "%choice%"=="4" (
    echo.
    echo 运行音频输入测试...
    python tests\test_audio_input.py
) else if "%choice%"=="0" (
    echo.
    echo 退出
    exit /b 0
) else (
    echo.
    echo [错误] 无效选项
)

echo.
pause
