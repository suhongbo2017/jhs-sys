@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set "APP_NAME=jhs-system"
set "SCRIPT_NAME=wsgi.py"
set "PORT=8080"
cd /d "%~dp0"

set "VENV_PY=%~dp0.venv\Scripts\python.exe"
set "VENV_PYW=%~dp0.venv\Scripts\pythonw.exe"
set "NPM_DIR=%APPDATA%\npm"

rem ============================================================
rem  启动前置检查：Node / npm / PM2 / 虚拟环境 / 端口
rem ============================================================
call :PREFLIGHT
if errorlevel 1 (
    echo.
    echo 环境检查未通过，请先处理上面的问题后重新打开本工具。
    pause
    exit /b 1
)

:MENU
cls
echo ==========================================
echo       金恒晟系统 - PM2 管理工具
echo ==========================================
echo   应用名称：%APP_NAME%      端口：%PORT%
echo   解释器  ：%VENV_PYW%
echo ------------------------------------------
echo  1. 启动服务 (Start)
echo  2. 停止服务 (Stop)
echo  3. 重启服务 (Restart)
echo  4. 查看状态 (Status)
echo  5. 查看实时日志 (Logs)
echo  6. 删除/关闭任务 (Delete)
echo  7. 保存开机自启 (Save)
echo  8. 环境检查与环境修复 (Check / Install)
echo  9. 退出 (Exit)
echo ==========================================
set "choice="
set /p choice=请输入数字选择操作:

if "%choice%"=="1" goto START
if "%choice%"=="2" goto STOP
if "%choice%"=="3" goto RESTART
if "%choice%"=="4" goto STATUS
if "%choice%"=="5" goto LOGS
if "%choice%"=="6" goto DELETE
if "%choice%"=="7" goto SAVE
if "%choice%"=="8" goto CHECK
if "%choice%"=="9" goto EXIT
goto MENU

:START
call "%PM2%" describe %APP_NAME% >nul 2>&1
if not errorlevel 1 (
    echo 检测到 %APP_NAME% 已在 PM2 中，改为执行重启...
    call "%PM2%" restart %APP_NAME% --update-env
    if errorlevel 1 (
        echo PM2 重启失败，请检查上面的错误信息。
        pause
        goto MENU
    )
    goto START_DONE
)
echo 正在启动服务...
call "%PM2%" start %SCRIPT_NAME% --name "%APP_NAME%" --interpreter "%VENV_PYW%" --update-env
if errorlevel 1 (
    echo PM2 启动失败，请检查上面的错误信息。
    echo 提示：若提示 Script already launched，请选择 3 重启，或选择 6 删除任务后重试。
    pause
    goto MENU
)
:START_DONE
call "%PM2%" save >nul 2>&1
echo.
echo 操作完成！可用选项 4 查看状态，选项 5 查看日志。
pause
goto MENU

:STOP
echo 正在停止服务...
call "%PM2%" stop %APP_NAME%
pause
goto MENU

:RESTART
echo 正在重启服务...
call "%PM2%" restart %APP_NAME% --update-env
pause
goto MENU

:STATUS
call "%PM2%" status %APP_NAME%
echo.
echo 端口状态：
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" || echo   端口 %PORT% 未在监听
pause
goto MENU

:LOGS
echo 正在打开实时日志 (按 Ctrl+C 退出日志查看)...
call "%PM2%" logs %APP_NAME%
goto MENU

:DELETE
echo [警告] 正在彻底删除/关闭任务...
call "%PM2%" delete %APP_NAME%
pause
goto MENU

:SAVE
call "%PM2%" save
echo 已保存当前进程列表以实现开机自启。
echo 提示：首次配置开机自启需管理员权限执行 pm2-startup（或 pm2 startup）后再 pm2 save。
pause
goto MENU

:CHECK
call :PREFLIGHT_FORCE
pause
goto MENU

:EXIT
call %PM2% save >nul 2>&1
exit /b 0


rem ============================================================
rem  子过程：前置检查（静默修复版，失败 return 1）
rem ============================================================
:PREFLIGHT
call :CHECK_NODE silent
if errorlevel 1 exit /b 1
call :CHECK_PM2 silent
if errorlevel 1 exit /b 1
call :CHECK_VENV silent
if errorlevel 1 exit /b 1
exit /b 0

