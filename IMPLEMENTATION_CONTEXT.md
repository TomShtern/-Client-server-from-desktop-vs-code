# Implementation Context & Plan for Secure File Backup System

## 📋 **CRITICAL PROJECT CONTEXT**

### **🔑 Project State & Repository**
- **GitHub Repository**: https://github.com/TomShtern/-Client-server-from-desktop-vs-code.git
- **Working Directory**: `c:\Users\user\VSCode\Secure_baclup_Server`
- **Current Status**: HTTP system working, TCP binary protocol server implemented but needs critical fixes
- **User**: Tom Shtern, prefers step-by-step approval before coding changes

### **📖 Specification Compliance Requirements**
- **Source of Truth**: `Spesifications.md` - ABSOLUTE compliance required
- **Current Gap**: HTTP system vs Binary TCP protocol requirement
- **Critical Rule**: Never deviate from specifications, always reference it first
- **Goal**: Full compliance first, then eventual enhancement

### **💻 Development Environment**
- **IDE**: VS Code (NOT Visual Studio IDE)
- **Available Compilers**: Visual Studio Build Tools 2019, possibly MinGW
- **Preference**: Avoid CMake complexity, use direct compilation
- **Build Strategy**: VS Code tasks and build scripts

### **🔧 Available Code Assets**
- **File**: `All_code_Snippets_and_files_that_are_given_with_this_project.md`
- **Contains**:
  - Linux cksum implementation (memcrc function) - Lines 8-507
  - AESWrapper (needs 16→32 byte key fix) - Lines 814-1023
  - RSAWrapper (perfect 160-byte X.509 format) - Lines 1027-1474+
  - Base64Wrapper (for me.info storage) - Lines 692-809
  - Boost.Asio examples - Lines 512-563
  - Socket programming examples - Lines 568-687
- **Status**: Must be used as foundation, can modify to suit needs
- **Critical**: Core should remain intact, modify only as needed for specifications

### **⚙️ Critical Technical Requirements**
- **Server**: Python 3.11.4 with PyCryptodome (installed)
- **Client**: C++17 with Crypto++ and Boost.Asio
- **Protocol**: Binary TCP, version 3, little-endian
- **Encryption**: RSA-1024 + AES-256-CBC (NOT 128-bit!)
- **CRC**: Linux cksum algorithm (provided in code snippets)
- **Port**: Read from port.info, default 1256

### **🚨 Immediate Critical Fixes Identified**
1. **AESWrapper**: DEFAULT_KEYLENGTH = 16 → 32 (specification violation)
2. **Server RSA**: Handle 160-byte X.509 format from C++ client
3. **cksum**: Port C++ implementation to Python server
4. **Build System**: VS Code tasks, no CMake
5. **Client Session Management**: Fix session lookup in file transfer (use client_id from header)
6. **Reconnection Logic**: Validate both UUID from header AND username from payload

### **🧠 Memory Context**
- User prefers descriptive GitHub repository names like 'Client-server from desktop vs code'
- Project uses specifications.md as source of truth and goal is full compliance with it
- Python server uses pycryptodome, C++ client uses cryptopp and boost.asio
- User prefers to avoid CMake complexity and step-by-step implementation planning with approval
- User has Visual Studio and VS Build Tools 2019 installed, possibly MinGW
- User is using VS Code for development, so build system should be adjusted accordingly
- User emphasizes specifications.md as the absolute source of truth that must be adhered to

---

## 📋 **VS CODE-OPTIMIZED IMPLEMENTATION PLAN**

### **PHASE 2: SERVER FIXES USING PROVIDED CODE**

#### **Step 2.1: Port Linux cksum to Python** ⚠️ **HIGH PRIORITY**
- **Action**: Convert provided C++ `memcrc` function to Python
- **Files**: `server/tcp_server.py` - replace `_calculate_cksum` method
- **Method**: Direct port of CRC table and algorithm logic
- **Test**: Verify against known Linux cksum values

#### **Step 2.2: Fix AES Key Size Verification** ⚠️ **CRITICAL**
- **Action**: Ensure server uses 32-byte AES keys consistently
- **Files**: `server/tcp_server.py` - verify `AES_KEY_SIZE = 32`
- **Status**: Likely already correct, but need verification

#### **Step 2.3: Fix RSA Public Key Handling** ⚠️ **CRITICAL**
- **Action**: Handle 160-byte X.509 format from C++ RSAWrapper
- **Method**: Research PyCryptodome raw X.509 byte import
- **Files**: `server/tcp_server.py` - `_handle_send_public_key`

### **PHASE 3: C++ CLIENT FOR VS CODE ENVIRONMENT**

