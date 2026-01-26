# ============================================
# DPL Docker Run Script (Windows PowerShell)
# ============================================

param(
    [Parameter(Position=0)]
    [string]$Command,
    
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
Set-Location $ProjectDir

Write-Host "=== DPL: Political Rhetoric Analyzer ===" -ForegroundColor Green

# Проверяем наличие .env
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from env.example..." -ForegroundColor Yellow
    Copy-Item "env.example" ".env"
}

# Проверяем наличие модели Whisper
if (-not (Test-Path "models\whisper\config.json")) {
    Write-Host "Warning: Whisper model not found in models\whisper\" -ForegroundColor Red
    Write-Host "Please clone the model first:" -ForegroundColor Yellow
    Write-Host "  cd models\whisper"
    Write-Host "  git lfs install"
    Write-Host "  git clone https://huggingface.co/openai/whisper-large-v3 ."
    Write-Host ""
}

# Показываем помощь если нет аргументов
if (-not $Command) {
    Write-Host @"
Usage: .\docker-run.ps1 <command> [args]

Commands:
  analyze -p <politician>   Full pipeline: search -> download -> transcribe -> analyze
  legacy -t <transcript>    Analyze existing transcript
  visualize -r <results>    Visualize existing results
  shell                     Open shell in container
  build                     Build Docker image
  build-gpu                 Build GPU Docker image

Examples:
  .\docker-run.ps1 analyze -p "Donald Trump"
  .\docker-run.ps1 legacy -t data/transcripts/speech.txt
  .\docker-run.ps1 shell
"@
    exit 0
}

$ArgsString = $Args -join " "

switch ($Command) {
    "build" {
        Write-Host "Building Docker image (CPU)..." -ForegroundColor Green
        docker-compose build dpl
    }
    "build-gpu" {
        Write-Host "Building Docker image (GPU)..." -ForegroundColor Green
        docker-compose --profile gpu build dpl-gpu
    }
    "shell" {
        Write-Host "Opening shell in container..." -ForegroundColor Green
        docker-compose run --rm dpl /bin/bash
    }
    { $_ -in "analyze", "legacy", "visualize" } {
        Write-Host "Running: $Command $ArgsString" -ForegroundColor Green
        docker-compose run --rm dpl $Command $Args
    }
    default {
        Write-Host "Running custom command: $Command $ArgsString" -ForegroundColor Green
        docker-compose run --rm dpl $Command $Args
    }
}
