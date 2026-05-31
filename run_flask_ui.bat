@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe sleep_detector.py
) else (
  echo Virtual environment not found. Please create it and install dependencies.
  pause
)
