#!/bin/bash
# AI虚拟软件公司 - 启动脚本
# ==========================

set -e

echo "=========================================="
echo "🚀 AI虚拟软件公司 - 启动脚本"
echo "=========================================="

# 检查Python版本
echo "📋 检查环境..."
python3 --version || { echo "❌ 需要Python 3.9+"; exit 1; }

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 检查依赖安装
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "❌ 依赖安装失败，请检查网络连接"
    exit 1
fi

echo "✅ 依赖安装完成"

# 启动服务
echo ""
echo "=========================================="
echo "🎯 启动服务"
echo "=========================================="
echo "📡 Web界面: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🔌 WebSocket: ws://localhost:8000/ws"
echo "👔 老板WebSocket: ws://localhost:8000/ws/boss"
echo "=========================================="
echo ""

# 启动服务器
python3 main.py --host 0.0.0.0 --port 8000
