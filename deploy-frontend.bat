@echo off
chcp 65001 >nul
title VerinX 前端构建 + Vercel 部署

echo ============================================
echo   VerinX 前端构建 + Vercel 部署
echo ============================================
echo.

cd /d "%~dp0frontend"

REM 检查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 18+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

REM 安装依赖
if not exist "node_modules" (
    echo [1/3] 安装前端依赖...
    call npm install
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [1/3] 依赖已安装，跳过
)

REM 构建
echo [2/3] 构建前端...
call npm run build
if %errorlevel% neq 0 (
    echo [错误] 构建失败
    pause
    exit /b 1
)
echo [完成] 构建成功，输出在 dist\ 目录

REM 检查 Vercel CLI
where vercel >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 首次使用，安装 Vercel CLI...
    call npm install -g vercel
)

echo.
echo [3/3] 部署到 Vercel...
echo.
echo ============================================
echo   部署说明：
echo   1. 首次部署会要求你登录 Vercel
echo   2. 登录后选择 "Deploy"
echo   3. Framework Preset 选 Vite
echo   4. Build Command: npm run build
echo   5. Output Directory: dist
echo   6. Environment Variables 添加:
echo      Name: VITE_API_BASE_URL
echo      Value: https://你的ngrok地址/api
echo ============================================
echo.
echo 准备就绪，即将打开 Vercel 部署...
echo.
pause

call vercel --prod

echo.
echo ============================================
echo   部署完成！
echo   你的前端地址显示在上方
echo ============================================
pause
