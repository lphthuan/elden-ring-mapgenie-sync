@echo off
title Elden Ring to MapGenie Sync Tool
cd /d "%~dp0"
echo ========================================================
echo   KHOI DONG CONG CU DONG BO ELDEN RING -> MAPGENIE (FMG)
echo ========================================================
echo Dang khoi dong may chu giao dien Web...
python elden_ring_fmg_sync.py --web --port 8088
pause
