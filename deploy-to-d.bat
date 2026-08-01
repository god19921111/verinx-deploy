@echo off
chcp 65001 >nul
title VerinX 部署到D盘

echo ============================================
echo   VerinX 部署到 D:\VerinX-Deploy
echo ============================================
echo.

REM 获取当前项目根目录
set "SOURCE=%~dp0"
set "TARGET=D:\VerinX-Deploy"

echo 源目录: %SOURCE%
echo 目标目录: %TARGET%
echo.

REM 创建目标目录
if not exist "%TARGET%" mkdir "%TARGET%"
if not exist "%TARGET%\backend" mkdir "%TARGET%\backend"
if not exist "%TARGET%\frontend" mkdir "%TARGET%\frontend"
if not exist "%TARGET%\ngrok" mkdir "%TARGET%\ngrok"

REM 复制后端
echo [1/4] 复制后端文件...
robocopy "%SOURCE%backend" "%TARGET%\backend" /E /MIR /XD venv __pycache__ .git node_modules >nul 2>&1
echo       后端复制完成

REM 复制前端
echo [2/4] 复制前端文件...
robocopy "%SOURCE%frontend" "%TARGET%\frontend" /E /MIR /XD node_modules dist .git >nul 2>&1
echo       前端复制完成

REM 复制脚本
echo [3/4] 复制部署脚本...
copy "%SOURCE%start-backend.bat" "%TARGET%\" >nul 2>&1
copy "%SOURCE%stop-all.bat" "%TARGET%\" >nul 2>&1
copy "%SOURCE%deploy-frontend.bat" "%TARGET%\" >nul 2>&1
copy "%SOURCE%deploy-all.bat" "%TARGET%\" >nul 2>&1
echo       脚本复制完成

REM 安装后端依赖
echo [4/4] 安装后端依赖...
cd /d "%TARGET%\backend"
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements-deploy.txt
cd /d "%TARGET%"

echo.
echo ============================================
echo   部署完成！
echo.
echo   D:\VerinX-Deploy 目录结构:
echo     ├── backend\        后端代码
echo     ├── frontend\       前端代码
echo     ├── ngrok\          ngrok 工具（需手动放入）
echo     ├── start-backend.bat    启动后端+ngrok
echo     ├── stop-all.bat         停止所有服务
echo     ├── deploy-frontend.bat  部署前端到Vercel
echo     └── deploy-all.bat       一键全流程
echo.
echo   下一步:
echo   1. 下载 ngrok: https://ngrok.com/download
echo   2. 将 ngrok.exe 放到 D:\VerinX-Deploy\ngrok\
echo   3. 双击 start-backend.bat 启动
echo   4. 运行 deploy-frontend.bat 部署前端
echo ============================================
echo.
pause
