@echo off
setlocal
echo =======================================================
echo PocketSmart AI - One-Click GitHub Push
echo =======================================================
echo.

set "GIT_EXE=%LOCALAPPDATA%\MinGit\cmd\git.exe"

if not exist "%GIT_EXE%" (
    echo Git executable not found at %GIT_EXE%
    pause
    exit /b 1
)

echo [1/4] Checking local Git status...
"%GIT_EXE%" status

echo.
echo [2/4] Verifying remote origin...
"%GIT_EXE%" remote -v

echo.
echo [3/4] Ready to push to GitHub!
echo A browser window or login prompt will appear to authenticate your account.
echo.
pause

echo [4/4] Uploading all project files to main branch...
"%GIT_EXE%" push -u origin main

echo.
echo =======================================================
echo Push completed! Check your repository on GitHub.
echo =======================================================
pause
