#!/usr/bin/env python3
"""
Simple TCP client to test the binary protocol server
This is a basic test client to verify server functionality
"""

import socket
import struct

# Protocol Constants
PROTOCOL_VERSION = 3
REQ_REGISTER = 1025
RESP_REGISTER_SUCCESS = 1600
RESP_REGISTER_FAILED = 1601

REQUEST_HEADER_FORMAT = '<16sBHI'  # client_id(16), version(1), code(2), payload_size(4)
RESPONSE_HEADER_FORMAT = '<BHI'    # version(1), code(2), payload_size(4)

def pack_request_header(client_id: bytes, code: int, payload_size: int) -> bytes:
    """Pack request header into binary format"""
    return struct.pack(REQUEST_HEADER_FORMAT, client_id, PROTOCOL_VERSION, code, payload_size)

def unpack_response_header(data: bytes) -> tuple:
    """Unpack response header from binary format"""
    return struct.unpack(RESPONSE_HEADER_FORMAT, data[:7])

def pad_string(s: str, size: int) -> bytes:
    """Pad string to specified size with null termination"""
    if len(s) >= size:
        s = s[:size-1]  # Truncate if too long
    return s.encode('ascii') + b'\x00' * (size - len(s))

def test_registration():
    """Test client registration"""
    print("Testing TCP Binary Protocol Server...")
    
    # Connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', 1256))
        print("✓ Connected to server")
        
        # Test registration
        username = "testuser"
        client_id = b'\x00' * 16  # Dummy client ID (ignored for registration)
        
        # Prepare registration payload
        payload = pad_string(username, 255)
        
        # Send registration request
        header = pack_request_header(client_id, REQ_REGISTER, len(payload))
        request = header + payload
        
        sock.sendall(request)
        print(f"✓ Sent registration request for username: {username}")
        
        # Receive response header
        response_header = sock.recv(7)
        if len(response_header) < 7:
            print("✗ Failed to receive complete response header")
            return
        
        version, code, payload_size = unpack_response_header(response_header)
        print(f"✓ Received response: version={version}, code={code}, payload_size={payload_size}")
        
        # Receive payload if present
        if payload_size > 0:
            response_payload = sock.recv(payload_size)
            if code == RESP_REGISTER_SUCCESS:
                received_uuid = response_payload[:16]
                print(f"✓ Registration successful! UUID: {received_uuid.hex()}")
            else:
                print(f"✗ Registration failed with code: {code}")
        else:
            if code == RESP_REGISTER_FAILED:
                print("✗ Registration failed (no payload)")
            else:
                print(f"? Unexpected response code: {code}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        sock.close()

def test_duplicate_registration():
    """Test duplicate username registration"""
    print("\nTesting duplicate registration...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', 1256))
        
        # Try to register same username again
        username = "testuser"
        client_id = b'\x00' * 16
        payload = pad_string(username, 255)
        header = pack_request_header(client_id, REQ_REGISTER, len(payload))
        request = header + payload
        
        sock.sendall(request)
        print(f"✓ Sent duplicate registration for: {username}")
        
        # Receive response
        response_header = sock.recv(7)
        version, code, payload_size = unpack_response_header(response_header)
        
        if code == RESP_REGISTER_FAILED:
            print("✓ Duplicate registration correctly rejected")
        else:
            print(f"✗ Unexpected response to duplicate registration: {code}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    test_registration()
    test_duplicate_registration()
    print("\nBasic TCP protocol test completed!")
