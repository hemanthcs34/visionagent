@echo off
echo === CogniSync Backend Setup ===
echo.

echo [1/4] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/4] Installing core API packages...
python -m pip install --only-binary :all: ^
  fastapi==0.109.2 ^
  uvicorn==0.27.1 ^
  python-dotenv==1.0.1 ^
  pydantic==2.6.1

echo.
echo [3/4] Installing AI/vision packages...
python -m pip install --only-binary :all: ^
  "numpy>=1.26.4" ^
  "Pillow>=10.2.0" ^
  "opencv-python-headless>=4.9.0.80" ^
  "mediapipe>=0.10.30" ^
  "httpx>=0.26.0" ^
  "openai>=1.12.0"

echo.
echo [4/4] Done! All packages installed.
echo.
echo Run the server with: python main.py
pause
