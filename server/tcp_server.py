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
import time
import argparse
from datetime import datetime
from collections import defaultdict
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

class ServerStats:
    """Track server statistics for monitoring and debugging"""
    def __init__(self):
        self.start_time = time.time()
        self.connections_total = 0
        self.connections_active = 0
        self.requests_by_type = defaultdict(int)
        self.responses_by_type = defaultdict(int)
        self.files_received = 0
        self.bytes_received = 0
        self.errors_count = 0
        self.clients_registered = 0
        self.clients_reconnected = 0
        self.crc_validations = {'valid': 0, 'invalid': 0, 'aborted': 0}

    def log_connection(self):
        self.connections_total += 1
        self.connections_active += 1

    def log_disconnection(self):
        self.connections_active = max(0, self.connections_active - 1)

    def log_request(self, code: int):
        self.requests_by_type[code] += 1

    def log_response(self, code: int):
        self.responses_by_type[code] += 1

    def log_file_received(self, size: int):
        self.files_received += 1
        self.bytes_received += size

    def log_error(self):
        self.errors_count += 1

    def log_registration(self):
        self.clients_registered += 1

    def log_reconnection(self):
        self.clients_reconnected += 1

    def log_crc_result(self, result: str):
        if result in self.crc_validations:
            self.crc_validations[result] += 1

    def get_uptime(self) -> float:
        return time.time() - self.start_time

    def get_summary(self) -> str:
        uptime = self.get_uptime()
        return f"""
=== SERVER STATISTICS ===
Uptime: {uptime:.1f} seconds ({uptime/60:.1f} minutes)
Connections: {self.connections_total} total, {self.connections_active} active
Clients: {self.clients_registered} registered, {self.clients_reconnected} reconnected
Files: {self.files_received} received, {self.bytes_received:,} bytes total
CRC: {self.crc_validations['valid']} valid, {self.crc_validations['invalid']} invalid, {self.crc_validations['aborted']} aborted
Errors: {self.errors_count}
Request Types: {dict(self.requests_by_type)}
Response Types: {dict(self.responses_by_type)}
========================
"""

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

    def __init__(self, debug_mode: bool = False, verbose: bool = False):
        self.port = self._read_port()
        self.clients: Dict[bytes, ClientSession] = {}  # client_id -> session
        self.usernames: Dict[str, bytes] = {}  # username -> client_id
        self.files_dir = "server_files"
        self.lock = threading.Lock()
        self.debug_mode = debug_mode
        self.verbose = verbose
        self.stats = ServerStats()

        # Setup logging with debug level if requested
        log_level = logging.DEBUG if debug_mode else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tcp_server.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Create files directory
        os.makedirs(self.files_dir, exist_ok=True)

        if debug_mode:
            self.logger.debug("🐛 DEBUG MODE ENABLED")
        if verbose:
            self.logger.info("📊 VERBOSE MODE ENABLED")
        
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

        # Track stats
        self.stats.log_response(code)

        if self.verbose:
            self.logger.info(f"📤 Sent response code {code} with {len(payload)} bytes payload")
        elif self.debug_mode:
            self.logger.debug(f"Response: code={code}, payload_size={len(payload)}")
        else:
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
        """Calculate Linux cksum compatible checksum - ported from provided C++ memcrc function"""
        # CRC table from provided C++ code (crctab[0] - first 256 entries)
        # This is the exact table used by Linux cksum for polynomial 0x04C11DB7
        crctab = [
            0x00000000, 0x04c11db7, 0x09823b6e, 0x0d4326d9, 0x130476dc, 0x17c56b6b,
            0x1a864db2, 0x1e475005, 0x2608edb8, 0x22c9f00f, 0x2f8ad6d6, 0x2b4bcb61,
            0x350c9b64, 0x31cd86d3, 0x3c8ea00a, 0x384fbdbd, 0x4c11db70, 0x48d0c6c7,
            0x4593e01e, 0x4152fda9, 0x5f15adac, 0x5bd4b01b, 0x569796c2, 0x52568b75,
            0x6a1936c8, 0x6ed82b7f, 0x639b0da6, 0x675a1011, 0x791d4014, 0x7ddc5da3,
            0x709f7b7a, 0x745e66cd, 0x9823b6e0, 0x9ce2ab57, 0x91a18d8e, 0x95609039,
            0x8b27c03c, 0x8fe6dd8b, 0x82a5fb52, 0x8664e6e5, 0xbe2b5b58, 0xbaea46ef,
            0xb7a96036, 0xb3687d81, 0xad2f2d84, 0xa9ee3033, 0xa4ad16ea, 0xa06c0b5d,
            0xd4326d90, 0xd0f37027, 0xddb056fe, 0xd9714b49, 0xc7361b4c, 0xc3f706fb,
            0xceb42022, 0xca753d95, 0xf23a8028, 0xf6fb9d9f, 0xfbb8bb46, 0xff79a6f1,
            0xe13ef6f4, 0xe5ffeb43, 0xe8bccd9a, 0xec7dd02d, 0x34867077, 0x30476dc0,
            0x3d044b19, 0x39c556ae, 0x278206ab, 0x23431b1c, 0x2e003dc5, 0x2ac12072,
            0x128e9dcf, 0x164f8078, 0x1b0ca6a1, 0x1fcdbb16, 0x018aeb13, 0x054bf6a4,
            0x0808d07d, 0x0cc9cdca, 0x7897ab07, 0x7c56b6b0, 0x71159069, 0x75d48dde,
            0x6b93dddb, 0x6f52c06c, 0x6211e6b5, 0x66d0fb02, 0x5e9f46bf, 0x5a5e5b08,
            0x571d7dd1, 0x53dc6066, 0x4d9b3063, 0x495a2dd4, 0x44190b0d, 0x40d816ba,
            0xaca5c697, 0xa864db20, 0xa527fdf9, 0xa1e6e04e, 0xbfa1b04b, 0xbb60adfc,
            0xb6238b25, 0xb2e29692, 0x8aad2b2f, 0x8e6c3698, 0x832f1041, 0x87ee0df6,
            0x99a95df3, 0x9d684044, 0x902b669d, 0x94ea7b2a, 0xe0b41de7, 0xe4750050,
            0xe9362689, 0xedf73b3e, 0xf3b06b3b, 0xf771768c, 0xfa325055, 0xfef34de2,
            0xc6bcf05f, 0xc27dede8, 0xcf3ecb31, 0xcbffd686, 0xd5b88683, 0xd1799b34,
            0xdc3abded, 0xd8fba05a, 0x690ce0ee, 0x6dcdfd59, 0x608edb80, 0x644fc637,
            0x7a089632, 0x7ec98b85, 0x738aad5c, 0x774bb0eb, 0x4f040d56, 0x4bc510e1,
            0x46863638, 0x42472b8f, 0x5c007b8a, 0x58c1663d, 0x558240e4, 0x51435d53,
            0x251d3b9e, 0x21dc2629, 0x2c9f00f0, 0x285e1d47, 0x36194d42, 0x32d850f5,
            0x3f9b762c, 0x3b5a6b9b, 0x0315d626, 0x07d4cb91, 0x0a97ed48, 0x0e56f0ff,
            0x1011a0fa, 0x14d0bd4d, 0x19939b94, 0x1d528623, 0xf12f560e, 0xf5ee4bb9,
            0xf8ad6d60, 0xfc6c70d7, 0xe22b20d2, 0xe6ea3d65, 0xeba91bbc, 0xef68060b,
            0xd727bbb6, 0xd3e6a601, 0xdea580d8, 0xda649d6f, 0xc423cd6a, 0xc0e2d0dd,
            0xcda1f604, 0xc960ebb3, 0xbd3e8d7e, 0xb9ff90c9, 0xb4bcb610, 0xb07daba7,
            0xae3afba2, 0xaafbe615, 0xa7b8c0cc, 0xa379dd7b, 0x9b3660c6, 0x9ff77d71,
            0x92b45ba8, 0x9675461f, 0x8832161a, 0x8cf30bad, 0x81b02d74, 0x857130c3,
            0x5d8a9099, 0x594b8d2e, 0x5408abf7, 0x50c9b640, 0x4e8ee645, 0x4a4ffbf2,
            0x470cdd2b, 0x43cdc09c, 0x7b827d21, 0x7f436096, 0x7200464f, 0x76c15bf8,
            0x68860bfd, 0x6c47164a, 0x61043093, 0x65c52d24, 0x119b4be9, 0x155a565e,
            0x18197087, 0x1cd86d30, 0x029f3d35, 0x065e2082, 0x0b1d065b, 0x0fdc1bec,
            0x3793a651, 0x3352bbe6, 0x3e119d3f, 0x3ad08088, 0x2497d08d, 0x2056cd3a,
            0x2d15ebe3, 0x29d4f654, 0xc5a92679, 0xc1683bce, 0xcc2b1d17, 0xc8ea00a0,
            0xd6ad50a5, 0xd26c4d12, 0xdf2f6bcb, 0xdbee767c, 0xe3a1cbc1, 0xe760d676,
            0xea23f0af, 0xeee2ed18, 0xf0a5bd1d, 0xf464a0aa, 0xf9278673, 0xfde69bc4,
            0x89b8fd09, 0x8d79e0be, 0x803ac667, 0x84fbdbd0, 0x9abc8bd5, 0x9e7d9662,
            0x933eb0bb, 0x97ffad0c, 0xafb010b1, 0xab710d06, 0xa6322bdf, 0xa2f33668,
            0xbcb4666d, 0xb8757bda, 0xb5365d03, 0xb1f740b4
        ]

        # Port of C++ memcrc function
        s = 0  # CRC accumulator (equivalent to 's' in C++)

        # Process each byte in the data (equivalent to first loop in C++)
        for byte_val in data:
            tabidx = (s >> 24) ^ byte_val
            s = ((s << 8) ^ crctab[tabidx]) & 0xFFFFFFFF

        # Process file length (equivalent to second loop in C++)
        temp_n = len(data)
        while temp_n:
            c = temp_n & 0o377  # Octal 377 = 0xFF
            temp_n = temp_n >> 8
            s = ((s << 8) ^ crctab[(s >> 24) ^ c]) & 0xFFFFFFFF

        # Final step: bitwise NOT (equivalent to ~s in C++)
        return (~s) & 0xFFFFFFFF
    
    def _handle_client(self, conn: socket.socket, address: Tuple[str, int]) -> None:
        """Handle individual client connection"""
        # Track connection
        self.stats.log_connection()

        try:
            if self.verbose:
                self.logger.info(f"🔗 New client connected from {address}")

            while True:
                # Receive request header
                header_data = self._recv_exact(conn, REQUEST_HEADER_SIZE)
                client_id, version, code, payload_size = self._unpack_request_header(header_data)

                # Track request
                self.stats.log_request(code)

                if self.verbose:
                    self.logger.info(f"📥 Request: client={client_id.hex()[:8]}..., version={version}, code={code}, payload={payload_size}B")
                elif self.debug_mode:
                    self.logger.debug(f"Request: code={code}, payload_size={payload_size}")
                else:
                    self.logger.info(f"Received request: version={version}, code={code}, payload_size={payload_size}")

                # Validate protocol version
                if version != PROTOCOL_VERSION:
                    self.logger.warning(f"❌ Invalid protocol version: {version} (expected {PROTOCOL_VERSION})")
                    self.stats.log_error()
                    self._send_response(conn, RESP_SERVER_ERROR)
                    continue

                # Receive payload if present
                payload = b''
                if payload_size > 0:
                    payload = self._recv_exact(conn, payload_size)
                    if self.debug_mode:
                        self.logger.debug(f"Received payload: {len(payload)} bytes")

                # Route request to appropriate handler
                try:
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
                        self.logger.warning(f"❌ Unknown request code: {code}")
                        self.stats.log_error()
                        self._send_response(conn, RESP_SERVER_ERROR)
                except Exception as handler_error:
                    self.logger.error(f"❌ Handler error for code {code}: {handler_error}")
                    self.stats.log_error()
                    self._send_response(conn, RESP_SERVER_ERROR)

        except ConnectionError:
            if self.verbose:
                self.logger.info(f"🔌 Client {address} disconnected")
            else:
                self.logger.info(f"Client {address} disconnected")
        except Exception as e:
            self.logger.error(f"❌ Error handling client {address}: {e}")
            self.stats.log_error()
        finally:
            self.stats.log_disconnection()
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

            # Track registration
            self.stats.log_registration()

            if self.verbose:
                self.logger.info(f"✅ Registered new client: {username} with UUID: {new_client_id.hex()}")
            else:
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
                # Import RSA public key (160-byte X.509 DER format from Crypto++)
                self.logger.debug(f"Importing RSA public key, size: {len(public_key)} bytes")
                rsa_key = RSA.import_key(public_key)
                self.logger.debug(f"RSA key imported successfully, size: {rsa_key.size_in_bits()} bits")

                cipher_rsa = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA256)
                encrypted_aes_key = cipher_rsa.encrypt(aes_key)

                # Send response with encrypted AES key
                response_payload = actual_client_id + encrypted_aes_key
                self._send_response(conn, RESP_PUBLIC_KEY_RECEIVED, response_payload)

                self.logger.info(f"AES key generated and sent to {username}")

            except Exception as e:
                self.logger.error(f"Error encrypting AES key for {username}: {e}")
                self.logger.error(f"Public key size: {len(public_key)} bytes, expected: {RSA_PUBLIC_KEY_SIZE}")
                if len(public_key) >= 10:
                    self.logger.error(f"Public key header: {public_key[:10].hex()}")
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
                self.logger.debug(f"Using stored RSA public key for {username}, size: {len(session.rsa_public_key)} bytes")
                rsa_key = RSA.import_key(session.rsa_public_key)
                cipher_rsa = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA256)
                encrypted_aes_key = cipher_rsa.encrypt(aes_key)

                # Send approval with encrypted AES key
                response_payload = actual_client_id + encrypted_aes_key
                self._send_response(conn, RESP_RECONNECT_APPROVED, response_payload)

                self.logger.info(f"Reconnection approved for {username}")

            except Exception as e:
                self.logger.error(f"Error encrypting AES key for reconnection of {username}: {e}")
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
            # Find client session using client_id from header (CRITICAL FIX)
            if client_id not in self.clients:
                self.logger.warning(f"Unknown client ID for file transfer: {client_id.hex()}")
                self._send_response(conn, RESP_SERVER_ERROR)
                return

            session = self.clients[client_id]
            if session.aes_key is None:
                self.logger.warning(f"No AES key for client: {client_id.hex()}")
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

                # Track file reception
                self.stats.log_file_received(len(decrypted_data))

                if self.verbose:
                    self.logger.info(f"💾 File saved: {file_path}, size: {len(decrypted_data):,}B, CRC: {calculated_crc:08x}")
                else:
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

        # Track CRC validation
        self.stats.log_crc_result('valid')

        if self.verbose:
            self.logger.info(f"✅ CRC validation successful for: {filename}")
        else:
            self.logger.info(f"CRC validation successful for: {filename}")

        # Send acknowledgement
        self._send_response(conn, RESP_GENERIC_ACK, client_id)

    def _handle_crc_invalid_resend(self, conn: socket.socket, client_id: bytes, payload: bytes) -> None:
        """Handle CRC invalid, resending (1030)"""
        if len(payload) < FILENAME_SIZE:
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        filename = self._unpad_string(payload[:FILENAME_SIZE])

        # Track CRC validation failure
        self.stats.log_crc_result('invalid')

        if self.verbose:
            self.logger.info(f"❌ CRC validation failed, client will resend: {filename}")
        else:
            self.logger.info(f"CRC validation failed, client will resend: {filename}")

        # Prepare for file retransmission - no response needed

    def _handle_crc_invalid_abort(self, conn: socket.socket, client_id: bytes, payload: bytes) -> None:
        """Handle CRC invalid, aborting (1031)"""
        if len(payload) < FILENAME_SIZE:
            self._send_response(conn, RESP_SERVER_ERROR)
            return

        filename = self._unpad_string(payload[:FILENAME_SIZE])

        # Track CRC abort
        self.stats.log_crc_result('aborted')

        if self.verbose:
            self.logger.info(f"💥 CRC validation failed 3 times, client aborting: {filename}")
        else:
            self.logger.info(f"CRC validation failed 3 times, client aborting: {filename}")

        # Send acknowledgement
        self._send_response(conn, RESP_GENERIC_ACK, client_id)

    def print_stats(self):
        """Print current server statistics"""
        print(self.stats.get_summary())

    def get_debug_info(self) -> str:
        """Get debug information for AI development"""
        return f"""
=== DEBUG INFO FOR AI AGENT ===
Server Mode: {'DEBUG' if self.debug_mode else 'NORMAL'} | {'VERBOSE' if self.verbose else 'QUIET'}
Active Sessions: {len(self.clients)}
Usernames Registered: {list(self.usernames.keys())}
Files Directory: {os.path.abspath(self.files_dir)}
Log Level: {self.logger.level}
Protocol Version: {PROTOCOL_VERSION}
Port: {self.port}
{self.stats.get_summary()}
===============================
"""

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
            if self.verbose:
                print("\n" + "="*50)
                print("📊 FINAL SERVER STATISTICS")
                print("="*50)
                self.print_stats()
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            self.stats.log_error()
        finally:
            server_socket.close()
            self.logger.info("Server stopped")

def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description='TCP Binary Protocol Server')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Enable debug mode with detailed logging')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose mode with enhanced output')
    parser.add_argument('--stats', '-s', action='store_true',
                       help='Print initial debug info and stats')
    parser.add_argument('--test', '-t', action='store_true',
                       help='Run in test mode (for development)')

    args = parser.parse_args()

    # Create server with specified options
    server = TCPServer(debug_mode=args.debug, verbose=args.verbose)

    if args.stats or args.debug:
        print(server.get_debug_info())

    if args.test:
        print("🧪 TEST MODE: Server will start but you can run additional tests")
        print("Use Ctrl+C to stop and see final stats")

    try:
        server.start()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")

if __name__ == "__main__":
    main()
