#!/usr/bin/env python3
"""
Comprehensive integration tests for the secure file backup system.
Tests end-to-end functionality between C++ client and Python server.
"""

import os
import sys
import time
import subprocess
import threading
import tempfile
import shutil
import socket
from pathlib import Path

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from tcp_server import TCPServer

class ClientServerIntegrationTest:
    def __init__(self):
        self.test_dir = Path(__file__).parent.parent.parent
        self.server_process = None
        self.server_thread = None
        self.server = None
        self.test_port = 12560  # Use different port for testing
        self.tests_run = 0
        self.tests_passed = 0
        
    def assert_test(self, condition, test_name):
        """Assert test condition and track results"""
        self.tests_run += 1
        if condition:
            self.tests_passed += 1
            print(f"✅ PASS: {test_name}")
            return True
        else:
            print(f"❌ FAIL: {test_name}")
            return False
    
    def setup_test_environment(self):
        """Set up test environment with temporary files"""
        print("\n=== Setting Up Test Environment ===")
        
        # Create test port configuration
        test_port_file = self.test_dir / "server" / "port.info"
        with open(test_port_file, 'w') as f:
            f.write(str(self.test_port))
        
        client_port_file = self.test_dir / "client" / "port.info"
        with open(client_port_file, 'w') as f:
            f.write(str(self.test_port))
        
        # Create test files directory
        test_files_dir = Path(__file__).parent.parent / "fixtures" / "test_files"
        test_files_dir.mkdir(parents=True, exist_ok=True)
        
        # Create various test files
        self.create_test_files(test_files_dir)
        
        print(f"✅ Test environment set up on port {self.test_port}")
        
    def create_test_files(self, test_dir):
        """Create various test files for testing"""
        
        # Small text file
        small_file = test_dir / "small_test.txt"
        with open(small_file, 'w') as f:
            f.write("This is a small test file.\nWith multiple lines.\nFor testing purposes.\n")
        
        # Medium text file
        medium_file = test_dir / "medium_test.txt"
        with open(medium_file, 'w') as f:
            for i in range(100):
                f.write(f"Line {i+1}: This is a medium-sized test file for backup testing.\n")
        
        # Binary file
        binary_file = test_dir / "binary_test.bin"
        with open(binary_file, 'wb') as f:
            for i in range(256):
                f.write(bytes([i]))
        
        # Large text file (1MB)
        large_file = test_dir / "large_test.txt"
        with open(large_file, 'w') as f:
            content = "This is a large test file. " * 100 + "\n"
            for i in range(1000):
                f.write(f"Block {i+1}: {content}")
        
        # Empty file
        empty_file = test_dir / "empty_test.txt"
        empty_file.touch()
        
        print(f"✅ Created test files in {test_dir}")
    
    def start_server(self):
        """Start the TCP server in a separate thread"""
        print("\n=== Starting TCP Server ===")
        
        def run_server():
            try:
                self.server = TCPServer(debug_mode=True, verbose=True)
                self.server.start()
            except Exception as e:
                print(f"❌ Server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Test server connection
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', self.test_port))
            sock.close()
            
            if result == 0:
                print(f"✅ Server started successfully on port {self.test_port}")
                return True
            else:
                print(f"❌ Server not responding on port {self.test_port}")
                return False
        except Exception as e:
            print(f"❌ Server connection test failed: {e}")
            return False
    
    def stop_server(self):
        """Stop the TCP server"""
        if self.server:
            try:
                self.server.shutdown()
                print("✅ Server stopped")
            except:
                pass
    
    def build_client(self):
        """Build the C++ client"""
        print("\n=== Building C++ Client ===")
        
        client_dir = self.test_dir / "client"
        build_script = client_dir / "build_vs2022.bat"
        
        if not build_script.exists():
            print("❌ Build script not found")
            return False
        
        try:
            # Run build script
            result = subprocess.run(
                [str(build_script)],
                cwd=str(client_dir),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Check if executable was created
            exe_file = client_dir / "tcp_client.exe"
            if exe_file.exists():
                print("✅ Client built successfully")
                return True
            else:
                print("❌ Client build failed - executable not found")
                print(f"Build output: {result.stdout}")
                print(f"Build errors: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Client build timed out")
            return False
        except Exception as e:
            print(f"❌ Client build error: {e}")
            return False
    
    def test_file_transfer(self, test_file_path):
        """Test file transfer with the client"""
        print(f"\n=== Testing File Transfer: {test_file_path.name} ===")
        
        client_exe = self.test_dir / "client" / "tcp_client.exe"
        if not client_exe.exists():
            return self.assert_test(False, f"Client executable not found for {test_file_path.name}")
        
        # Copy test file to client directory
        client_test_file = self.test_dir / "client" / "test_file.txt"
        shutil.copy2(test_file_path, client_test_file)
        
        try:
            # Run client
            result = subprocess.run(
                [str(client_exe)],
                cwd=str(self.test_dir / "client"),
                capture_output=True,
                text=True,
                timeout=30,
                input="\n"  # Press enter to continue
            )
            
            # Check if transfer was successful
            success_indicators = [
                "File transfer completed successfully",
                "✅",
                "SUCCESS"
            ]
            
            output = result.stdout + result.stderr
            transfer_successful = any(indicator in output for indicator in success_indicators)
            
            if transfer_successful:
                # Verify file was created on server
                server_files_dir = self.test_dir / "server" / "server_files"
                if server_files_dir.exists():
                    server_files = list(server_files_dir.glob("*test_file.txt"))
                    file_created = len(server_files) > 0
                    return self.assert_test(file_created, f"File transfer and storage: {test_file_path.name}")
                else:
                    return self.assert_test(False, f"Server files directory not found for {test_file_path.name}")
            else:
                print(f"Client output: {output}")
                return self.assert_test(False, f"File transfer failed: {test_file_path.name}")
                
        except subprocess.TimeoutExpired:
            return self.assert_test(False, f"File transfer timed out: {test_file_path.name}")
        except Exception as e:
            return self.assert_test(False, f"File transfer error: {test_file_path.name} - {e}")
        finally:
            # Clean up
            if client_test_file.exists():
                client_test_file.unlink()
    
    def test_multiple_transfers(self):
        """Test multiple file transfers"""
        print("\n=== Testing Multiple File Transfers ===")
        
        test_files_dir = Path(__file__).parent.parent / "fixtures" / "test_files"
        test_files = [
            test_files_dir / "small_test.txt",
            test_files_dir / "medium_test.txt",
            test_files_dir / "binary_test.bin"
        ]
        
        successful_transfers = 0
        for test_file in test_files:
            if test_file.exists():
                if self.test_file_transfer(test_file):
                    successful_transfers += 1
                time.sleep(1)  # Brief pause between transfers
        
        return self.assert_test(
            successful_transfers == len(test_files),
            f"Multiple file transfers ({successful_transfers}/{len(test_files)} successful)"
        )
    
    def test_server_stats(self):
        """Test server statistics and monitoring"""
        print("\n=== Testing Server Statistics ===")
        
        if self.server:
            try:
                stats = self.server.get_debug_info()
                has_stats = "Server Statistics" in stats or "clients" in stats.lower()
                return self.assert_test(has_stats, "Server provides statistics")
            except Exception as e:
                return self.assert_test(False, f"Server stats error: {e}")
        else:
            return self.assert_test(False, "Server not available for stats test")
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        print("\n=== Cleaning Up Test Environment ===")
        
        # Stop server
        self.stop_server()
        
        # Clean up test files
        try:
            test_files_dir = Path(__file__).parent.parent / "fixtures" / "test_files"
            if test_files_dir.exists():
                for file in test_files_dir.glob("*test*"):
                    file.unlink()
            
            # Clean up server files
            server_files_dir = self.test_dir / "server" / "server_files"
            if server_files_dir.exists():
                for file in server_files_dir.glob("*test_file.txt"):
                    file.unlink()
            
            print("✅ Test environment cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🔗 Client-Server Integration Tests")
        print("==================================")
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Build client
            if not self.build_client():
                print("❌ Cannot proceed without client build")
                return
            
            # Start server
            if not self.start_server():
                print("❌ Cannot proceed without server")
                return
            
            # Run tests
            test_files_dir = Path(__file__).parent.parent / "fixtures" / "test_files"
            
            # Test individual file transfers
            self.test_file_transfer(test_files_dir / "small_test.txt")
            self.test_file_transfer(test_files_dir / "binary_test.bin")
            
            # Test multiple transfers
            self.test_multiple_transfers()
            
            # Test server functionality
            self.test_server_stats()
            
        finally:
            # Always cleanup
            self.cleanup_test_environment()
        
        # Print results
        print(f"\n📊 Integration Test Results:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {100.0 * self.tests_passed / self.tests_run if self.tests_run > 0 else 0:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All integration tests passed!")
        else:
            print("❌ Some integration tests failed!")

if __name__ == "__main__":
    test = ClientServerIntegrationTest()
    test.run_all_tests()
