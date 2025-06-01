#!/usr/bin/env python3
"""
TCP Binary Protocol Server - Specification Compliant
Implements the binary TCP protocol as defined in Spesifications.md
"""

import socket
import struct
import threading
import os
import uuid
import logging
from typing import Dict, Optional, Tuple, Any
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256

# Protocol Constants
PROTOCOL_VERSION = 3
DEFAULT_PORT = 1256

# Request Codes (Client -> Server)
REQ_REGISTER = 1025
REQ_SEND_PUBLIC_KEY = 1026
REQ_RECONNECT = 1027
REQ_SEND_FILE = 1028
REQ_CRC_VALID = 1029
REQ_CRC_INVALID_RESEND = 1030
REQ_CRC_INVALID_ABORT = 1031

# Response Codes (Server -> Client)
RESP_REGISTER_SUCCESS = 1600
RESP_REGISTER_FAILED = 1601
RESP_PUBLIC_KEY_RECEIVED = 1602
RESP_FILE_RECEIVED = 1603
RESP_GENERIC_ACK = 1604
RESP_RECONNECT_APPROVED = 1605
RESP_RECONNECT_DENIED = 1606
RESP_SERVER_ERROR = 1607

# Field Sizes
CLIENT_ID_SIZE = 16
USERNAME_SIZE = 255
FILENAME_SIZE = 255
RSA_PUBLIC_KEY_SIZE = 160
AES_KEY_SIZE = 32  # 256 bits
AES_IV_SIZE = 16

# Message Header Structures
REQUEST_HEADER_FORMAT = '<16sBHI'  # client_id(16), version(1), code(2), payload_size(4)
RESPONSE_HEADER_FORMAT = '<BHI'    # version(1), code(2), payload_size(4)

REQUEST_HEADER_SIZE = struct.calcsize(REQUEST_HEADER_FORMAT)
RESPONSE_HEADER_SIZE = struct.calcsize(RESPONSE_HEADER_FORMAT)

class ClientSession:
    """Represents an active client session"""
    def __init__(self, client_id: bytes, username: str):
        self.client_id = client_id
        self.username = username
        self.rsa_public_key: Optional[bytes] = None
        self.aes_key: Optional[bytes] = None
        self.last_seen = None

