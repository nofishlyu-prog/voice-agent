#!/bin/bash

echo "========================================"
echo " Voice Agent - 启动菜单"
echo "========================================"
echo

# 检查虚拟环境
if [ ! -f ".venv/bin/activate" ]; then
    echo "[错误] 虚拟环境不存在，请先运行 ./install.sh"
    exit 1
fi

echo "激活虚拟环境..."
source .venv/bin/activate

echo
echo "请选择运行模式："
echo
echo "  [1] 文本对话模式 (chat_demo)"
echo "  [2] 语音对话模式 (voice_demo) - 需要麦克风"
echo "  [3] 测试脚本 (test_agent)"
echo "  [4] 音频输入测试 (test_audio_input)"
echo "  [0] 退出"
echo
read -p "请输入选项 (0-4): " choice

echo
case $choice in
    1)
        echo "启动文本对话模式..."
        python examples/chat_demo.py
        ;;
    2)
        echo "启动语音对话模式..."
        python examples/voice_demo.py
        ;;
    3)
        echo "运行测试脚本..."
        python tests/test_agent.py
        ;;
    4)
        echo "运行音频输入测试..."
        python tests/test_audio_input.py
        ;;
    0)
        echo "退出"
        exit 0
        ;;
    *)
        echo "[错误] 无效选项"
        exit 1
        ;;
esac

echo
