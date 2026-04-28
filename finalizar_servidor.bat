@echo off
title SAR — Finalizar Servidor
cd /d "%~dp0"

echo.
echo  =============================================
echo   SAR - Finalizando Servidor
echo  =============================================
echo.

if not exist "sar.pid" (
    echo  Nenhuma instancia ativa encontrada.
    echo  O servidor pode ja estar encerrado.
    echo.
    pause
    exit /b 0
)

set /p PID=<sar.pid
echo  Encerrando processo PID %PID%...

taskkill /PID %PID% /F >nul 2>&1

if exist "sar.pid" del "sar.pid"

echo  Servidor finalizado com sucesso.
echo.
pause