rem 交互版（菜单选项 8）
:PREFLIGHT_FORCE
cls
echo ==========================================
echo       环境检查与环境修复
echo ==========================================
call :CHECK_NODE loud
if errorlevel 1 (
    echo [结论] Node.js 未就绪，无法继续。
    exit /b 1
)
call :CHECK_PM2 loud
if errorlevel 1 (
    echo [结论] PM2 未就绪，无法继续。
    exit /b 1
)
call :CHECK_VENV loud
if errorlevel 1 (
    echo [结论] 虚拟环境未就绪，无法继续。
    exit /b 1
)
call :CHECK_PORT loud
echo.
echo [结论] 环境检查全部通过。
exit /b 0

rem ---------- Node / npm ----------
:CHECK_NODE
set "NODE_OK=0"
where node >nul 2>&1 && set "NODE_OK=1"
where npm >nul 2>&1 && set "NPM_OK=1"
if "%NODE_OK%"=="1" if "%NPM_OK%"=="1" (
    for /f "delims=" %%v in ('node --version 2^>nul') do set "NODE_VER=%%v"
    echo [OK]  Node.js !NODE_VER! / npm 已安装
    exit /b 0
)
echo [缺失] 未检测到 Node.js 或 npm（PM2 依赖 Node.js）
echo        安装方式：访问 https://nodejs.org 下载 LTS 版本安装后重开本工具
echo        或使用包管理器：choco install nodejs-lts / scoop install nodejs-lts
exit /b 1

rem ---------- PM2 ----------
:CHECK_PM2
set "PM2="
for /f "delims=" %%i in ('where pm2 2^>nul') do if not defined PM2 set "PM2=%%i"
if not defined PM2 if exist "%NPM_DIR%\pm2.cmd" set "PM2=%NPM_DIR%\pm2.cmd"
if defined PM2 (
    for /f "delims=" %%v in ('call "%PM2%" --version 2^>nul ^| findstr /r "^[0-9]"') do set "PM2_VER=%%v"
    echo [OK]  PM2 !PM2_VER! 已安装
    exit /b 0
)
echo [缺失] 未检测到 PM2
set "ans="
set /p ans=是否现在安装 PM2？(Y/N):
if /i not "%ans%"=="Y" (
    echo        已跳过。PM2 为本工具的进程守护依赖，缺少它将无法启动服务。
    exit /b 1
)
echo 正在安装 PM2（npm install -g pm2）...
call npm install -g pm2
if errorlevel 1 (
    echo [失败] PM2 安装失败，请检查网络或 npm 权限后重试。
    exit /b 1
)
if exist "%NPM_DIR%\pm2.cmd" set "PM2=%NPM_DIR%\pm2.cmd"
if not defined PM2 (
    echo [失败] PM2 安装命令已执行，但仍未找到 pm2 可执行文件。
    exit /b 1
)
for /f "delims=" %%v in ('call "%PM2%" --version 2^>nul ^| findstr /r "^[0-9]"') do set "PM2_VER=%%v"
echo [OK]  PM2 !PM2_VER! 安装完成
exit /b 0

rem ---------- 虚拟环境 ----------
:CHECK_VENV
if exist "%VENV_PYW%" (
    echo [OK]  Python 虚拟环境已就绪
    exit /b 0
)
echo [缺失] 未找到 .venv 虚拟环境（%VENV_PYW%）
set "ans="
set /p ans=是否现在创建并安装依赖？(Y/N):
if /i not "%ans%"=="Y" (
    echo        已跳过。缺少虚拟环境将无法启动服务。
    exit /b 1
)
where uv >nul 2>&1
if errorlevel 1 (
    echo 正在使用 python 创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [失败] 创建虚拟环境失败，请确认已安装 Python 3.11+。
        exit /b 1
    )
    echo 正在安装依赖...
    call "%VENV_PY%" -m pip install -r requirements.txt
) else (
    echo 正在使用 uv 同步依赖...
    call uv sync
)
if not exist "%VENV_PYW%" (
    echo [失败] 虚拟环境仍不可用。
    exit /b 1
)
echo [OK]  虚拟环境准备完成
exit /b 0

rem ---------- 端口占用 ----------
:CHECK_PORT
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [OK]  端口 %PORT% 空闲
    exit /b 0
)
if defined PM2 (
    call "%PM2%" describe %APP_NAME% >nul 2>&1
    if not errorlevel 1 (
        echo [提示] 端口 %PORT% 已被 %APP_NAME% 占用（本工具已管理的进程）
        exit /b 0
    )
)
echo [警告] 端口 %PORT% 被其他进程占用：
netstat -ano | findstr /r /c:":%PORT% .*LISTENING"
echo        可先结束占用进程：taskkill /PID ^<PID^> /F
exit /b 0
