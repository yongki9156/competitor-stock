@echo off
rem Hourly auto check - opens product pages with #autotrack
rem Tampermonkey script uploads stock and closes each tab by itself
cd /d "%~dp0"
for /f "usebackq delims=" %%u in ("products.txt") do (
  start "" "chrome.exe" "%%u#autotrack"
  timeout /t 6 /nobreak >nul
)
exit
