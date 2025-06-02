@echo off
echo ===============================================
echo         CLEANING BUILD ARTIFACTS
echo ===============================================
echo.

echo Removing executable files...
if exist "test_wrappers.exe" (
    del "test_wrappers.exe"
    echo   ✓ Removed test_wrappers.exe
)
if exist "tcp_client.exe" (
    del "tcp_client.exe"
    echo   ✓ Removed tcp_client.exe
)
if exist "client.exe" (
    del "client.exe"
    echo   ✓ Removed client.exe
)

echo.
echo Removing object files...
if exist "*.obj" (
    del "*.obj"
    echo   ✓ Removed .obj files
)
if exist "*.o" (
    del "*.o"
    echo   ✓ Removed .o files
)

echo.
echo Removing debug files...
if exist "*.pdb" (
    del "*.pdb"
    echo   ✓ Removed .pdb files
)
if exist "*.ilk" (
    del "*.ilk"
    echo   ✓ Removed .ilk files
)

echo.
echo ===============================================
echo            CLEAN COMPLETE
echo ===============================================
echo All build artifacts removed.
echo Ready for fresh build.
echo ===============================================
