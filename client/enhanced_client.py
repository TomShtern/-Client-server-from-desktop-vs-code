# Python client with resumable uploads
import os
import sys
import requests
import base64
import hashlib
import argparse
import time
from urllib.parse import urljoin

CHUNK_SIZE = 1024 * 1024  # 1MB chunks

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

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of file for integrity verification"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def upload_file(url, username, password, file_path, resumable=False):
    """Upload a file to the backup server"""
    # Get file details
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_hash = calculate_file_hash(file_path)
    
    print(f"Uploading {file_name} ({format_size(file_size)})...")
    
    # Prepare authentication
    auth = requests.auth.HTTPBasicAuth(username, password)
    
    # Standard upload
    if not resumable or file_size < CHUNK_SIZE:
        # Upload with progress
        with open(file_path, 'rb') as f:
            start_time = time.time()
            
            headers = {
                'X-Filename': file_name,
                'X-File-Hash': file_hash
            }
            
            response = requests.post(
                url,
                headers=headers,
                auth=auth,
                data=f
            )
            
            elapsed_time = time.time() - start_time
            
        # Check response
        if response.status_code == 200:
            print(f"Upload successful in {elapsed_time:.1f}s ({format_size(file_size/elapsed_time)}/s)")
            print(f"Server response: {response.text}")
            return True
        else:
            print(f"Upload failed: {response.status_code} - {response.text}")
            return False
    
    # Resumable upload (chunked)
    else:
        print(f"Using resumable upload with {CHUNK_SIZE/1024/1024:.1f}MB chunks")
        total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
        
        with open(file_path, 'rb') as f:
            start_time = time.time()
            
            for chunk_num in range(total_chunks):
                # Read chunk
                f.seek(chunk_num * CHUNK_SIZE)
                chunk_data = f.read(CHUNK_SIZE)
                
                # Calculate progress
                bytes_sent = (chunk_num * CHUNK_SIZE) + len(chunk_data)
                progress = bytes_sent / file_size * 100
                
                # Upload chunk
                headers = {
                    'X-Filename': file_name,
                    'X-Chunk-Number': str(chunk_num),
                    'X-Total-Chunks': str(total_chunks),
                    'X-File-Size': str(file_size),
                    'X-File-Hash': file_hash
                }
                
                # Display progress
                print(f"\rUploading: {progress:.1f}% ({chunk_num+1}/{total_chunks} chunks)", end="")
                
                # Send chunk
                response = requests.post(
                    url,
                    headers=headers,
                    auth=auth,
                    data=chunk_data
                )
                
                # Check response
                if response.status_code != 200:
                    print(f"\nChunk {chunk_num+1} upload failed: {response.status_code} - {response.text}")
                    return False
            
            elapsed_time = time.time() - start_time
            print(f"\nUpload successful in {elapsed_time:.1f}s ({format_size(file_size/elapsed_time)}/s)")
            return True

def main():
    parser = argparse.ArgumentParser(description='Upload files to backup server')
    parser.add_argument('url', help='Server URL (e.g., http://localhost:8080)')
    parser.add_argument('username', help='Authentication username')
    parser.add_argument('password', help='Authentication password')
    parser.add_argument('file_path', help='Path to file for upload')
    parser.add_argument('--resumable', action='store_true', help='Use resumable upload for large files')
    
    args = parser.parse_args()
    
    # Validate file path
    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        return 1
    
    # Perform upload
    success = upload_file(args.url, args.username, args.password, args.file_path, args.resumable)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
