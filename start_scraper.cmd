@echo off
title scrape-llm Launcher
echo ================================================
echo   scrape-llm - Text + Image Scraper with LLM
echo ================================================

REM Ensure venv exists
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

REM Install/upgrade pip + requirements
echo [INFO] Installing/Updating dependencies...
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

REM Launch Streamlit UI
echo [INFO] Starting web UI...
start "" http://localhost:8501
.\.venv\Scripts\python.exe -m streamlit run app.py
