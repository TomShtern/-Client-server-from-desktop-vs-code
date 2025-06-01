# Python script for uploading files to the backup server
# Provides an alternative to the C++ client for testing or quick uploads

import os
import sys
import requests
import base64
from urllib.parse import urljoin
import time

def format_size(size_bytes):
    """Convert size in bytes to human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.1f} GB"

def upload_file(url, username, password, file_path):
    """Upload a file to the backup server"""
    # Get file details
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    print(f"Uploading {file_name} ({format_size(file_size)})...")
    
    # Prepare request
    auth = requests.auth.HTTPBasicAuth(username, password)
    headers = {'X-Filename': file_name}
    
    # Upload with progress
    with open(file_path, 'rb') as f:
        start_time = time.time()
        
        response = requests.post(
            url,
            headers=headers,
            auth=auth,
            data=f
        )
        
        elapsed_time = time.time() - start_time
        
    # Display result
    if response.status_code == 200:
        print(f"Upload successful in {elapsed_time:.2f} seconds ({format_size(file_size/elapsed_time)}/s)")
        print(f"Server response: {response.text}")
        return True
    else:
        print(f"Upload failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"Usage: python {sys.argv[0]} <server_url> <username> <password> <file_path>")
        sys.exit(1)
    
    server_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    file_path = sys.argv[4]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    upload_file(server_url, username, password, file_path)
