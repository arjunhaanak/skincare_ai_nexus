@echo off
echo Starting Skincare AI Nexus - Professional Edition...
echo.

:: Check for virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. 
    echo Please run the following command first:
    echo python -m venv venv
    pause
    exit /b
)

:: Activate and Run
echo [1/2] Activating Clinical Environment...
call venv\Scripts\activate

echo [2/2] Launching Neural Pipeline...
echo Access the portal at http://localhost:5001
echo.
python app.py

pause
