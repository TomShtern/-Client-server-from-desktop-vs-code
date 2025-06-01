@echo off
echo Creating test file (1MB)...
python create_test_file.py test_file.dat 1024
echo.
echo Uploading test file to server...
cd client
client.exe http://localhost:8080 user password ..\test_file.dat
cd ..
echo.
echo Test completed!
