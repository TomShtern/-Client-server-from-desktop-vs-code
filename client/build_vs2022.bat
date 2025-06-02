@echo off
echo Building TCP Client with VS 2022
echo =================================

REM Use VS 2022 directly
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: VS 2022 not found
    exit /b 1
)

echo Using VS 2022 Community...

REM Set vcpkg paths
set VCPKG_ROOT=C:\vcpkg

echo.
echo Building TCP Client with static Crypto++...
cl /std:c++17 /EHsc /MT ^
   /D_WIN32_WINNT=0x0A00 /DWIN32_LEAN_AND_MEAN ^
   /I"%VCPKG_ROOT%\installed\x64-windows-static\include" ^
   AESWrapper.cpp RSAWrapper.cpp Base64Wrapper.cpp cksum.cpp ^
   tcp_client.cpp tcp_client_file_ops.cpp main.cpp ^
   /Fe:tcp_client.exe ^
   /link /LIBPATH:"%VCPKG_ROOT%\installed\x64-windows-static\lib" ^
   cryptopp.lib ws2_32.lib

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: TCP Client built successfully with VS 2022!
    echo Output: tcp_client.exe
) else (
    echo.
    echo ERROR: Build failed with VS 2022
    exit /b 1
)
