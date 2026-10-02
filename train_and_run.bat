@echo off
title Train ^& Launch DMart AI Suite
echo =====================================================================
echo  Step 1: Training Models ^& Generating Serialized Artifacts (.pkl)
echo =====================================================================
python train_model.py
echo.
echo =====================================================================
echo  Step 2: Starting Web Application on http://127.0.0.1:8000
echo =====================================================================
python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
