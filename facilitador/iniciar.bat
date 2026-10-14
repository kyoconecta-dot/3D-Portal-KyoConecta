@echo off
REM Facilitador da impressora 3D: atualiza o repo e abre http://localhost:8000
cd /d "%~dp0.."
git pull --ff-only || echo AVISO: git pull falhou, seguindo com a versao local
where py >nul 2>nul
if %errorlevel%==0 (py -3 -m facilitador.app) else (python -m facilitador.app)
pause
