@echo off
title SAR — Servidor
cd /d "%~dp0"

echo.
echo  =============================================
echo   SAR - Sistema de Automacao de Recolocacao
echo  =============================================
echo.
echo  Iniciando servidor...
echo  Acesse: https://127.0.0.1:8000/sar
echo.

start /min "" cmd /c "timeout /t 4 /nobreak > nul & start https://127.0.0.1:8000/sar"

cd backend
python servidor.py

echo.
echo  Servidor encerrado.
pause
