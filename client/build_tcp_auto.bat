@echo off
echo TCP Client Autonomous Build
echo ===========================

REM Set up Visual Studio environment - prioritize VS 2022 for newer standard library
set "VS2019_VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "VS2022_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

if exist "%VS2022_VCVARS%" (
    echo Using VS 2022 Community (newer standard library)...
    call "%VS2022_VCVARS%" >nul 2>&1
) else if exist "%VS2019_VCVARS%" (
    echo Using VS 2019 Build Tools...
    call "%VS2019_VCVARS%" >nul 2>&1
) else (
    echo ERROR: No Visual Studio found
    exit /b 1
)

REM Set vcpkg paths
set VCPKG_ROOT=C:\vcpkg
if not exist "%VCPKG_ROOT%" (
    echo ERROR: vcpkg not found
    exit /b 1
)

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
    echo SUCCESS: TCP Client built successfully!
    echo Output: tcp_client.exe
    exit /b 0
) else (
    echo.
    echo ERROR: Build failed
    exit /b 1
)
