@echo off
echo Simple Build Test - Direct Approach
echo ===================================

REM Try to find and use Visual Studio tools
set "VS2019_VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "VS2022_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

if exist "%VS2019_VCVARS%" (
    echo Using VS 2019 Build Tools...
    call "%VS2019_VCVARS%" >nul 2>&1
) else if exist "%VS2022_VCVARS%" (
    echo Using VS 2022 Community...
    call "%VS2022_VCVARS%" >nul 2>&1
) else (
    echo No Visual Studio found! Please install VS Build Tools.
    pause
    exit /b 1
)

REM Set vcpkg paths
set VCPKG_ROOT=C:\vcpkg
if not exist "%VCPKG_ROOT%" (
    echo vcpkg not found at %VCPKG_ROOT%
    pause
    exit /b 1
)

echo.
echo Building simple test with static runtime...
cl /std:c++17 /EHsc /MT ^
   /I"%VCPKG_ROOT%\installed\x64-windows\include" ^
   simple_test.cpp AESWrapper.cpp RSAWrapper.cpp Base64Wrapper.cpp cksum.cpp ^
   /Fe:simple_test_static.exe ^
   /link /LIBPATH:"%VCPKG_ROOT%\installed\x64-windows\lib" ^
   cryptopp.lib

if %ERRORLEVEL% EQU 0 (
    echo Static runtime build successful!
    echo Running test...
    simple_test_static.exe
    goto :end
)

echo Static runtime failed, trying dynamic with newer libs...
cl /std:c++20 /EHsc /MD ^
   /I"%VCPKG_ROOT%\installed\x64-windows\include" ^
   simple_test.cpp AESWrapper.cpp RSAWrapper.cpp Base64Wrapper.cpp cksum.cpp ^
   /Fe:simple_test_cpp20.exe ^
   /link /LIBPATH:"%VCPKG_ROOT%\installed\x64-windows\lib" ^
   cryptopp.lib

if %ERRORLEVEL% EQU 0 (
    echo C++20 build successful!
    echo Running test...
    simple_test_cpp20.exe
    goto :end
)

echo All build attempts failed!
echo This is the known Crypto++ compatibility issue.
echo The vcpkg Crypto++ was compiled with a newer C++ standard library.
pause
exit /b 1

:end
echo Build completed successfully!
