#include "tcp_client.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cstring>
#include <boost/asio.hpp>

using boost::asio::ip::tcp;

TCPClient::TCPClient() 
    : socket_(nullptr), retry_count_(0) {
    // Initialize client_id to zeros (will be set from credentials)
    std::memset(client_id_, 0, CLIENT_ID_SIZE);
}

TCPClient::~TCPClient() {
    disconnect();
}

bool TCPClient::initialize() {
    std::cout << "=== Secure File Backup Client ===" << std::endl;
    std::cout << "Initializing client..." << std::endl;

    // Load server configuration
    if (!loadServerConfig()) {
        std::cerr << "❌ Failed to load server configuration" << std::endl;
        return false;
    }
    
    std::cout << "✓ Server config loaded: " << server_config_.host 
              << ":" << server_config_.port << std::endl;

    // Load or prepare client credentials
    if (!loadClientCredentials()) {
        std::cout << "ℹ No existing credentials found - will register as new client" << std::endl;
        credentials_.username = server_config_.username;
        credentials_.valid = false;
    } else {
        std::cout << "✓ Existing credentials loaded for: " << credentials_.username << std::endl;
    }

    return true;
}

bool TCPClient::run() {
    std::cout << "\n=== Starting Client Session ===" << std::endl;

    // Connect to server
    if (!connectToServer()) {
        std::cerr << "❌ Failed to connect to server" << std::endl;
        return false;
    }

    bool success = false;
    
    try {
        if (!credentials_.valid) {
            // First time - register
            std::cout << "📝 Registering new client..." << std::endl;
            if (!registerWithServer()) {
                std::cerr << "❌ Registration failed" << std::endl;
                return false;
            }
            
            if (!sendPublicKey()) {
                std::cerr << "❌ Failed to send public key" << std::endl;
                return false;
            }
        } else {
            // Returning client - reconnect
            std::cout << "🔄 Reconnecting existing client..." << std::endl;
            if (!reconnectToServer()) {
                std::cerr << "❌ Reconnection failed" << std::endl;
                return false;
            }
        }

        // AES key is now received and decrypted in sendPublicKey()

        // Send file
        if (!sendFile()) {
            std::cerr << "❌ File transfer failed" << std::endl;
            return false;
        }

        std::cout << "✅ File transfer completed successfully!" << std::endl;
        success = true;

    } catch (const std::exception& e) {
        std::cerr << "❌ Error during client session: " << e.what() << std::endl;
    }

    disconnect();
    return success;
}

bool TCPClient::loadServerConfig() {
    // Read transfer.info
    std::ifstream file("transfer.info");
    if (!file.is_open()) {
        std::cerr << "❌ Cannot open transfer.info" << std::endl;
        return false;
    }

    std::string line;
    std::vector<std::string> lines;
    
    while (std::getline(file, line)) {
        if (!line.empty()) {
            lines.push_back(line);
        }
    }
    
    if (lines.size() != 3) {
        std::cerr << "❌ transfer.info must have exactly 3 lines" << std::endl;
        return false;
    }

    // Parse lines
    server_config_.host = lines[0];
    server_config_.username = lines[1];
    server_config_.file_path = lines[2];

    // Read port from port.info (default 1256)
    std::ifstream port_file("port.info");
    if (port_file.is_open()) {
        std::string port_str;
        if (std::getline(port_file, port_str)) {
            try {
                server_config_.port = static_cast<uint16_t>(std::stoi(port_str));
            } catch (...) {
                server_config_.port = 1256;
            }
        }
    } else {
        server_config_.port = 1256;
    }

    return true;
}

