@echo off
echo Starting enhanced backup server (with encryption and file browser) on port 8080...
start "" http://localhost:8080
cd server
python enhanced_server.py
