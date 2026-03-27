@echo off
chcp 65001 > nul
title 合同审查风险Agent

echo ========================================
echo     合同审查风险Agent
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查依赖...
python -c "import fastapi, uvicorn, langchain" 2>nul
if errorlevel 1 (
    echo 依赖未安装，正在安装...
    pip install -r requirements.txt -q
)

echo [2/3] 启动服务...
echo.
echo 服务启动后，请访问: http://localhost:8000
echo 按 Ctrl+C 停止服务
echo.

python main.py
