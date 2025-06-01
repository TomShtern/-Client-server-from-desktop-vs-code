# C++ File Backup Client

This is a C++ client for uploading files to the backup server.

## Requirements

- C++ compiler with C++17 support
- libcurl development files

## Building the Client

### Using CMake (Recommended)

```bash
mkdir build
cd build
cmake ..
cmake --build .
```

### Manual Compilation

On Windows with MinGW:

```bash
g++ -std=c++17 client.cpp -o client.exe -lcurl
```

On Linux/macOS:

```bash
g++ -std=c++17 client.cpp -o client -lcurl
```

## Installing libcurl

### Windows

1. Download the curl development files from [curl.se/windows](https://curl.se/windows/)
2. Extract the files
3. Add the bin directory to your PATH

### Ubuntu/Debian

```bash
sudo apt-get install libcurl4-openssl-dev
```

### macOS

```bash
brew install curl
```

## Usage

```bash
client <server_url> <username> <password> <file_path>
```

Example:

```bash
client http://localhost:8080 user password C:/path/to/file.txt
```

## Features

- Visual progress bar for upload tracking
- Speed and transfer size reporting
- Basic error handling
- Proper authentication with the server

## Alternative Python Client

For those who prefer Python or want to avoid C++ compilation, the repository includes a Python client:

```bash
python python_client.py <server_url> <username> <password> <file_path>
```

Example:

```bash
python python_client.py http://localhost:8080 user password C:/path/to/file.txt
```

## Enhanced Python Client

We also provide an enhanced Python client with additional features:

```bash
python enhanced_client.py <server_url> <username> <password> <file_path> [--resumable]
```

### Enhanced Features

- **Resumable Uploads**: For large files, use `--resumable` to upload in chunks
- **Hash Verification**: Files include SHA-256 hash for integrity verification
- **Better Progress Display**: Shows upload progress and transfer speed

## Troubleshooting

- **Connection refused**: Make sure the server is running and accessible
- **Authentication failed**: Check username and password
- **File not found**: Ensure the file path is correct
- **Cannot resolve host**: Check network connection and server URL
