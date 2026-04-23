@echo off
REM ---------------------------------------------------------------------------
REM Promote dev -> main.
REM
REM Run this ONLY after you've tested dev locally against a real client and
REM the output looks correct. This is the step that puts code into production.
REM ---------------------------------------------------------------------------

setlocal

echo.
echo === Promoting dev -^> main ===
echo.

REM Make sure we have the latest of everything
git fetch origin || goto :fail

REM Switch to dev, make sure it's current
git checkout dev || goto :fail
git pull origin dev || goto :fail

REM Switch to main, make sure it's current
git checkout main || goto :fail
git pull origin main || goto :fail

REM Merge dev into main. --no-ff forces a merge commit so the history
REM clearly shows "this is where we promoted".
git merge --no-ff dev -m "promote: dev -> main" || goto :fail

REM Push to GitHub
git push origin main || goto :fail

echo.
echo === Promotion complete ===
echo main is now at:
git log -1 --oneline
echo.

endlocal
exit /b 0

:fail
echo.
echo === Promotion FAILED ===
echo The last git command returned an error. Nothing was pushed.
echo Check the output above, fix the problem, and re-run promote.bat.
echo.
endlocal
exit /b 1
