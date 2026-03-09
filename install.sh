#!/bin/bash

echo "========================================"
echo " Voice Agent - Mac/Linux 安装脚本"
echo "========================================"
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.8+"
    echo "Mac: brew install python"
    echo "Ubuntu: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

echo "[1/4] 创建虚拟环境..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "[错误] 创建虚拟环境失败"
    exit 1
fi

echo "[2/4] 激活虚拟环境..."
source .venv/bin/activate

echo "[3/4] 升级 pip..."
pip install --upgrade pip --quiet

echo "[4/4] 安装依赖..."
pip install -r requirements.txt --quiet

echo
echo "========================================"
echo " 安装完成！"
echo "========================================"
echo
echo "下一步："
echo 1. 复制 .env.example 为 .env
echo 2. 编辑 .env 填入你的 DASHSCOPE_API_KEY
echo 3. 运行 ./start.sh 启动
echo
