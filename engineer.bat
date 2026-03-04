@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\mrleo\Downloads\autonomous-engineer"
python engineer.py %*
