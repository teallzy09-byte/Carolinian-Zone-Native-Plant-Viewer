@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where py >nul 2>nul && (py -3 -m streamlit run streamlit_app.py & exit /b)
where python >nul 2>nul && (python -m streamlit run streamlit_app.py & exit /b)
echo ERROR: Python was not found.
pause
