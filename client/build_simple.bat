@echo off
echo ===============================================
echo    SIMPLE TEST BUILD (VERIFY CRITICAL FIXES)
echo ===============================================
echo.

REM Setup Visual Studio Build Tools environment
echo [1/3] Setting up MSVC environment...
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   ✗ Visual Studio Build Tools 2019 not found
    echo   Trying VS 2022...
    call "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo   ✗ Visual Studio Build Tools not found
        echo   Please install Visual Studio Build Tools
        pause
        exit /b 1
    )
)
echo   ✓ MSVC environment ready

REM Compile simple test (no Crypto++ dependencies)
echo.
echo [2/3] Building simple test...
cl /std:c++17 /EHsc /MD ^
   cksum.cpp simple_test.cpp ^
   /Fe:simple_test.exe

if %ERRORLEVEL% NEQ 0 (
    echo   ✗ Simple test build failed
    pause
    exit /b 1
)
echo   ✓ Simple test built successfully

REM Run the test
echo.
echo [3/3] Running simple test...
simple_test.exe

echo.
echo ===============================================
echo                BUILD COMPLETE
echo ===============================================
echo Built files:
if exist "simple_test.exe" echo   ✓ simple_test.exe
echo.
echo This test verifies:
echo - AES-256 fix (32-byte keys)
echo - Linux cksum algorithm
echo.
echo Next: Install compatible Crypto++ for full testing
echo ===============================================
pause
