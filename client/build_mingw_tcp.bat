@echo off
echo MinGW TCP Client Build
echo ======================

REM Check for MinGW
where g++ >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo MinGW g++ not found in PATH
    echo Please install MinGW or add it to PATH
    pause
    exit /b 1
)

REM Check for vcpkg
set VCPKG_ROOT=C:\vcpkg
if not exist "%VCPKG_ROOT%" (
    echo vcpkg not found at %VCPKG_ROOT%
    pause
    exit /b 1
)

echo.
echo Building TCP Client with MinGW...
echo Using: 
g++ --version | findstr "g++"

echo.
echo Compiling...
g++ -std=c++17 -O2 ^
    -I"%VCPKG_ROOT%\installed\x64-windows\include" ^
    -DWIN32_LEAN_AND_MEAN ^
    -DBOOST_ALL_NO_LIB ^
    AESWrapper.cpp RSAWrapper.cpp Base64Wrapper.cpp cksum.cpp ^
    tcp_client.cpp tcp_client_file_ops.cpp main.cpp ^
    -o tcp_client_mingw.exe ^
    -L"%VCPKG_ROOT%\installed\x64-windows\lib" ^
    -lcryptopp -lws2_32 -static-libgcc -static-libstdc++

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo MinGW build failed!
    echo This might be due to Crypto++ compatibility issues.
    echo.
    echo Alternative: Try building with a different Crypto++ version
    echo or use the Python client for testing.
    pause
    exit /b 1
)

echo.
echo ✓ TCP Client built successfully with MinGW!
echo   Output: tcp_client_mingw.exe
echo.
echo Testing basic functionality...
if exist "tcp_client_mingw.exe" (
    echo ✓ Executable created
    echo.
    echo Ready for integration testing!
    echo.
    echo Next steps:
    echo 1. Start Python TCP server: cd ..\server && python tcp_server.py
    echo 2. Run TCP client: tcp_client_mingw.exe
) else (
    echo ✗ Executable not found
)
