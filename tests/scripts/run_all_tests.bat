@echo off
REM Comprehensive test runner for the secure file backup system
REM Runs unit tests, integration tests, and generates reports

echo ===============================================
echo     SECURE FILE BACKUP SYSTEM - TEST SUITE
echo ===============================================
echo.

set "PROJECT_ROOT=%~dp0..\.."
set "CLIENT_DIR=%PROJECT_ROOT%\client"
set "TESTS_DIR=%PROJECT_ROOT%\tests"
set "UNIT_DIR=%TESTS_DIR%\unit"
set "INTEGRATION_DIR=%TESTS_DIR%\integration"

echo Project Root: %PROJECT_ROOT%
echo Client Directory: %CLIENT_DIR%
echo Tests Directory: %TESTS_DIR%
echo.

REM Check if we're in the right directory
if not exist "%CLIENT_DIR%\tcp_client.h" (
    echo ❌ Error: Project structure not found
    echo Make sure you're running this from the tests\scripts directory
    pause
    exit /b 1
)

echo ===============================================
echo              PHASE 1: BUILD TESTS
echo ===============================================
echo.

REM Build unit tests
echo [1/4] Building unit tests...
cd /d "%CLIENT_DIR%"

REM Check for Visual Studio environment
call "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" 2>nul
if %ERRORLEVEL% NEQ 0 (
    call "%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Visual Studio environment not found
        echo Please install Visual Studio 2019 Build Tools or VS 2022 Community
        pause
        exit /b 1
    )
)

echo   ✓ Visual Studio environment loaded

REM Set include and library paths
set "VCPKG_ROOT=C:\vcpkg"
if not exist "%VCPKG_ROOT%" (
    echo ❌ vcpkg not found at %VCPKG_ROOT%
    echo Please install vcpkg and Crypto++ packages
    pause
    exit /b 1
)

set "INCLUDE_PATHS=/I"%VCPKG_ROOT%\installed\x64-windows-static\include""
set "LIB_PATHS=/LIBPATH:"%VCPKG_ROOT%\installed\x64-windows-static\lib""
set "LIBS=cryptopp-static.lib"

echo   ✓ vcpkg environment configured

REM Build AES wrapper test
echo.
echo [2/4] Building AES wrapper test...
cl /std:c++17 /EHsc /MT %INCLUDE_PATHS% ^
   AESWrapper.cpp Base64Wrapper.cpp "%UNIT_DIR%\test_aes_wrapper.cpp" ^
   /Fe:"%UNIT_DIR%\test_aes_wrapper.exe" ^
   /link %LIB_PATHS% %LIBS%

if %ERRORLEVEL% NEQ 0 (
    echo   ❌ AES wrapper test build failed
    pause
    exit /b 1
)
echo   ✓ AES wrapper test built successfully

REM Build RSA wrapper test
echo.
echo [3/4] Building RSA wrapper test...
cl /std:c++17 /EHsc /MT %INCLUDE_PATHS% ^
   RSAWrapper.cpp Base64Wrapper.cpp "%UNIT_DIR%\test_rsa_wrapper.cpp" ^
   /Fe:"%UNIT_DIR%\test_rsa_wrapper.exe" ^
   /link %LIB_PATHS% %LIBS%

if %ERRORLEVEL% NEQ 0 (
    echo   ❌ RSA wrapper test build failed
    pause
    exit /b 1
)
echo   ✓ RSA wrapper test built successfully

REM Build CRC test
echo.
echo [4/4] Building CRC test...
cl /std:c++17 /EHsc /MT ^
   cksum.cpp "%UNIT_DIR%\test_cksum.cpp" ^
   /Fe:"%UNIT_DIR%\test_cksum.exe"

if %ERRORLEVEL% NEQ 0 (
    echo   ❌ CRC test build failed
    pause
    exit /b 1
)
echo   ✓ CRC test built successfully

echo.
echo ===============================================
echo              PHASE 2: UNIT TESTS
echo ===============================================
echo.

REM Run unit tests
cd /d "%UNIT_DIR%"

echo [1/3] Running AES wrapper tests...
if exist "test_aes_wrapper.exe" (
    test_aes_wrapper.exe
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ AES wrapper tests passed
    ) else (
        echo   ❌ AES wrapper tests failed
    )
) else (
    echo   ❌ AES wrapper test executable not found
)

echo.
echo [2/3] Running RSA wrapper tests...
if exist "test_rsa_wrapper.exe" (
    test_rsa_wrapper.exe
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ RSA wrapper tests passed
    ) else (
        echo   ❌ RSA wrapper tests failed
    )
) else (
    echo   ❌ RSA wrapper test executable not found
)

echo.
echo [3/3] Running CRC tests...
if exist "test_cksum.exe" (
    test_cksum.exe
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ CRC tests passed
    ) else (
        echo   ❌ CRC tests failed
    )
) else (
    echo   ❌ CRC test executable not found
)

echo.
echo ===============================================
echo           PHASE 3: INTEGRATION TESTS
echo ===============================================
echo.

REM Check Python environment
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found
    echo Please install Python 3.11+ and ensure it's in PATH
    pause
    exit /b 1
)

echo   ✓ Python environment available

REM Run integration tests
cd /d "%INTEGRATION_DIR%"

echo [1/1] Running client-server integration tests...
python test_client_server.py
if %ERRORLEVEL% EQU 0 (
    echo   ✓ Integration tests passed
) else (
    echo   ❌ Integration tests failed
)

echo.
echo ===============================================
echo              PHASE 4: CLEANUP
echo ===============================================
echo.

REM Clean up test executables
cd /d "%UNIT_DIR%"
if exist "*.exe" (
    del "*.exe"
    echo   ✓ Unit test executables cleaned up
)

if exist "*.obj" (
    del "*.obj"
    echo   ✓ Object files cleaned up
)

echo.
echo ===============================================
echo                TEST SUMMARY
echo ===============================================
echo.

echo 🧪 Test Suite Execution Complete
echo.
echo Components tested:
echo   • AES-256 encryption/decryption wrapper
echo   • RSA-1024 key generation and encryption wrapper
echo   • Linux cksum CRC calculation algorithm
echo   • End-to-end client-server file transfer
echo   • Protocol compliance and error handling
echo.
echo 📊 For detailed results, review the output above
echo.
echo Next steps:
echo   1. Review any failed tests and fix issues
echo   2. Run performance tests if needed
echo   3. Test with different file types and sizes
echo   4. Verify production deployment readiness
echo.

pause
