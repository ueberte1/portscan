@echo off
title Iniciando PortScan Pro...
cd /d "%~dp0"

REM Verifica se python está disponível no PATH ou no caminho padrão
where python >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw gui_port_scanner.py
    exit
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" gui_port_scanner.py
    exit
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" gui_port_scanner.py
    exit
)

echo Python nao foi encontrado automaticamente.
echo Por favor, instale o Python ou certifique-se de que ele esta no PATH.
pause