bool TCPClient::loadClientCredentials() {
    std::ifstream file("me.info");
    if (!file.is_open()) {
        return false; // File doesn't exist - first run
    }

    std::string line;
    std::vector<std::string> lines;
    
    while (std::getline(file, line)) {
        if (!line.empty()) {
            lines.push_back(line);
        }
    }
    
    if (lines.size() != 3) {
        std::cerr << "❌ me.info corrupted - expected 3 lines" << std::endl;
        return false;
    }

    credentials_.username = lines[0];
    credentials_.uuid = lines[1];
    credentials_.private_key_base64 = lines[2];

    // Validate UUID format (32 hex characters)
    if (credentials_.uuid.length() != 32) {
        std::cerr << "❌ Invalid UUID format in me.info" << std::endl;
        return false;
    }

    // Convert UUID to binary for client_id
    for (size_t i = 0; i < 16; ++i) {
        std::string hex_byte = credentials_.uuid.substr(i * 2, 2);
        client_id_[i] = static_cast<uint8_t>(std::stoi(hex_byte, nullptr, 16));
    }

    // Initialize RSA private key wrapper from stored Base64 key
    try {
        std::string private_key_binary = Base64Wrapper::decode(credentials_.private_key_base64);
        rsa_private_ = std::make_unique<RSAPrivateWrapper>(private_key_binary);
        std::cout << "✓ RSA private key loaded from credentials" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "❌ Failed to load RSA private key: " << e.what() << std::endl;
        return false;
    }

    credentials_.valid = true;
    return true;
}

bool TCPClient::saveClientCredentials(const std::string& uuid, const std::string& private_key_base64) {
    // Atomic write: write to temp file, then rename
    std::ofstream temp_file("me.info.tmp");
    if (!temp_file.is_open()) {
        std::cerr << "❌ Cannot create temporary credentials file" << std::endl;
        return false;
    }

    temp_file << credentials_.username << std::endl;
    temp_file << uuid << std::endl;
    temp_file << private_key_base64 << std::endl;
    
    temp_file.close();

    // Rename temp file to actual file
    if (std::rename("me.info.tmp", "me.info") != 0) {
        std::cerr << "❌ Failed to save credentials file" << std::endl;
        return false;
    }

    std::cout << "✓ Credentials saved to me.info" << std::endl;
    return true;
}

bool TCPClient::connectToServer() {
    try {
        socket_ = std::make_unique<tcp::socket>(io_context_);
        
        tcp::resolver resolver(io_context_);
        auto endpoints = resolver.resolve(server_config_.host, std::to_string(server_config_.port));
        
        boost::asio::connect(*socket_, endpoints);
        
        std::cout << "✓ Connected to " << server_config_.host 
                  << ":" << server_config_.port << std::endl;
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "❌ Connection failed: " << e.what() << std::endl;
        return false;
    }
}

void TCPClient::disconnect() {
    if (socket_ && socket_->is_open()) {
        try {
            socket_->close();
            std::cout << "✓ Disconnected from server" << std::endl;
        } catch (...) {
            // Ignore errors during disconnect
        }
    }
}

void TCPClient::padString(char* dest, const std::string& src, size_t size) {
    std::memset(dest, 0, size);
    std::strncpy(dest, src.c_str(), std::min(src.length(), size - 1));
}

bool TCPClient::sendRequest(uint16_t code, const void* payload, uint32_t payload_size) {
    try {
        RequestHeader header;
        std::memcpy(header.client_id, client_id_, CLIENT_ID_SIZE);
        header.version = PROTOCOL_VERSION;
        header.code = code;
        header.payload_size = payload_size;

        // Send header
        boost::asio::write(*socket_, boost::asio::buffer(&header, sizeof(header)));
        
        // Send payload if present
        if (payload_size > 0 && payload) {
            boost::asio::write(*socket_, boost::asio::buffer(payload, payload_size));
        }

        return true;
    } catch (const std::exception& e) {
        std::cerr << "❌ Failed to send request: " << e.what() << std::endl;
        return false;
    }
}

