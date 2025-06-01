# Secure File Backup System

This project provides a file backup system with:

- A **Python server** that accepts file uploads over HTTP and stores them in a backup directory.
- A **C++ client** that connects, authenticates, and uploads files to the server.

## Structure

- `server/` — Python server code
- `client/` — C++ client code

## Features

- Basic authentication
- Multi-threaded server for handling multiple uploads
- File encryption at rest (when cryptography module is available)
- File deduplication to save storage space
- Web interface for browsing and downloading files
- Resumable uploads for large files (with enhanced client)

## Setup

1. Run the Python server (`python server.py` in the server directory).
2. Install libcurl (required for the C++ client).
3. Build and run the C++ client to upload files.

## Requirements

- Python 3.x (for server)
- C++ compiler with C++17 support (for client)
- libcurl (for client)

## Usage

### Starting the Server

```bash
cd server
python server.py
```

Or simply run the `start_server.bat` file to launch the server. The server will start on port 8080 and create a `backups` directory for storage.

### Using the C++ Client

```bash
cd client
client.exe http://localhost:8080 user password C:\path\to\file.txt
```

### Using the Python Client

```bash
cd client
python python_client.py http://localhost:8080 user password C:\path\to\file.txt
```

For more detailed instructions, see the READMEs in the `server/` and `client/` directories.

## Security Considerations

- The server uses basic HTTP authentication. For production use, consider implementing HTTPS.
- Default credentials are set to `user:password`. Change these in `server.py` before deployment.
- The backup files are stored in a subdirectory of the server. Consider using absolute paths for more secure storage.

## Potential Improvements

- Add file encryption at rest
- Implement file deduplication to save storage space
- Add integrity verification with hash checking
- Create a web interface for file browsing
- Implement resumable uploads for large files

## Testing

Run the included test scripts to verify your setup:

```bash
run_tests.bat
```

This will create sample files and upload them to test the system.
