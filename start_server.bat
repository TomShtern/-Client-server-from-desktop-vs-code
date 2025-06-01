@echo off
echo Starting backup server on port 8080...
start "" http://localhost:8080
cd server
python server.py
