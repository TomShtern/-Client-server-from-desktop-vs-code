@echo off
echo Creating test files for backup...

python create_test_file.py testfile_small.dat 10
python create_test_file.py testfile_medium.dat 100
python create_test_file.py testfile_large.dat 1000

echo Test files created!
echo.
echo To use them, build the C++ client and run:
echo client.exe http://localhost:8080 user password testfile_small.dat
echo.
echo Press any key to exit...
pause > nul