class TCPServer:
    """Binary TCP Protocol Server"""
    
    def __init__(self):
        self.port = self._read_port()
        self.clients: Dict[bytes, ClientSession] = {}  # client_id -> session
        self.usernames: Dict[str, bytes] = {}  # username -> client_id
        self.files_dir = "server_files"
        self.lock = threading.Lock()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tcp_server.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create files directory
        os.makedirs(self.files_dir, exist_ok=True)
        
    def _read_port(self) -> int:
        """Read port from port.info file or use default"""
        try:
            with open('port.info', 'r') as f:
                port = int(f.read().strip())
                return port
        except (FileNotFoundError, ValueError) as e:
            print(f"Warning: port.info not found or invalid, using default port {DEFAULT_PORT}")
            return DEFAULT_PORT
    
    def _pack_response_header(self, code: int, payload_size: int) -> bytes:
        """Pack response header into binary format"""
        return struct.pack(RESPONSE_HEADER_FORMAT, PROTOCOL_VERSION, code, payload_size)
    
    def _unpack_request_header(self, data: bytes) -> Tuple[bytes, int, int, int]:
        """Unpack request header from binary format"""
        if len(data) < REQUEST_HEADER_SIZE:
            raise ValueError("Insufficient data for request header")
        
        client_id, version, code, payload_size = struct.unpack(REQUEST_HEADER_FORMAT, data[:REQUEST_HEADER_SIZE])
        return client_id, version, code, payload_size
    
    def _send_response(self, conn: socket.socket, code: int, payload: bytes = b'') -> None:
        """Send binary response to client"""
        header = self._pack_response_header(code, len(payload))
        response = header + payload
        conn.sendall(response)
        self.logger.info(f"Sent response code {code} with {len(payload)} bytes payload")
    
    def _recv_exact(self, conn: socket.socket, size: int) -> bytes:
        """Receive exactly 'size' bytes from socket"""
        data = b''
        while len(data) < size:
            chunk = conn.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed unexpectedly")
            data += chunk
        return data
    
    def _pad_string(self, s: str, size: int) -> bytes:
        """Pad string to specified size with null termination"""
        if len(s) >= size:
            s = s[:size-1]  # Truncate if too long
        return s.encode('ascii') + b'\x00' * (size - len(s))
    
    def _unpad_string(self, data: bytes) -> str:
        """Extract null-terminated string from padded bytes"""
        null_pos = data.find(b'\x00')
        if null_pos == -1:
            return data.decode('ascii')
        return data[:null_pos].decode('ascii')
    
    def _generate_uuid(self) -> bytes:
        """Generate 16-byte UUID"""
        return uuid.uuid4().bytes
    
    def _calculate_cksum(self, data: bytes) -> int:
        """Calculate Linux cksum compatible checksum"""
        # CRC table for polynomial 0x04C11DB7
        crc_table = []
        for i in range(256):
            crc = i << 24
            for _ in range(8):
                if crc & 0x80000000:
                    crc = (crc << 1) ^ 0x04C11DB7
                else:
                    crc = crc << 1
                crc &= 0xFFFFFFFF
            crc_table.append(crc)
        
        # Calculate CRC
        crc = 0x00000000
        
        # Process file data
        for byte in data:
            crc = ((crc << 8) ^ crc_table[((crc >> 24) ^ byte) & 0xFF]) & 0xFFFFFFFF
        
        # Process file length
        length = len(data)
        while length > 0:
            crc = ((crc << 8) ^ crc_table[((crc >> 24) ^ (length & 0xFF)) & 0xFF]) & 0xFFFFFFFF
            length >>= 8
        
        # Final step: bitwise NOT
        crc = (~crc) & 0xFFFFFFFF
        return crc
    
    def _handle_client(self, conn: socket.socket, address: Tuple[str, int]) -> None:
        """Handle individual client connection"""
        try:
            while True:
                # Receive request header
                header_data = self._recv_exact(conn, REQUEST_HEADER_SIZE)
                client_id, version, code, payload_size = self._unpack_request_header(header_data)

                self.logger.info(f"Received request: version={version}, code={code}, payload_size={payload_size}")

                # Validate protocol version
                if version != PROTOCOL_VERSION:
                    self.logger.warning(f"Invalid protocol version: {version}")
                    self._send_response(conn, RESP_SERVER_ERROR)
                    continue

                # Receive payload if present
                payload = b''
                if payload_size > 0:
                    payload = self._recv_exact(conn, payload_size)

                # Route request to appropriate handler
                if code == REQ_REGISTER:
                    self._handle_register(conn, client_id, payload)
                elif code == REQ_SEND_PUBLIC_KEY:
                    self._handle_send_public_key(conn, client_id, payload)
                elif code == REQ_RECONNECT:
                    self._handle_reconnect(conn, client_id, payload)
                elif code == REQ_SEND_FILE:
                    self._handle_send_file(conn, client_id, payload)
                elif code == REQ_CRC_VALID:
                    self._handle_crc_valid(conn, client_id, payload)
                elif code == REQ_CRC_INVALID_RESEND:
                    self._handle_crc_invalid_resend(conn, client_id, payload)
                elif code == REQ_CRC_INVALID_ABORT:
                    self._handle_crc_invalid_abort(conn, client_id, payload)
                else:
                    self.logger.warning(f"Unknown request code: {code}")
                    self._send_response(conn, RESP_SERVER_ERROR)

        except ConnectionError:
            self.logger.info(f"Client {address} disconnected")
        except Exception as e:
            self.logger.error(f"Error handling client {address}: {e}")
        finally:
            conn.close()

    def _handle_register(self, conn: socket.socket, client_id: bytes, payload: bytes) -> None:
        """Handle registration request (1025)"""
        if len(payload) < USERNAME_SIZE:
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        username = self._unpad_string(payload[:USERNAME_SIZE])
        self.logger.info(f"Registration request for username: {username}")

        with self.lock:
            # Check if username already exists
            if username in self.usernames:
                self.logger.warning(f"Username {username} already exists")
                self._send_response(conn, RESP_REGISTER_FAILED)
                return

            # Generate new UUID for client
            new_client_id = self._generate_uuid()

            # Create client session
            session = ClientSession(new_client_id, username)
            self.clients[new_client_id] = session
            self.usernames[username] = new_client_id

            self.logger.info(f"Registered new client: {username} with UUID: {new_client_id.hex()}")

            # Send success response with UUID
            self._send_response(conn, RESP_REGISTER_SUCCESS, new_client_id)

    def _handle_send_public_key(self, conn: socket.socket, client_id: bytes, payload: bytes) -> None:
        """Handle public key submission (1026)"""
        if len(payload) < USERNAME_SIZE + RSA_PUBLIC_KEY_SIZE:
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        username = self._unpad_string(payload[:USERNAME_SIZE])
        public_key = payload[USERNAME_SIZE:USERNAME_SIZE + RSA_PUBLIC_KEY_SIZE]

        self.logger.info(f"Public key received from: {username}")

        with self.lock:
            # Find client by username
            if username not in self.usernames:
                self.logger.warning(f"Unknown username: {username}")
                self._send_response(conn, RESP_SERVER_ERROR)
                return

            actual_client_id = self.usernames[username]
            session = self.clients[actual_client_id]

            # Store public key
            session.rsa_public_key = public_key

            # Generate AES session key
            aes_key = get_random_bytes(AES_KEY_SIZE)
            session.aes_key = aes_key

            # Encrypt AES key with client's RSA public key
            try:
                # Import RSA public key (assuming X.509 format)
                rsa_key = RSA.import_key(public_key)
                cipher_rsa = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA256)
                encrypted_aes_key = cipher_rsa.encrypt(aes_key)

                # Send response with encrypted AES key
                response_payload = actual_client_id + encrypted_aes_key
                self._send_response(conn, RESP_PUBLIC_KEY_RECEIVED, response_payload)

                self.logger.info(f"AES key generated and sent to {username}")

            except Exception as e:
                self.logger.error(f"Error encrypting AES key: {e}")
                self._send_response(conn, RESP_SERVER_ERROR)

    def _handle_reconnect(self, conn: socket.socket, client_id: bytes, payload: bytes) -> None:
        """Handle reconnection request (1027)"""
        if len(payload) < USERNAME_SIZE:
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        username = self._unpad_string(payload[:USERNAME_SIZE])
        self.logger.info(f"Reconnection request for username: {username}")

        with self.lock:
            # Verify client exists and has public key
            if username not in self.usernames:
                self.logger.warning(f"Unknown username for reconnection: {username}")
                self._send_response(conn, RESP_RECONNECT_DENIED, client_id)
                return

            actual_client_id = self.usernames[username]
            session = self.clients[actual_client_id]

            if session.rsa_public_key is None:
                self.logger.warning(f"No public key for reconnecting user: {username}")
                self._send_response(conn, RESP_RECONNECT_DENIED, actual_client_id)
                return

            # Generate NEW AES session key (always new on reconnection)
            aes_key = get_random_bytes(AES_KEY_SIZE)
            session.aes_key = aes_key

            # Encrypt AES key with stored public key
            try:
                rsa_key = RSA.import_key(session.rsa_public_key)
                cipher_rsa = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA256)
                encrypted_aes_key = cipher_rsa.encrypt(aes_key)

                # Send approval with encrypted AES key
                response_payload = actual_client_id + encrypted_aes_key
                self._send_response(conn, RESP_RECONNECT_APPROVED, response_payload)

                self.logger.info(f"Reconnection approved for {username}")

            except Exception as e:
                self.logger.error(f"Error encrypting AES key for reconnection: {e}")
                self._send_response(conn, RESP_RECONNECT_DENIED, actual_client_id)

    def _handle_send_file(self, conn: socket.socket, client_id: bytes, payload: bytes) -> None:
        """Handle file transfer request (1028)"""
        # Parse file transfer payload
        if len(payload) < 4 + 4 + 2 + 2 + FILENAME_SIZE:
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        offset = 0
        content_size = struct.unpack('<I', payload[offset:offset+4])[0]
        offset += 4
        orig_file_size = struct.unpack('<I', payload[offset:offset+4])[0]
        offset += 4
        packet_number = struct.unpack('<H', payload[offset:offset+2])[0]
        offset += 2
        total_packets = struct.unpack('<H', payload[offset:offset+2])[0]
        offset += 2
        filename = self._unpad_string(payload[offset:offset+FILENAME_SIZE])
        offset += FILENAME_SIZE

        encrypted_file_data = payload[offset:]

        self.logger.info(f"File transfer: {filename}, size: {content_size}, original: {orig_file_size}")

        # Validate single packet transfer (per specification)
        if packet_number != 1 or total_packets != 1:
            self.logger.warning(f"Invalid packet numbers: {packet_number}/{total_packets}")
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        with self.lock:
            # Find client session
            session = None
            for sess in self.clients.values():
                if sess.aes_key is not None:  # Find active session
                    session = sess
                    break

            if session is None or session.aes_key is None:
                self.logger.warning("No active session with AES key")
                self._send_response(conn, RESP_SERVER_ERROR)
                return

            try:
                # Decrypt file using AES-CBC with zero IV
                iv = b'\x00' * AES_IV_SIZE
                cipher_aes = AES.new(session.aes_key, AES.MODE_CBC, iv)
                decrypted_data = cipher_aes.decrypt(encrypted_file_data)

                # Remove PKCS7 padding
                padding_length = decrypted_data[-1]
                decrypted_data = decrypted_data[:-padding_length]

                # Calculate CRC of decrypted data
                calculated_crc = self._calculate_cksum(decrypted_data)

                # Save file with UUID-based naming
                safe_filename = f"{session.client_id.hex()}_{filename}"
                file_path = os.path.join(self.files_dir, safe_filename)

                with open(file_path, 'wb') as f:
                    f.write(decrypted_data)

                self.logger.info(f"File saved: {file_path}, CRC: {calculated_crc:08x}")

                # Send response with CRC
                response_payload = (session.client_id +
                                  struct.pack('<I', content_size) +
                                  self._pad_string(filename, FILENAME_SIZE) +
                                  struct.pack('<I', calculated_crc))

                self._send_response(conn, RESP_FILE_RECEIVED, response_payload)

            except Exception as e:
                self.logger.error(f"Error processing file: {e}")
                self._send_response(conn, RESP_SERVER_ERROR)

    def _handle_crc_valid(self, conn: socket.socket, client_id: bytes, payload: bytes) -> None:
        """Handle CRC valid confirmation (1029)"""
        if len(payload) < FILENAME_SIZE:
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        filename = self._unpad_string(payload[:FILENAME_SIZE])
        self.logger.info(f"CRC validation successful for: {filename}")

        # Send acknowledgement
        self._send_response(conn, RESP_GENERIC_ACK, client_id)

    def _handle_crc_invalid_resend(self, conn: socket.socket, client_id: bytes, payload: bytes) -> None:
        """Handle CRC invalid, resending (1030)"""
        if len(payload) < FILENAME_SIZE:
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        filename = self._unpad_string(payload[:FILENAME_SIZE])
        self.logger.info(f"CRC validation failed, client will resend: {filename}")

        # Prepare for file retransmission - no response needed

    def _handle_crc_invalid_abort(self, conn: socket.socket, client_id: bytes, payload: bytes) -> None:
        """Handle CRC invalid, aborting (1031)"""
        if len(payload) < FILENAME_SIZE:
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        filename = self._unpad_string(payload[:FILENAME_SIZE])
        self.logger.info(f"CRC validation failed 3 times, client aborting: {filename}")

        # Send acknowledgement
        self._send_response(conn, RESP_GENERIC_ACK, client_id)

    def start(self):
        """Start the TCP server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind(('0.0.0.0', self.port))
            server_socket.listen(5)

            self.logger.info(f"TCP Server started on port {self.port}")
            self.logger.info(f"Files will be stored in: {os.path.abspath(self.files_dir)}")
            print(f"TCP Binary Protocol Server listening on port {self.port}")
            print(f"Press Ctrl+C to stop the server")

            while True:
                client_socket, client_address = server_socket.accept()
                self.logger.info(f"New connection from {client_address}")

                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()

        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            server_socket.close()
            self.logger.info("Server stopped")

def main():
    """Main entry point"""
    server = TCPServer()
    server.start()

if __name__ == "__main__":
    main()
