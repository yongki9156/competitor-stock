@echo off
cd /d "%~dp0"

echo Opening product pages from list...
for /f "usebackq delims=" %%u in ("products.txt") do (
  start "" "chrome.exe" "%%u"
  timeout /t 2 /nobreak >nul
)

echo Syncing product list to GitHub...
git add -A
git commit -m "update product list"
git pull origin main --no-rebase --no-edit
git push

echo Done.
pause
