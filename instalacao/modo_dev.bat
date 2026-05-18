@echo off
title SAR - Modo Desenvolvimento

echo.
echo  ================================================
echo   Sistema de Automacao de Recolocacao - SAR
echo   Ativando modo desenvolvimento...
echo  ================================================
echo.

if exist "%APPDATA%\SAR\instalacao.dat" (
    del "%APPDATA%\SAR\instalacao.dat"
    echo  Modo desenvolvimento ativado.
    echo  O servidor usara o .env local do projeto.
) else (
    echo  Nenhuma configuracao de producao encontrada.
    echo  O servidor ja esta em modo desenvolvimento.
)

echo.
pause
