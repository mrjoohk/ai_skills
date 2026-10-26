@echo off
rem office-drm-bridge 워커 기동. 사용자가 직접 켜고 닫는다.
rem   run_bridge_worker.bat            자동 모드(수락된 계획의 요청을 바로 실행)
rem   run_bridge_worker.bat --confirm  요청마다 y/N 확인
chcp 65001 >nul
cd /d "%~dp0..\..\..\.."
python ".claude\skills\office-drm-bridge\scripts\bridge_worker.py" %*
pause
