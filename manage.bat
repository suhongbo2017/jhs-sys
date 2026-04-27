@echo off
setlocal enabledelayedexpansion

:: 设置项目信息
set APP_NAME=jhs-system
set SCRIPT_NAME=wsgi.py
set INTERPRETER=.\.venv\Scripts\python.exe

:MENU
cls
echo ==========================================
echo       金恒晟系统 - PM2 管理工具
echo ==========================================
echo  1. 启动服务 (Start)
echo  2. 停止服务 (Stop)
echo  3. 重启服务 (Restart)
echo  4. 查看状态 (Status)
echo  5. 查看实时日志 (Logs)
echo  6. 清理并保存状态 (Save)
echo  7. 退出 (Exit)
echo ==========================================
set /p choice=请输入数字选择操作: 

if "%choice%"=="1" goto START
if "%choice%"=="2" goto STOP
if "%choice%"=="3" goto RESTART
if "%choice%"=="4" goto STATUS
if "%choice%"=="5" goto LOGS
if "%choice%"=="6" goto SAVE
if "%choice%"=="7" goto EXIT
goto MENU

:START
echo 正在启动服务...
pm2 start %SCRIPT_NAME% --name "%APP_NAME%" --interpreter "%INTERPRETER%"
pause
goto MENU

:STOP
echo 正在停止服务...
pm2 stop %APP_NAME%
pause
goto MENU

:RESTART
echo 正在重启服务...
pm2 restart %APP_NAME%
pause
goto MENU

:STATUS
pm2 status %APP_NAME%
pause
goto MENU

:LOGS
echo 正在打开实时日志 (按 Ctrl+C 退出日志查看)...
pm2 logs %APP_NAME%
goto MENU

:SAVE
echo 正在保存当前列表以实现开机自启...
pm2 save
pause
goto MENU

:EXIT
exit
