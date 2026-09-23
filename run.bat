@echo off
echo ==========================================
echo COMICCRAFT Startup Script
echo ==========================================

if not exist env\ (
    echo Creating virtual environment...
    python -m venv env
)

echo Activating virtual environment...
call env\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip --quiet

echo Installing requirements...
pip install -r requirements.txt --quiet

echo.
echo Starting FastAPI server on http://127.0.0.1:8000
echo Press CTRL+C to stop the server.
echo.
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

echo.
echo Server stopped.
pause
