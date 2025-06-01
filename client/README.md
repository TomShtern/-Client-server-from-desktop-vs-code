# C++ File Backup Client

⚠️ **IMPORTANT**: This directory contains TWO different client implementations:

## Current Implementation (HTTP-based)
- **File**: `client.cpp`
- **Protocol**: HTTP with libcurl
- **Status**: ✅ Working with current Python servers
- **Build**: Use `build_http_client.bat` (no CMake needed)

## Specification Requirements (Binary TCP)
- **Protocol**: Binary TCP with Crypto++ and Boost.Asio
- **Status**: ❌ Not implemented yet
- **Details**: See `../Spesifications.md` for complete requirements

---

## Building the HTTP Client (Current)

### Quick Build (No CMake)
```bash
# Windows - just run the build script
build_http_client.bat
```

### Requirements for HTTP Client
- C++ compiler with C++17 support
- libcurl development files

### Manual Compilation

On Windows with MinGW:
```bash
g++ -std=c++17 client.cpp -o http_client.exe -lcurl
```

On Linux/macOS:
```bash
g++ -std=c++17 client.cpp -o http_client -lcurl
```

### Using CMake (Optional)
```bash
mkdir build
cd build
cmake ..
cmake --build .
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
