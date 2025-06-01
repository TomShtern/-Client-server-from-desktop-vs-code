# Updated server.py with improved features
import os
import sys
import socket
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from base64 import b64decode
from datetime import datetime
import hashlib

# Try to import cryptography's Fernet for encryption
try:
    from cryptography.fernet import Fernet  # type: ignore
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    # Dummy Fernet when cryptography is unavailable
    class Fernet:
        @staticmethod
        def generate_key():
            raise RuntimeError("cryptography module not available")
        def __init__(self, key):
            pass
        def encrypt(self, data):
            return data
        def decrypt(self, data):
            return data

# Configuration
BACKUP_DIR = 'backups'
USERNAME = 'user'
PASSWORD = 'password'
HOST = ''  # Empty string means listen on all available interfaces
PORT = 8080
LOG_FILE = 'backup_server.log'
KEY_FILE = 'encryption.key'
ENABLE_ENCRYPTION = ENCRYPTION_AVAILABLE

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create backup directory if it doesn't exist
os.makedirs(BACKUP_DIR, exist_ok=True)

# File hash storage for deduplication (simple in-memory version)
file_hashes = {}

# Get or create encryption key
def get_encryption_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

# Get encryption cipher
def get_cipher():
    if ENABLE_ENCRYPTION:
        key = get_encryption_key()
        return Fernet(key)
    return None

class AuthHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to use our custom logger
        logging.info("%s - - [%s] %s" %
                     (self.client_address[0],
                      self.log_date_time_string(),
                      format % args))
    def do_GET(self):
        # Check if this is a download request
        if self.path.startswith('/download/'):
            # Authenticate first
            if not self.authenticate():
                return
                
            filename = self.path[10:]  # Remove '/download/' prefix
            file_path = os.path.join(BACKUP_DIR, filename)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    
                # Decrypt if necessary
                if ENABLE_ENCRYPTION:
                    try:
                        cipher = get_cipher()
                        if cipher:
                            try:
                                file_data = cipher.decrypt(file_data)
                            except Exception as e:
                                # If decryption fails, send the raw data
                                logging.error(f"Failed to decrypt {filename}: {e}")
                    except Exception as e:
                        logging.error(f"Error in decryption setup: {e}")
                
                self.wfile.write(file_data)
                logging.info(f"File downloaded: {filename} by {self.client_address[0]}")
                return
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'File not found')
                return
        
        # File browser page
        elif self.path == '/files':
            if not self.authenticate():
                return
                
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Get files list
            files = []
            for filename in os.listdir(BACKUP_DIR):
                file_path = os.path.join(BACKUP_DIR, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_time = os.path.getmtime(file_path)
                    files.append((filename, file_size, datetime.fromtimestamp(file_time)))
            
            # Sort files by timestamp (newest first)
            files.sort(key=lambda x: x[2], reverse=True)
            
            # Build the HTML page
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Backup Server - File Browser</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
                    tr:hover { background-color: #f5f5f5; }
                    th { background-color: #4CAF50; color: white; }
                    .size { text-align: right; }
                    .navbar { margin-bottom: 20px; }
                    .navbar a { margin-right: 15px; }
                </style>
            </head>
            <body>
                <div class="navbar">
                    <a href="/">Home</a>
                    <a href="/files">File Browser</a>
                </div>
                <h1>Backup Server - File Browser</h1>
                <p>Total files: {}</p>
                <table>
                    <tr>
                        <th>Filename</th>
                        <th>Size</th>
                        <th>Timestamp</th>
                        <th>Actions</th>
                    </tr>
            """.format(len(files))
            
            for filename, size, timestamp in files:
                # Format size in human-readable form
                size_str = self._format_size(size)
                    
                html += f"""
                    <tr>
                        <td>{filename}</td>
                        <td class="size">{size_str}</td>
                        <td>{timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                        <td><a href="/download/{filename}">Download</a></td>
                    </tr>
                """
                
            html += """
                </table>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            return
            
        # Simple status page
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Count files in backup directory
            try:
                file_count = len([f for f in os.listdir(BACKUP_DIR) if os.path.isfile(os.path.join(BACKUP_DIR, f))])
                total_size = sum(os.path.getsize(os.path.join(BACKUP_DIR, f)) for f in os.listdir(BACKUP_DIR) 
                               if os.path.isfile(os.path.join(BACKUP_DIR, f)))
                
                # Convert size to human-readable format
                size_str = self._format_size(total_size)
            except Exception as e:
                file_count = 0
                size_str = "Error: " + str(e)
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>                <title>Backup Server Status</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    h1 {{ color: #333; }}
                    .status {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                    .footer {{ margin-top: 30px; font-size: 0.8em; color: #777; }}
                    .navbar {{ margin-bottom: 20px; }}
                    .navbar a {{ margin-right: 15px; text-decoration: none; color: #4CAF50; }}
                    .navbar a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <div class="navbar">
                    <a href="/">Home</a>
                    <a href="/files">File Browser</a>
                </div>
                <h1>Backup Server Status</h1>
                <div class="status">
                    <p><strong>Status:</strong> Running</p>
                    <p><strong>Files stored:</strong> {file_count}</p>
                    <p><strong>Total storage used:</strong> {size_str}</p>
                    <p><strong>Server started:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div class="footer">
                    <p>Backup Server v1.0</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            return
        
        self.send_response(404)
        self.end_headers()
    
    def do_POST(self):
        # Check authentication
        if not self.headers.get('Authorization'):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Secure Backup"')
            self.end_headers()
            logging.warning(f"Authentication missing from {self.client_address[0]}")
            return
        
        try:
            auth_type, encoded = self.headers.get('Authorization').split(' ', 1)
            if auth_type != 'Basic':
                self.send_response(401)
                self.end_headers()
                logging.warning(f"Non-Basic authentication attempt from {self.client_address[0]}")
                return
            
            decoded = b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            if username != USERNAME or password != PASSWORD:
                self.send_response(403)
                self.end_headers()
                logging.warning(f"Failed login attempt from {self.client_address[0]} with username: {username}")
                return
            
            # Get filename from headers
            filename = self.headers.get('X-Filename')
            if not filename:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Error: X-Filename header is required')
                logging.error(f"Missing X-Filename header from {self.client_address[0]}")
                return
            
            # Create timestamped filename to prevent overwrites
            basename = os.path.basename(filename)
            name, ext = os.path.splitext(basename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(BACKUP_DIR, safe_filename)
            content_length = int(self.headers.get('Content-Length', 0))
              # Read and save the file
            data = self.rfile.read(content_length)
            
            # Calculate file hash for deduplication
            file_hash = hashlib.sha256(data).hexdigest()
            
            # Check for duplicates
            deduplicated = False
            if file_hash in file_hashes:
                existing_path = file_hashes[file_hash]
                if os.path.exists(existing_path):
                    try:
                        os.link(existing_path, filepath)
                        logging.info(f"Deduplicated file {safe_filename} (matches {os.path.basename(existing_path)})")
                        deduplicated = True
                    except:
                        # If linking fails, continue with normal save
                        pass
            
            if not deduplicated:
                # Encrypt the file if encryption is enabled
                try:
                    if ENABLE_ENCRYPTION:
                        cipher = get_cipher()
                        if cipher:
                            data = cipher.encrypt(data)
                            logging.info(f"File {safe_filename} encrypted")
                except Exception as e:
                    logging.error(f"Encryption error: {e}")
                    # Continue with unencrypted data if encryption fails
                
                # Write the file to disk
                with open(filepath, 'wb') as f:
                    f.write(data)
                
                # Store hash for future deduplication
                file_hashes[file_hash] = filepath
            
            file_size = os.path.getsize(filepath)
            size_str = self._format_size(file_size)
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'File uploaded successfully: {safe_filename} ({size_str})'.encode('utf-8'))
            
            logging.info(f"File uploaded: {safe_filename} ({size_str}) from {self.client_address[0]}")
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Server error: {str(e)}'.encode('utf-8'))
            logging.error(f"Error handling upload: {str(e)}")
    def _format_size(self, size_bytes):
        """Convert size in bytes to human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.1f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f} GB"
            
    def authenticate(self):
        """Authenticate user for protected pages"""
        if not self.headers.get('Authorization'):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Secure Backup"')
            self.end_headers()
            logging.warning(f"Authentication missing from {self.client_address[0]}")
            return False
        
        try:
            auth_type, encoded = self.headers.get('Authorization').split(' ', 1)
            if auth_type != 'Basic':
                self.send_response(401)
                self.end_headers()
                logging.warning(f"Non-Basic authentication attempt from {self.client_address[0]}")
                return False
            
            decoded = b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            if username != USERNAME or password != PASSWORD:
                self.send_response(403)
                self.end_headers()
                logging.warning(f"Failed login attempt from {self.client_address[0]} with username: {username}")
                return False
                
            return True
                
        except Exception as e:
            self.send_response(401)
            self.end_headers()
            logging.error(f"Authentication error: {e}")
            return False

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

def run(server_class=ThreadedHTTPServer, handler_class=AuthHandler):
    server_address = (HOST, PORT)
    httpd = server_class(server_address, handler_class)
    
    # Get server IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"Starting backup server on port {PORT}...")
    print(f"Local URL: http://{local_ip}:{PORT}")
    print(f"Network URL: http://0.0.0.0:{PORT}")
    print(f"Files will be stored in: {os.path.abspath(BACKUP_DIR)}")
    print(f"Press Ctrl+C to stop the server")
    
    logging.info(f"Server started on port {PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        logging.info("Server shutdown")
    
    httpd.server_close()
    print("Server stopped")

if __name__ == '__main__':
    run()