#### **Step 3.1: Create VS Code Build Configuration** 
- **Action**: Set up VS Code tasks.json and c_cpp_properties.json
- **Method**: Configure for Visual Studio Build Tools 2019 (cl.exe)
- **Alternative**: MinGW g++ if available and preferred
- **Files**: `.vscode/tasks.json`, `.vscode/c_cpp_properties.json`
- **No CMake**: Direct compiler invocation

#### **Step 3.2: Fix AESWrapper for 32-byte Keys** ⚠️ **CRITICAL**
- **Action**: Modify provided AESWrapper for 256-bit keys
- **Change**: `DEFAULT_KEYLENGTH = 16` → `DEFAULT_KEYLENGTH = 32`
- **Files**: `client/AESWrapper.h`, `client/AESWrapper.cpp`
- **Critical**: Maintain zero IV as required by spec

#### **Step 3.3: Extract and Organize Provided Code**
- **Action**: Extract wrapper classes from consolidated file
- **Files**: 
  - `client/cksum.cpp` (extract memcrc function)
  - `client/AESWrapper.h/.cpp` (with 32-byte fix)
  - `client/RSAWrapper.h/.cpp` (as-is)
  - `client/Base64Wrapper.h/.cpp` (as-is)
- **Status**: Ready to use with minor modifications

#### **Step 3.4: Create Simple Build Script for VS Code**
- **Action**: Create batch script for compilation
- **Method**: Direct cl.exe or g++ invocation
- **Files**: `client/build.bat` (Windows batch script)
- **Dependencies**: Auto-detect Crypto++, Boost libraries
- **Example**:
  ```batch
  @echo off
  REM Try Visual Studio Build Tools first
  call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" 2>nul
  if %ERRORLEVEL% EQU 0 (
      cl /std:c++17 *.cpp /Fe:tcp_client.exe /I"path\to\cryptopp" /I"path\to\boost"
  ) else (
      REM Fallback to MinGW if available
      g++ -std=c++17 *.cpp -o tcp_client.exe -lcryptopp -lboost_system
  )
  ```

#### **Step 3.5: VS Code IntelliSense Configuration**
- **Action**: Configure C++ extension for proper code completion
- **Files**: `.vscode/c_cpp_properties.json`
- **Include Paths**: Crypto++, Boost headers
- **Compiler**: cl.exe or g++ depending on availability

#### **Step 3.6: Implement Binary Protocol with Boost.Asio**
- **Action**: Adapt provided Boost examples for binary protocol
- **Files**: `client/network.cpp`, `client/protocol.cpp`
- **Method**: Replace string messages with binary structs
- **Base**: Use provided boost-client.cpp as foundation

### **PHASE 4: VS CODE INTEGRATION & TESTING**

#### **Step 4.1: VS Code Tasks for Build/Run**
- **Action**: Create VS Code tasks for build, clean, run
- **Files**: `.vscode/tasks.json`
- **Tasks**: 
  - Build client
  - Build and run server
  - Clean build artifacts
  - Run tests

#### **Step 4.2: VS Code Launch Configuration**
- **Action**: Set up debugging configuration
- **Files**: `.vscode/launch.json`
- **Targets**: Debug client, debug server, attach to running processes

#### **Step 4.3: Library Detection Script**
- **Action**: Create script to detect available libraries
- **Files**: `detect_libs.bat`
- **Purpose**: Auto-configure build based on available Crypto++/Boost

---

## 🎯 **VS CODE-SPECIFIC IMMEDIATE ACTIONS**

### **Priority 1: Verify Build Environment**
```batch
REM Create detect_environment.bat
@echo off
echo Detecting build environment for VS Code...

REM Check for Visual Studio Build Tools
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Visual Studio Build Tools 2019 found
    cl 2>nul
    if %ERRORLEVEL% EQU 0 echo ✓ cl.exe compiler available
) else (
    echo ✗ Visual Studio Build Tools not found
)

REM Check for MinGW
g++ --version 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ MinGW g++ found
) else (
    echo ✗ MinGW g++ not found
)
```

### **Priority 2: VS Code Configuration Files**
```json
// .vscode/c_cpp_properties.json
{
    "configurations": [
        {
            "name": "Win32",
            "includePath": [
                "${workspaceFolder}/**",
                "C:/path/to/cryptopp",
                "C:/path/to/boost"
            ],
            "defines": ["_DEBUG", "UNICODE", "_UNICODE"],
            "windowsSdkVersion": "10.0.19041.0",
            "compilerPath": "cl.exe",
            "cStandard": "c17",
            "cppStandard": "c++17",
            "intelliSenseMode": "windows-msvc-x64"
        }
    ]
}
```

