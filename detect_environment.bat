@echo off
echo ===============================================
echo    BUILD ENVIRONMENT DETECTION FOR VS CODE
echo ===============================================
echo.

REM Check for Visual Studio Build Tools
echo [1/5] Checking Visual Studio Build Tools...
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Visual Studio Build Tools 2019 found
    where cl >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ cl.exe compiler available
        cl 2>&1 | findstr "Version" | head -1
    ) else (
        echo   ✗ cl.exe compiler not in PATH
    )
) else (
    echo   ✗ Visual Studio Build Tools 2019 not found
    echo     Try: C:\Program Files\Microsoft Visual Studio\2022\BuildTools\...
)
echo.

REM Check for MinGW
echo [2/5] Checking MinGW/MSYS2...
where g++ >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   ✓ MinGW g++ found
    g++ --version | head -1
) else (
    echo   ✗ MinGW g++ not found in PATH
    if exist "C:\msys64\mingw64\bin\g++.exe" (
        echo   ✓ Found at C:\msys64\mingw64\bin\g++.exe
    ) else (
        echo   ✗ MinGW not found
    )
)
echo.

REM Check for Crypto++
echo [3/5] Checking Crypto++ library...
set CRYPTOPP_FOUND=0
if exist "C:\vcpkg\installed\x64-windows\include\cryptopp" (
    echo   ✓ Crypto++ found via vcpkg
    set CRYPTOPP_FOUND=1
)
if exist "C:\Program Files\cryptopp\include" (
    echo   ✓ Crypto++ found in Program Files
    set CRYPTOPP_FOUND=1
)
if exist "C:\cryptopp\include" (
    echo   ✓ Crypto++ found in C:\cryptopp
    set CRYPTOPP_FOUND=1
)
if %CRYPTOPP_FOUND% EQU 0 (
    echo   ✗ Crypto++ not found
    echo     Install via: vcpkg install cryptopp:x64-windows
)
echo.

REM Check for Boost
echo [4/5] Checking Boost library...
set BOOST_FOUND=0
if exist "C:\vcpkg\installed\x64-windows\include\boost" (
    echo   ✓ Boost found via vcpkg
    set BOOST_FOUND=1
)
if exist "C:\Program Files\boost\include" (
    echo   ✓ Boost found in Program Files
    set BOOST_FOUND=1
)
if exist "C:\boost\include" (
    echo   ✓ Boost found in C:\boost
    set BOOST_FOUND=1
)
if %BOOST_FOUND% EQU 0 (
    echo   ✗ Boost not found
    echo     Install via: vcpkg install boost-asio:x64-windows
)
echo.

REM Check for vcpkg
echo [5/5] Checking vcpkg package manager...
where vcpkg >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   ✓ vcpkg found in PATH
    vcpkg version | head -1
) else (
    if exist "C:\vcpkg\vcpkg.exe" (
        echo   ✓ vcpkg found at C:\vcpkg\vcpkg.exe
    ) else (
        echo   ✗ vcpkg not found
        echo     Install from: https://github.com/Microsoft/vcpkg
    )
)
echo.

echo ===============================================
echo                   SUMMARY
echo ===============================================
if %ERRORLEVEL% EQU 0 (
    echo Status: Ready for C++ development
) else (
    echo Status: Some dependencies missing
)
echo.
echo Recommended setup:
echo 1. Install vcpkg: git clone https://github.com/Microsoft/vcpkg.git
echo 2. Install dependencies: vcpkg install cryptopp:x64-windows boost-asio:x64-windows
echo 3. Integrate with VS: vcpkg integrate install
echo.
echo VS Code tasks available:
echo - Build TCP Client (MSVC)
echo - Build TCP Client (MinGW)  
echo - Test C++ Wrappers
echo - Run TCP Server (Debug)
echo ===============================================
pause
