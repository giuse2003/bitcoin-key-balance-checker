@echo off
cd /d "%~dp0"
title Verifica saldi Bitcoin tramite API
python bitcoin_api_bridge.py
echo.
echo Il servizio API locale si e arrestato.
pause