### **Priority 3: Simple Build Task**
```json
// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Build C++ Client",
            "type": "shell",
            "command": "${workspaceFolder}/client/build.bat",
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        }
    ]
}
```

---

## 🔧 **CRITICAL FIXES REQUIRED**

### **AESWrapper Key Size Fix**
```cpp
// In AESWrapper.h - change line 832:
static const unsigned int DEFAULT_KEYLENGTH = 32; // Was 16

// In AESWrapper.cpp - update constructor validation:
if (length != DEFAULT_KEYLENGTH)
    throw std::length_error("key length must be 32 bytes"); // Was 16
```

### **Python cksum Implementation**
```python
# Port the memcrc function to Python for server use
def calculate_linux_cksum(data: bytes) -> int:
    # Port the C++ crctab and memcrc logic
    # This ensures exact Linux cksum compatibility
```

---

## 📁 **KEY FILES TO REFERENCE**
- `Spesifications.md` - Source of truth for all requirements
- `All_code_Snippets_and_files_that_are_given_with_this_project.md` - Code foundation
- `server/tcp_server.py` - Current TCP server implementation (has critical bugs)
- `server/server.py` - Working HTTP server for comparison
- `server/enhanced_server.py` - Enhanced HTTP server with web interface
- `client/python_client.py` - Working HTTP Python client
- `client/enhanced_client.py` - Enhanced HTTP Python client
- `client/client.cpp` - HTTP C++ client (needs replacement with TCP version)
- `requirements.txt` - Python dependencies (PyCryptodome installed)
- `server/port.info` - Server port configuration (1256)

## 🔍 **CURRENT PROJECT STRUCTURE**
```
Secure_baclup_Server/
├── server/
│   ├── tcp_server.py          # NEW: Binary TCP server (has bugs)
│   ├── server.py              # Working HTTP server
│   ├── enhanced_server.py     # Enhanced HTTP server
│   └── port.info              # Port configuration
├── client/
│   ├── client.cpp             # HTTP C++ client (to be replaced)
│   ├── python_client.py       # Working HTTP Python client
│   └── enhanced_client.py     # Enhanced HTTP Python client
├── Spesifications.md          # SOURCE OF TRUTH
├── All_code_Snippets_and_files_that_are_given_with_this_project.md
├── requirements.txt
├── README.md
├── ENHANCEMENTS.md
└── test files and scripts
```

---

## 🚀 **NEXT CHAT STARTING POINT**

**"I have the VS Code-optimized implementation plan approved. Ready to start with Priority 1: Fix AESWrapper key size from 16 to 32 bytes, then port the Linux cksum algorithm to Python server. All changes must maintain specification compliance."**

### **Current Implementation Status**
- **✅ TCP Server**: Implemented but has critical bugs
- **✅ HTTP System**: Working baseline for comparison  
- **❌ C++ Client**: Not started (will use provided wrappers)
- **❌ Integration**: Not tested end-to-end

### **User Preferences Reminder**
- **Planning**: Detailed step-by-step plans with approval before coding
- **Repository**: Regular commits with descriptive messages
- **Specifications**: Absolute adherence, then eventual enhancement
- **Build**: Simple, working solutions over complex setups
- **Communication**: Ask for approval before major changes or implementations
- **Testing**: Suggest writing tests and running them to verify implementations

## 🧪 **TESTING STRATEGY**
### **Current Working Baseline**
- **HTTP Server**: `python server/server.py` (port 8080)
- **HTTP Client**: `python client/python_client.py http://localhost:8080 user password test_file.txt`
- **Test File Creation**: `python create_test_file.py test_file.txt 1024`
- **Status**: ✅ Working end-to-end

### **TCP Testing Plan**
1. **Server Testing**: `python server/tcp_server.py` (port 1256)
2. **Protocol Testing**: `python test_tcp_client.py` (basic registration test)
3. **Integration Testing**: C++ client ↔ Python TCP server
4. **Compliance Testing**: Verify against specifications.md requirements

## ⚠️ **KNOWN ISSUES IN CURRENT TCP SERVER**
1. **RSA Key Import**: Cannot handle 160-byte X.509 format from Crypto++
2. **Session Management**: Incorrect client_id lookup in file transfer
3. **Reconnection**: Not validating UUID from header properly
4. **cksum Algorithm**: Implemented but not verified against Linux cksum

## 🔄 **DEPENDENCIES & LIBRARIES**
### **Python (Server)**
- **Installed**: PyCryptodome, standard libraries
- **Required**: socket, struct, threading, os, uuid, logging

