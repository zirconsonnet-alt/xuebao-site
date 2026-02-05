@echo off
setlocal

echo [1/2] Push to gitee...
git push gitee main
if errorlevel 1 (
  echo ERROR: push to gitee failed. Stop.
  exit /b 1
)

echo [2/2] Push to github...
git push github main
if errorlevel 1 (
  echo WARN: push to github failed (network issue). You can retry later.
  exit /b 0
)

echo OK: pushed to both.
endlocal
