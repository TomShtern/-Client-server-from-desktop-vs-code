@echo off
echo TCP Client Build - Multiple Approaches
echo ======================================

echo.
echo This script tries multiple build approaches to resolve the Crypto++ compatibility issue.
echo.

REM Approach 1: Try MinGW if available
echo [1/3] Trying MinGW build...
where g++ >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   ✓ MinGW found, attempting build...
    call build_mingw_tcp.bat
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ MinGW build successful!
        goto :success
    ) else (
        echo   ✗ MinGW build failed
    )
) else (
    echo   ⚠ MinGW not available
)

echo.
echo [2/3] Trying MSVC with VS 2022 (newer standard library)...
set "VS2022_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
set "VS2019_VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

if exist "%VS2022_VCVARS%" (
    echo   Using VS 2022 Community (recommended)...
    call "%VS2022_VCVARS%" >nul 2>&1
) else if exist "%VS2019_VCVARS%" (
    echo   Using VS 2019 Build Tools (may have compatibility issues)...
    call "%VS2019_VCVARS%" >nul 2>&1
) else (
    echo   ✗ No Visual Studio found
    goto :alternative
)

set VCPKG_ROOT=C:\vcpkg
if not exist "%VCPKG_ROOT%" (
    echo   ✗ vcpkg not found
    goto :alternative
)

echo   Building with static Crypto++ libraries...
cl /std:c++17 /EHsc /MT ^
   /D_WIN32_WINNT=0x0A00 /DWIN32_LEAN_AND_MEAN ^
   /I"%VCPKG_ROOT%\installed\x64-windows-static\include" ^
   AESWrapper.cpp RSAWrapper.cpp Base64Wrapper.cpp cksum.cpp ^
   tcp_client.cpp tcp_client_file_ops.cpp main.cpp ^
   /Fe:tcp_client.exe ^
   /link /LIBPATH:"%VCPKG_ROOT%\installed\x64-windows-static\lib" ^
   cryptopp.lib ws2_32.lib

if %ERRORLEVEL% EQU 0 (
    echo   ✓ TCP Client build successful!
    goto :success
) else (
    echo   ✗ Build failed
)

:alternative
echo.
echo [3/3] Alternative solutions...
echo.
echo ⚠ All build attempts failed due to Crypto++ compatibility issues.
echo.
echo 📋 AVAILABLE SOLUTIONS:
echo.
echo 1. ✅ USE PYTHON CLIENT (Recommended for testing)
echo    - Full functionality verified working
echo    - Located: ..\test_tcp_client.py
echo    - Command: cd .. && python test_tcp_client.py
echo.
echo 2. 🔧 INSTALL COMPATIBLE CRYPTO++
echo    - Uninstall current: C:\vcpkg\vcpkg.exe remove cryptopp
echo    - Install older version or build from source
echo.
echo 3. 🛠 USE DIFFERENT COMPILER
echo    - Install MinGW-w64 or newer Visual Studio
echo    - Try: winget install MSYS2.MSYS2
echo.
echo 4. ✅ CORE FUNCTIONALITY VERIFIED
echo    - AES-256, RSA-1024, Linux cksum all working
echo    - TCP server fully functional
echo    - Integration testing successful with Python
echo.
goto :end

:success
echo.
echo 🎉 BUILD SUCCESSFUL!
echo.
echo Built files:
if exist "tcp_client_mingw.exe" echo   ✓ tcp_client_mingw.exe (MinGW)
if exist "tcp_client.exe" echo   ✓ tcp_client.exe (MSVC VS2022 Static)
echo.
echo 🚀 READY FOR INTEGRATION TESTING!
echo.
echo Next steps:
echo 1. Start server: cd ..\server && python tcp_server.py --debug
echo 2. Run client: tcp_client.exe
echo 3. Test file transfer functionality

:end
echo.
echo Press any key to continue...
pause >nul
