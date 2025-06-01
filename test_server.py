#!/usr/bin/env python
# Script to test uploading files to the backup server

import os
import sys
import time
import requests
import argparse
from datetime import datetime

def test_server(server_url, username, password, num_files=5, file_size_kb=100):
    """Run a stress test on the backup server"""
    print(f"Testing backup server at {server_url}")
    print(f"Creating {num_files} test files of {file_size_kb}KB each...")
    
    # Create test directory
    os.makedirs("test_files", exist_ok=True)
    
    # Create test files
    test_files = []
    for i in range(num_files):
        filename = f"test_files/test_{i+1}.dat"
        with open(filename, 'w') as f:
            # Create a file with specified size
            f.write('X' * (file_size_kb * 1024))
        test_files.append(filename)
    
    print(f"Created {len(test_files)} test files")
    
    # Upload files and measure time
    total_time = 0
    success_count = 0
    
    for file_path in test_files:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        print(f"Uploading {file_name} ({file_size} bytes)...", end='', flush=True)
        
        try:
            start_time = time.time()
            
            with open(file_path, 'rb') as f:
                headers = {'X-Filename': file_name}
                response = requests.post(
                    server_url,
                    auth=(username, password),
                    headers=headers,
                    data=f
                )
            
            elapsed = time.time() - start_time
            total_time += elapsed
            
            if response.status_code == 200:
                print(f" OK ({elapsed:.2f}s)")
                success_count += 1
            else:
                print(f" FAILED (Status: {response.status_code})")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print(f" ERROR: {str(e)}")
    
    # Print results
    print("\nTest Results:")
    print(f"Total files: {num_files}")
    print(f"Successful uploads: {success_count}")
    print(f"Failed uploads: {num_files - success_count}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average time per file: {total_time/num_files:.2f} seconds")
    
    if success_count > 0:
        total_mb = (file_size_kb * num_files) / 1024
        print(f"Upload speed: {total_mb/total_time:.2f} MB/s")
    
    # Clean up test files
    print("\nCleaning up test files...")
    for file_path in test_files:
        try:
            os.remove(file_path)
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test the backup server with multiple file uploads')
    parser.add_argument('--server', default='http://localhost:8080', help='Server URL')
    parser.add_argument('--username', default='user', help='Username for authentication')
    parser.add_argument('--password', default='password', help='Password for authentication')
    parser.add_argument('--files', type=int, default=5, help='Number of files to upload')
    parser.add_argument('--size', type=int, default=100, help='Size of each file in KB')
    
    args = parser.parse_args()
    
    test_server(args.server, args.username, args.password, args.files, args.size)
