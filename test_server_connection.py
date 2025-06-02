#!/usr/bin/env python3
"""
Simple test to verify the server is responding correctly
"""

import socket
import struct
import time

def test_server_connection():
    """Test basic connection to the server"""
    try:
        # Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        
        print("Attempting to connect to server on localhost:1256...")
        sock.connect(('localhost', 1256))
        print("✅ Successfully connected to server!")
        
        # Try to send a simple invalid request to see server response
        # This should trigger an error response from the server
        invalid_data = b"INVALID_REQUEST_TEST"
        sock.send(invalid_data)
        
        # Try to read response (if any)
        try:
            response = sock.recv(1024)
            if response:
                print(f"✅ Server responded with {len(response)} bytes")
                print(f"Response: {response[:50]}...")  # Show first 50 bytes
            else:
                print("✅ Server closed connection (expected for invalid request)")
        except socket.timeout:
            print("✅ Server didn't respond to invalid request (expected)")
        
        sock.close()
        print("✅ Connection test completed successfully!")
        return True
        
    except ConnectionRefusedError:
        print("❌ Connection refused - server not running on port 1256")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing server connection...")
    print("=" * 40)
    success = test_server_connection()
    
    if success:
        print("\n🎉 Server is running and accepting connections!")
    else:
        print("\n💥 Server connection test failed!")
