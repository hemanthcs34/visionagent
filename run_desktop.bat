@echo off
echo Starting CogniSync Desktop Agent Mode...
echo Installing required dependencies if missing (PyQt6)...
cd backend
call venv\Scripts\activate
pip install PyQt6 PyQt6-WebEngine
cd ..
echo Launching the desktop wrapper...
python desktop_app.py
pause
