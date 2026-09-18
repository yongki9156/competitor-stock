@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo Opening product pages from list...
for /f "usebackq delims=" %%u in ("products.txt") do (
  start "" "chrome.exe" "%%u"
  timeout /t 2 /nobreak >nul
)

echo Waiting for background sync to finish...
timeout /t 20 /nobreak >nul

echo Syncing product list to GitHub...
git add -A
git commit -m "update product list"

set RETRY=0
:PUSHLOOP
git pull origin main --no-rebase --no-edit
git push
if !ERRORLEVEL! NEQ 0 (
  set /a RETRY+=1
  if !RETRY! LSS 5 (
    echo Push conflict, retrying in 5 seconds... attempt !RETRY!
    timeout /t 5 /nobreak >nul
    goto PUSHLOOP
  ) else (
    echo Push failed after several attempts. Run this file again later.
  )
) else (
  echo Sync successful.
)

echo Done.
pause
