@echo off
chcp 65001 >nul
title VerinX 一键部署（Vercel + ngrok）

echo ============================================
echo   VerinX 一键部署
echo   前端: Vercel（云）
echo   后端: ngrok 隧道（本地）
echo   电脑关机后 ngrok 地址会变
echo ============================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM ========== 步骤 1: 启动后端 + ngrok ==========
echo [步骤 1] 启动后端服务和 ngrok 隧道...
echo.

if not exist "backend\venv\Scripts\python.exe" (
    echo [首次运行] 创建 Python 虚拟环境...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements-deploy.txt
    cd ..
)

REM 启动后端
cd backend
start "VerinX-Backend" /min cmd /c "venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
cd ..

timeout /t 3 /nobreak >nul

REM 启动 ngrok
if not exist "ngrok\ngrok.exe" (
    echo [首次运行] 下载 ngrok...
    mkdir ngrok 2>nul
    echo 请手动下载 ngrok: https://ngrok.com/download
    echo 解压后将 ngrok.exe 放到 ngrok\ 目录
    echo.
    echo 下载地址: https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip
    pause
)

start "ngrok" cmd /c "ngrok http 8000"

echo.
echo ============================================
echo   后端已启动！
echo   本地地址: http://localhost:8000
echo   ngrok 地址: 请查看 ngrok 窗口
echo ============================================
echo.
pause

REM ========== 步骤 2: 获取 ngrok 地址 ==========
echo.
echo [步骤 2] 获取 ngrok 公网地址...
echo.

REM 从 ngrok API 获取地址
set NGROK_URL=
for /f "delims=" %%a in ('curl -s http://localhost:4040/api/tunnels ^| findstr "public_url"') do (
    for /f "tokens=2 delims=:," %%b in ("%%a") do (
        set "NGROK_URL=%%b"
    )
)

if "%NGROK_URL%"=="" (
    echo [提示] 无法自动获取 ngrok 地址
    echo [提示] 请手动复制 ngrok 窗口中的 "Forwarding" 地址
    echo.
    set /p NGROK_URL=请输入 ngrok 地址（如 https://xxxx.ngrok-free.app）: 
)

echo.
echo 你的 ngrok 地址: %NGROK_URL%
echo.

REM ========== 步骤 3: 构建前端 ==========
echo [步骤 3] 构建前端...
cd frontend

if not exist "node_modules" (
    call npm install
)

REM 更新环境变量
echo VITE_API_BASE_URL=%NGROK_URL%/api > .env.production

call npm run build

if %errorlevel% neq 0 (
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo.
echo [完成] 前端构建成功

REM ========== 步骤 4: 部署到 Vercel ==========
echo.
echo [步骤 4] 部署到 Vercel...
echo.

where vercel >nul 2>&1
if %errorlevel% neq 0 (
    echo [首次运行] 安装 Vercel CLI...
    call npm install -g vercel
)

echo ============================================
echo   Vercel 部署配置：
echo   - Project: verinx
echo   - Framework: Vite
echo   - Build Command: npm run build
echo   - Output: dist
echo   - Environment Variable:
echo     Name: VITE_API_BASE_URL
echo     Value: %NGROK_URL%/api
echo ============================================
echo.
echo 即将打开 Vercel 部署窗口，请按提示操作...
echo.
pause

call vercel --prod

echo.
echo ============================================
echo   部署完成！
echo.
echo   前端地址: 查看 Vercel 输出
echo   后端地址: %NGROK_URL%
echo.
echo   分享前端地址给朋友即可使用
echo   注意：电脑关机后 ngrok 地址会变，需要重新部署
echo ============================================
pause
