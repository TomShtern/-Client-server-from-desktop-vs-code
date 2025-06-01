@echo off
echo This script tests the enhanced backup features

REM Start the enhanced server in a new window
start cmd /c "cd /d %~dp0 && start_enhanced_server.bat"

REM Wait for server to start
timeout /t 3 /nobreak > nul

REM Create test file if it doesn't exist
if not exist large_test_file.bin (
  echo Creating large test file (10MB)...
  python -c "with open('large_test_file.bin', 'wb') as f: f.write(b'0' * 10 * 1024 * 1024)"
)

REM Upload with resumable upload
echo.
echo Testing resumable upload with enhanced client...
python client\enhanced_client.py http://localhost:8080 user password large_test_file.bin --resumable

REM Test file browser
echo.
echo Opening file browser in web browser...
start "" http://localhost:8080/files

echo.
echo Tests completed! The enhanced server is still running.
echo Press Ctrl+C in the server window to stop it when done.
