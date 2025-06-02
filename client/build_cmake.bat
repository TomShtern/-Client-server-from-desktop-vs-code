@echo off
echo ===============================================
echo    BUILDING TCP CLIENT WITH CMAKE + VCPKG
echo ===============================================
echo.

REM Setup Visual Studio Build Tools environment
echo [1/4] Setting up MSVC environment...
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

REM Check for vcpkg
echo.
echo [2/4] Checking vcpkg integration...
if not exist "C:\vcpkg\vcpkg.exe" (
    echo   ✗ vcpkg not found at C:\vcpkg\vcpkg.exe
    echo     Please install vcpkg first
    pause
    exit /b 1
)
echo   ✓ vcpkg found

REM Create build directory
echo.
echo [3/4] Setting up build directory...
if exist "build" rmdir /s /q build
mkdir build
cd build

REM Configure with CMake
echo.
echo [4/4] Building with CMake...
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:\vcpkg\scripts\buildsystems\vcpkg.cmake -G "Visual Studio 16 2019" -A x64

if %ERRORLEVEL% NEQ 0 (
    echo   ✗ CMake configuration failed
    cd ..
    pause
    exit /b 1
)

cmake --build . --config Release

if %ERRORLEVEL% NEQ 0 (
    echo   ✗ CMake build failed
    cd ..
    pause
    exit /b 1
)

REM Copy executables to parent directory
if exist "Release\test_wrappers.exe" (
    copy "Release\test_wrappers.exe" "..\test_wrappers.exe" >nul
    echo   ✓ test_wrappers.exe built successfully
) else (
    echo   ✗ test_wrappers.exe not found
)

if exist "Release\tcp_client.exe" (
    copy "Release\tcp_client.exe" "..\tcp_client.exe" >nul
    echo   ✓ tcp_client.exe built successfully
) else (
    echo   ✗ tcp_client.exe not found
)

cd ..

echo.
echo ===============================================
echo                BUILD COMPLETE
echo ===============================================
echo Built files:
if exist "test_wrappers.exe" echo   ✓ test_wrappers.exe
if exist "tcp_client.exe" echo   ✓ tcp_client.exe
echo.
echo Next steps:
echo 1. Run: test_wrappers.exe (test crypto functions)
echo 2. Run: tcp_client.exe (full TCP client)
echo 3. Test with Python TCP server
echo ===============================================
pause