### **C++ (Client) - To Be Installed**
- **Required**: Crypto++, Boost.Asio
- **Compilers**: Visual Studio Build Tools 2019 (cl.exe) or MinGW (g++)
- **Detection**: Use environment detection script first

## 🔑 **CRITICAL SPECIFICATION DETAILS**
### **Protocol Message Codes**
- **Client Request Codes**: 1025 (Register), 1026 (Send Public Key), 1027 (Reconnect), 1028 (Send File), 1029 (CRC Valid), 1030 (CRC Invalid Resend), 1031 (CRC Invalid Abort)
- **Server Response Codes**: 1600 (Register Success), 1601 (Register Failed), 1602 (Public Key Received), 1603 (File Received), 1604 (Generic ACK), 1605 (Reconnect Approved), 1606 (Reconnect Denied), 1607 (Server Error)

### **Binary Protocol Requirements**
- **Version**: 3 (both client and server MUST report this)
- **Byte Order**: Little-endian for ALL multi-byte integers
- **String Fields**: 255 bytes, null-terminated, zero-padded
- **RSA Public Key**: Exactly 160 bytes in Crypto++ X.509 format
- **AES Key**: 256 bits (32 bytes) - override wrapper default of 16
- **Static IV**: Exactly 16 bytes of 0x00 for AES-CBC
- **File Transfer**: MUST set packet_number=1, total_packets=1 (no chunking)
- **Client ID**: Server MUST ignore this field in registration request (1025)
- **UUID Format**: 16 bytes binary in protocol, 32 lowercase hex chars in me.info

### **Configuration File Formats**
#### **transfer.info** (exactly 3 lines)
```
127.0.0.1:1234
Michael Jackson
C:\data\New_product_spec.docx
```
#### **me.info** (exactly 3 lines)
```
Michael Jackson
64f3f63985f04beb81a0e43321880182
MIGdMA0GCSqGSIb3DQEBA...
```

### **Error Handling Requirements**
- **Server Error Responses**: Print "server responded with an error" (exact format)
- **Retry Logic**: Up to 3 total attempts for requests and file transfers
- **CRC Mismatch**: Retry file transfer up to 2 more times, then send abort (1031)
- **Missing Config**: Server warns but doesn't crash on missing port.info

## 📊 **CURRENT WORKING SYSTEM DETAILS**
### **HTTP System (Working Baseline)**
- **Server**: Multi-threaded HTTP with Fernet encryption
- **Client**: HTTP POST with basic auth (user:password)
- **Features**: File deduplication, web interface at /files, logging
- **Storage**: UUID-based file naming in backups/ directory
- **Status**: ✅ Fully functional for comparison

### **TCP System (In Progress)**
- **Server**: Multi-threaded TCP with binary protocol
- **Status**: ❌ Has critical bugs but basic registration works
- **Test Results**: Registration (1025→1600) and duplicate rejection (1025→1601) working
- **Missing**: RSA key exchange, file transfer, CRC validation testing

## 🛠️ **IMPLEMENTATION HISTORY**
### **What Was Already Implemented**
1. **TCP Server Structure**: Complete message parsing, threading, logging
2. **Protocol Handlers**: All message codes implemented but buggy
3. **Binary Protocol**: Request/response header parsing working
4. **Registration Flow**: Basic client registration with UUID generation
5. **Port Configuration**: Reads from port.info, defaults to 1256
6. **Test Client**: Basic Python test client for protocol verification

### **What Needs Immediate Fixing**
1. **RSA Key Handling**: PyCryptodome can't import 160-byte X.509 format
2. **Session Management**: File transfer uses wrong client lookup
3. **AES Key Size**: Server generates 32-byte keys but client wrapper uses 16
4. **cksum Verification**: Algorithm implemented but not tested against Linux

## 🎯 **SUCCESS CRITERIA**
### **Phase 2 Complete When:**
- ✅ Linux cksum algorithm verified against actual cksum command
- ✅ Server handles 160-byte RSA public keys from C++ client
- ✅ All protocol message flows tested and working
- ✅ Session management uses correct client_id mapping

### **Phase 3 Complete When:**
- ✅ C++ client compiles with VS Code build system
- ✅ AESWrapper uses 32-byte keys (not 16-byte)
- ✅ Configuration files (transfer.info, me.info) working
- ✅ Binary protocol client communicates with server

### **Phase 4 Complete When:**
- ✅ End-to-end file transfer working (C++ client ↔ Python server)
- ✅ CRC validation and retry logic functional
- ✅ All specification requirements verified
- ✅ Integration tests passing
