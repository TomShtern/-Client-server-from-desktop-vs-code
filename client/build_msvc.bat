@echo off
echo ===============================================
echo    BUILDING TCP CLIENT WITH MSVC (VS 2019)
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

REM Check for required libraries
echo.
echo [2/4] Checking dependencies...
set INCLUDE_PATHS=
set LIB_PATHS=
set LIBS=

REM Check for vcpkg
if exist "C:\vcpkg\installed\x64-windows\include\cryptopp" (
    echo   ✓ Using vcpkg Crypto++
    set INCLUDE_PATHS=%INCLUDE_PATHS% /I"C:\vcpkg\installed\x64-windows\include"
    set LIB_PATHS=%LIB_PATHS% /LIBPATH:"C:\vcpkg\installed\x64-windows\lib"
    set LIBS=%LIBS% cryptopp.lib
) else (
    echo   ✗ Crypto++ not found via vcpkg
    echo     Install with: vcpkg install cryptopp:x64-windows
    pause
    exit /b 1
)

if exist "C:\vcpkg\installed\x64-windows\include\boost" (
    echo   ✓ Using vcpkg Boost
    REM Boost is header-only for what we need
) else (
    echo   ✗ Boost not found via vcpkg
    echo     Install with: vcpkg install boost-asio:x64-windows
    pause
    exit /b 1
)

REM Compile wrapper test first
echo.
echo [3/4] Building wrapper tests...
cl /std:c++17 /EHsc /MD %INCLUDE_PATHS% ^
   AESWrapper.cpp RSAWrapper.cpp Base64Wrapper.cpp cksum.cpp test_wrappers.cpp ^
   /Fe:test_wrappers.exe ^
   /link %LIB_PATHS% %LIBS% ws2_32.lib msvcrt.lib

if %ERRORLEVEL% NEQ 0 (
    echo   ✗ Wrapper test build failed
    pause
    exit /b 1
)
echo   ✓ Wrapper tests built successfully

REM Build actual TCP client
echo.
echo [4/4] Building TCP Client...
cl /std:c++17 /EHsc /MD %INCLUDE_PATHS% ^
   AESWrapper.cpp RSAWrapper.cpp Base64Wrapper.cpp cksum.cpp ^
   tcp_client.cpp tcp_client_file_ops.cpp main.cpp ^
   /Fe:tcp_client.exe ^
   /link %LIB_PATHS% %LIBS% ws2_32.lib msvcrt.lib

if %ERRORLEVEL% NEQ 0 (
    echo   ✗ TCP client build failed
    pause
    exit /b 1
)
echo   ✓ TCP client built successfully

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
