#!/usr/bin/env powershell
$ErrorActionPreference = "Stop"

Write-Host "Starting CoaiHome AI Dropshipping System..." -ForegroundColor Green
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Prevent Unicode console crashes and .pyc noise on Windows.
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

$python = ".\venv\Scripts\python.exe"

Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

Write-Host "Installing Playwright Chromium browser..." -ForegroundColor Yellow
& $python -m playwright install chromium

Write-Host "Launching API on http://localhost:8000 ..." -ForegroundColor Green
& $python main.py