bool TCPClient::receiveResponse(uint16_t& code, std::vector<uint8_t>& payload) {
    try {
        std::cout << "🔍 Debug: Starting receiveResponse..." << std::endl;

        ResponseHeader header;
        std::cout << "🔍 Debug: Reading response header (" << sizeof(header) << " bytes)..." << std::endl;
        boost::asio::read(*socket_, boost::asio::buffer(&header, sizeof(header)));
        std::cout << "🔍 Debug: Header received" << std::endl;

        if (header.version != PROTOCOL_VERSION) {
            std::cerr << "❌ Protocol version mismatch: got " << header.version << ", expected " << PROTOCOL_VERSION << std::endl;
            return false;
        }

        code = header.code;
        std::cout << "🔍 Debug: Response code: " << code << ", payload size: " << header.payload_size << std::endl;

        if (header.payload_size > 0) {
            payload.resize(header.payload_size);
            std::cout << "🔍 Debug: Reading payload (" << header.payload_size << " bytes)..." << std::endl;
            boost::asio::read(*socket_, boost::asio::buffer(payload.data(), header.payload_size));
            std::cout << "🔍 Debug: Payload received" << std::endl;
        } else {
            payload.clear();
        }

        std::cout << "🔍 Debug: receiveResponse completed successfully" << std::endl;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "❌ Failed to receive response: " << e.what() << std::endl;
        return false;
    }
}

bool TCPClient::registerWithServer() {
    std::cout << "📝 Sending registration request..." << std::endl;

    RegistrationPayload payload;
    padString(payload.name, credentials_.username, USERNAME_SIZE);

    if (!sendRequest(REQ_REGISTER, &payload, sizeof(payload))) {
        return false;
    }

    uint16_t response_code;
    std::vector<uint8_t> response_payload;

    if (!receiveResponse(response_code, response_payload)) {
        return false;
    }

    if (response_code == RESP_REGISTER_SUCCESS) {
        if (response_payload.size() != CLIENT_ID_SIZE) {
            std::cerr << "❌ Invalid UUID size in registration response" << std::endl;
            return false;
        }

        // Store UUID as binary in client_id and as hex string
        std::memcpy(client_id_, response_payload.data(), CLIENT_ID_SIZE);

        std::ostringstream uuid_hex;
        for (size_t i = 0; i < CLIENT_ID_SIZE; ++i) {
            uuid_hex << std::hex << std::setfill('0') << std::setw(2)
                     << static_cast<unsigned>(client_id_[i]);
        }
        credentials_.uuid = uuid_hex.str();

        // Generate RSA key pair
        rsa_private_ = std::make_unique<RSAPrivateWrapper>();

        // Get private key in Base64 format for storage
        std::string private_key_binary = rsa_private_->getPrivateKey();
        credentials_.private_key_base64 = Base64Wrapper::encode(private_key_binary);

        // Save credentials
        if (!saveClientCredentials(credentials_.uuid, credentials_.private_key_base64)) {
            return false;
        }

        credentials_.valid = true;
        std::cout << "✅ Registration successful! UUID: " << credentials_.uuid << std::endl;
        return true;

    } else if (response_code == RESP_REGISTER_FAILED) {
        std::cerr << "❌ Registration failed - username already exists" << std::endl;
        return false;
    } else {
        std::cerr << "❌ Unexpected response to registration: " << response_code << std::endl;
        return false;
    }
}

