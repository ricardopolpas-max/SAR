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

cd backend
python servidor.py

echo.
echo  Servidor encerrado.
pause
