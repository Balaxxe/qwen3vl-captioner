@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Add the newest installed CUDA Toolkit to PATH for DLL loading
REM (prevents ggml.dll / access violation errors). Numeric sort so
REM v12.10 beats v12.4 and v13.x beats both.
set "CUDA_BIN="
for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "$root='C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA'; if (Test-Path $root) { Get-ChildItem $root -Directory | Where-Object { $_.Name -match '^v(\d+)\.(\d+)$' } | Sort-Object { [version]($_.Name.TrimStart('v')) } -Descending | Select-Object -First 1 -ExpandProperty Name }"`) do (
    set "CUDA_BIN=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\%%D\bin"
)
if defined CUDA_BIN (
    set "PATH=!CUDA_BIN!;%PATH%"
) else if defined CUDA_PATH (
    set "PATH=%CUDA_PATH%\bin;%PATH%"
) else (
    echo [WARNING] CUDA Toolkit not found - GPU acceleration will not work.
    echo           Install it with:  winget install Nvidia.CUDA
    echo           then re-run setup.bat to install the matching wheel.
    echo.
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo         Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Qwen3-VL Captioner...
.venv\Scripts\python.exe app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with an error.
    echo         Run diagnose.bat for a full report of what's wrong,
    echo         and include its output if you open a GitHub issue.
    pause
)