bool TCPClient::reconnectToServer() {
    std::cout << "🔄 Sending reconnection request..." << std::endl;

    ReconnectionPayload payload;
    padString(payload.name, credentials_.username, USERNAME_SIZE);

    if (!sendRequest(REQ_RECONNECT, &payload, sizeof(payload))) {
        return false;
    }

    uint16_t response_code;
    std::vector<uint8_t> response_payload;

    if (!receiveResponse(response_code, response_payload)) {
        return false;
    }

    if (response_code == RESP_RECONNECT_APPROVED) {
        std::cout << "✅ Reconnection approved" << std::endl;

        // Extract AES key from response payload (UUID + encrypted AES key)
        if (response_payload.size() < CLIENT_ID_SIZE) {
            std::cerr << "❌ Invalid AES key response size" << std::endl;
            return false;
        }

        // Extract encrypted AES key (skip UUID)
        std::vector<uint8_t> encrypted_aes_key(
            response_payload.begin() + CLIENT_ID_SIZE,
            response_payload.end()
        );

        std::cout << "🔍 Debug: Encrypted AES key size: " << encrypted_aes_key.size() << " bytes" << std::endl;

        // Decrypt AES key using RSA private key
        try {
            std::string encrypted_key_str(encrypted_aes_key.begin(), encrypted_aes_key.end());
            std::cout << "🔍 Debug: Starting RSA decryption..." << std::endl;

            std::string decrypted_key = rsa_private_->decrypt(encrypted_key_str);
            std::cout << "🔍 Debug: RSA decryption completed" << std::endl;

            if (decrypted_key.length() != AES_KEY_SIZE) {
                std::cerr << "❌ Decrypted AES key has wrong size: " << decrypted_key.length() << " (expected " << AES_KEY_SIZE << ")" << std::endl;
                return false;
            }

            aes_key_.assign(decrypted_key.begin(), decrypted_key.end());

            // Initialize AES wrapper with received key
            aes_ = std::make_unique<AESWrapper>(aes_key_.data(), AES_KEY_SIZE);

            std::cout << "✅ AES session key received and decrypted" << std::endl;

        } catch (const std::exception& e) {
            std::cerr << "❌ Failed to decrypt AES key: " << e.what() << std::endl;
            return false;
        }

        return true;
    } else if (response_code == RESP_RECONNECT_DENIED) {
        std::cerr << "❌ Reconnection denied - client not found" << std::endl;
        return false;
    } else {
        std::cerr << "❌ Unexpected response to reconnection: " << response_code << std::endl;
        return false;
    }
}

bool TCPClient::sendPublicKey() {
    std::cout << "🔑 Sending public key..." << std::endl;

    if (!rsa_private_) {
        std::cerr << "❌ RSA private key not initialized" << std::endl;
        return false;
    }

    PublicKeyPayload payload;
    padString(payload.name, credentials_.username, USERNAME_SIZE);

    // Extract public key in X.509 format (160 bytes)
    rsa_private_->getPublicKey(reinterpret_cast<char*>(payload.public_key), RSA_PUBLIC_KEY_SIZE);

    if (!sendRequest(REQ_SEND_PUBLIC_KEY, &payload, sizeof(payload))) {
        return false;
    }

    uint16_t response_code;
    std::vector<uint8_t> response_payload;

    if (!receiveResponse(response_code, response_payload)) {
        return false;
    }

    if (response_code == RESP_PUBLIC_KEY_RECEIVED) {
        std::cout << "✅ Public key sent successfully" << std::endl;

        // Extract AES key from response payload (UUID + encrypted AES key)
        if (response_payload.size() < CLIENT_ID_SIZE) {
            std::cerr << "❌ Invalid AES key response size" << std::endl;
            return false;
        }

        // Extract encrypted AES key (skip UUID)
        std::vector<uint8_t> encrypted_aes_key(
            response_payload.begin() + CLIENT_ID_SIZE,
            response_payload.end()
        );

        std::cout << "🔍 Debug: Encrypted AES key size: " << encrypted_aes_key.size() << " bytes" << std::endl;

        // Decrypt AES key using RSA private key
        try {
            std::string encrypted_key_str(encrypted_aes_key.begin(), encrypted_aes_key.end());
            std::cout << "🔍 Debug: Starting RSA decryption..." << std::endl;

            std::string decrypted_key = rsa_private_->decrypt(encrypted_key_str);
            std::cout << "🔍 Debug: RSA decryption completed" << std::endl;

            if (decrypted_key.length() != AES_KEY_SIZE) {
                std::cerr << "❌ Decrypted AES key has wrong size: " << decrypted_key.length() << " (expected " << AES_KEY_SIZE << ")" << std::endl;
                return false;
            }

            aes_key_.assign(decrypted_key.begin(), decrypted_key.end());

            // Initialize AES wrapper with received key
            aes_ = std::make_unique<AESWrapper>(aes_key_.data(), AES_KEY_SIZE);

            std::cout << "✅ AES session key received and decrypted" << std::endl;

        } catch (const std::exception& e) {
            std::cerr << "❌ Failed to decrypt AES key: " << e.what() << std::endl;
            return false;
        }

        return true;
    } else {
        std::cerr << "❌ Failed to send public key, response: " << response_code << std::endl;
        return false;
    }
}
