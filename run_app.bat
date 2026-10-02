@echo off
title DMart Smart Retail Analytics & Demand Forecasting Suite
echo =====================================================================
echo  DMart Smart Retail Sales Analysis ^& Demand Forecasting Suite
echo  Cornerstone Project - Data Analysis Essentials (DAE)
echo =====================================================================
echo.
echo Starting Web Application Server on http://127.0.0.1:8000 ...
echo.

python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
