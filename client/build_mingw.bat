@echo off
echo ===============================================
echo    BUILDING TCP CLIENT WITH MINGW/MSYS2
echo ===============================================
echo.

REM Check for MinGW
echo [1/4] Checking MinGW environment...
where g++ >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   ✗ g++ not found in PATH
    if exist "C:\msys64\mingw64\bin\g++.exe" (
        echo   ✓ Found MinGW at C:\msys64\mingw64\bin\
        set PATH=C:\msys64\mingw64\bin;%PATH%
    ) else (
        echo   ✗ MinGW not found
        echo   Please install MSYS2 and MinGW-w64
        pause
        exit /b 1
    )
)
echo   ✓ MinGW g++ ready

REM Check for required libraries
echo.
echo [2/4] Checking dependencies...
set INCLUDE_PATHS=
set LIB_PATHS=
set LIBS=

REM Check for Crypto++ in MSYS2
if exist "C:\msys64\mingw64\include\cryptopp" (
    echo   ✓ Using MSYS2 Crypto++
    set INCLUDE_PATHS=%INCLUDE_PATHS% -I"C:\msys64\mingw64\include"
    set LIB_PATHS=%LIB_PATHS% -L"C:\msys64\mingw64\lib"
    set LIBS=%LIBS% -lcryptopp
) else (
    echo   ✗ Crypto++ not found in MSYS2
    echo     Install with: pacman -S mingw-w64-x86_64-crypto++
    pause
    exit /b 1
)

if exist "C:\msys64\mingw64\include\boost" (
    echo   ✓ Using MSYS2 Boost
    set LIBS=%LIBS% -lboost_system
) else (
    echo   ✗ Boost not found in MSYS2
    echo     Install with: pacman -S mingw-w64-x86_64-boost
    pause
    exit /b 1
)

REM Compile wrapper test first
echo.
echo [3/4] Building wrapper tests...
g++ -std=c++17 %INCLUDE_PATHS% ^
    AESWrapper.cpp RSAWrapper.cpp Base64Wrapper.cpp cksum.cpp test_wrappers.cpp ^
    -o test_wrappers.exe ^
    %LIB_PATHS% %LIBS% -lws2_32

if %ERRORLEVEL% NEQ 0 (
    echo   ✗ Wrapper test build failed
    pause
    exit /b 1
)
echo   ✓ Wrapper tests built successfully

REM Build actual TCP client
echo.
echo [4/4] Building TCP Client...
g++ -std=c++17 %INCLUDE_PATHS% ^
    AESWrapper.cpp RSAWrapper.cpp Base64Wrapper.cpp cksum.cpp ^
    tcp_client.cpp tcp_client_file_ops.cpp main.cpp ^
    -o tcp_client.exe %LIB_PATHS% %LIBS% -lws2_32

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
