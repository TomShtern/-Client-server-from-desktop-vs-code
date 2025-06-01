@echo off
REM This bat file tests both the Python server and C++ client for the secure file backup system

REM Create test directory if it doesn't exist
mkdir tmp 2>nul

REM First, create some test files
echo Creating test files...
python create_test_file.py tmp\test_small.dat 10
python create_test_file.py tmp\test_medium.dat 100

echo.
echo ======================================================
echo Step 1: Install required Python packages
echo ======================================================
pip install requests

echo.
echo ======================================================
echo Step 2: Start the Python server (in a separate window)
echo ======================================================
echo Please run 'start_server.bat' in a separate command prompt
echo and then press any key to continue with testing...
pause > nul

echo.
echo ======================================================
echo Step 3: Test the Python client
echo ======================================================
echo Running Python client to upload test file...
python client\python_client.py http://localhost:8080 user password tmp\test_small.dat

echo.
echo ======================================================
echo Step 4: C++ Client - This requires libcurl
echo ======================================================
echo If you have libcurl installed and want to build and test the C++ client:
echo 1. Navigate to the client directory
echo 2. Build with: g++ -std=c++17 client.cpp -o client.exe -lcurl
echo 3. Run with: client.exe http://localhost:8080 user password test_file.dat
echo.
echo Testing complete!
pause
