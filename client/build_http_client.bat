@echo off
REM Simple build script for HTTP-based client (no CMake required)
REM This builds the current working HTTP client

echo Building HTTP-based backup client...
echo.

REM Check if we're in the client directory
if not exist "client.cpp" (
    echo Error: client.cpp not found. Make sure you're in the client directory.
    pause
    exit /b 1
)

REM Try to compile with g++ (MinGW)
echo Attempting to build with g++ (MinGW)...
g++ -std=c++17 client.cpp -o http_client.exe -lcurl 2>nul

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ Build successful! Created http_client.exe
    echo.
    echo Usage: http_client.exe ^<server_url^> ^<username^> ^<password^> ^<file_path^>
    echo Example: http_client.exe http://localhost:8080 user password test.txt
    echo.
    goto :end
)

REM Try with Visual Studio compiler
echo g++ not found or failed. Trying with Visual Studio compiler...
cl /std:c++17 client.cpp /Fe:http_client.exe 2>nul

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ Build successful with Visual Studio! Created http_client.exe
    echo.
    goto :end
)

REM Both failed
echo.
echo ✗ Build failed. Possible issues:
echo   1. libcurl not installed or not in PATH
echo   2. No C++ compiler found (need MinGW g++ or Visual Studio)
echo   3. Missing development headers
echo.
echo For MinGW: Install from https://www.mingw-w64.org/
echo For libcurl: Download from https://curl.se/windows/
echo.
echo Alternative: Use the Python clients instead (no compilation needed)
echo.

:end
pause
