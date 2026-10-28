@echo off
echo ============================================================
echo   Pushing Wind Tunnel Calculator to GitHub
echo   Repository: https://github.com/restin-arch/High-Speed-Wind-Tunnel-Calculator
echo ============================================================
echo.
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ============================================================
    echo   SUCCESS! Uploaded to GitHub.
    echo   View online: https://github.com/restin-arch/High-Speed-Wind-Tunnel-Calculator
    echo ============================================================
) else (
    echo.
    echo Push encountered an error or needs authentication.
)
pause
