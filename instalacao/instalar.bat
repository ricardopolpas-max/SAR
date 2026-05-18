@echo off
title Instalador SAR

echo.
echo  ================================================
echo   Sistema de Automacao de Recolocacao - SAR
echo   Instalando, aguarde...
echo  ================================================
echo.

:: Cria pasta de dados do SAR em AppData
if not exist "%APPDATA%\SAR" mkdir "%APPDATA%\SAR"

:: Copia instalacao.dat para AppData\SAR
copy /Y "%~dp0instalacao.dat" "%APPDATA%\SAR\instalacao.dat" >nul

:: Copia o executavel para AppData\SAR
copy /Y "%~dp0SAR.exe" "%APPDATA%\SAR\SAR.exe" >nul

:: Cria atalho na area de trabalho via PowerShell
powershell -NoProfile -Command ^
  "$s=(New-Object -COM WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\SAR.lnk');$s.TargetPath='%APPDATA%\SAR\SAR.exe';$s.WorkingDirectory='%APPDATA%\SAR';$s.Description='Sistema de Automacao de Recolocacao';$s.Save()"

echo.
echo  Instalacao concluida com sucesso!
echo  Um atalho foi criado na sua area de trabalho.
echo.
pause
