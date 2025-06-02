// File operations and remaining methods for TCPClient
// This file contains the file transfer and utility methods

#include "tcp_client.h"
#include <iostream>
#include <fstream>
#include <filesystem>

bool TCPClient::receiveAESKey() {
    std::cout << "🔐 Receiving AES session key..." << std::endl;
    
    uint16_t response_code;
    std::vector<uint8_t> response_payload;
    
    if (!receiveResponse(response_code, response_payload)) {
        return false;
    }

    if (response_code == RESP_PUBLIC_KEY_RECEIVED || response_code == RESP_RECONNECT_APPROVED) {
        // Response should contain UUID + encrypted AES key
        if (response_payload.size() < CLIENT_ID_SIZE) {
            std::cerr << "❌ Invalid AES key response size" << std::endl;
            return false;
        }

        // Extract encrypted AES key (skip UUID)
        std::vector<uint8_t> encrypted_aes_key(
            response_payload.begin() + CLIENT_ID_SIZE, 
            response_payload.end()
        );

        // Decrypt AES key using RSA private key
        if (!rsa_private_) {
            // Load RSA private key from credentials
            // This would need Base64 decoding implementation
            std::cerr << "❌ RSA private key not available for AES decryption" << std::endl;
            return false;
        }

        try {
            std::string encrypted_key_str(encrypted_aes_key.begin(), encrypted_aes_key.end());
            std::string decrypted_key = rsa_private_->decrypt(encrypted_key_str);
            
            if (decrypted_key.length() != AES_KEY_SIZE) {
                std::cerr << "❌ Decrypted AES key has wrong size: " << decrypted_key.length() << std::endl;
                return false;
            }

            aes_key_.assign(decrypted_key.begin(), decrypted_key.end());
            
            // Initialize AES wrapper with received key
            aes_ = std::make_unique<AESWrapper>(aes_key_.data(), AES_KEY_SIZE);
            
            std::cout << "✅ AES session key received and decrypted" << std::endl;
            return true;
            
        } catch (const std::exception& e) {
            std::cerr << "❌ Failed to decrypt AES key: " << e.what() << std::endl;
            return false;
        }
    } else {
        std::cerr << "❌ Unexpected response when expecting AES key: " << response_code << std::endl;
        return false;
    }
}

bool TCPClient::sendFile() {
    std::cout << "📁 Preparing file transfer..." << std::endl;
    
    // Read file data
    file_data_ = readFile(server_config_.file_path);
    if (file_data_.empty()) {
        std::cerr << "❌ Failed to read file: " << server_config_.file_path << std::endl;
        return false;
    }

    // Calculate CRC of original unencrypted file
    file_crc_ = calculateFileCRC(file_data_);
    std::cout << "✓ File CRC calculated: 0x" << std::hex << file_crc_ << std::dec << std::endl;

    // Encrypt file with AES
    if (!aes_) {
        std::cerr << "❌ AES key not available for file encryption" << std::endl;
        return false;
    }

    std::string encrypted_file;
    try {
        std::string file_str(file_data_.begin(), file_data_.end());
        encrypted_file = aes_->encrypt(file_str.c_str(), file_str.length());
        std::cout << "✓ File encrypted, size: " << encrypted_file.length() << " bytes" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "❌ File encryption failed: " << e.what() << std::endl;
        return false;
    }

    // Prepare file payload
    FilePayload payload;
    payload.content_size = static_cast<uint32_t>(encrypted_file.length());
    
    // Extract filename from path
    std::filesystem::path file_path(server_config_.file_path);
    std::string filename = file_path.filename().string();
    padString(payload.file_name, filename, FILENAME_SIZE);

    // Send file transfer request
    retry_count_ = 0;
    while (retry_count_ < MAX_RETRIES) {
        std::cout << "📤 Sending file (attempt " << (retry_count_ + 1) << "/" << MAX_RETRIES << ")..." << std::endl;

        // Send payload header
        if (!sendRequest(REQ_SEND_FILE, &payload, sizeof(payload))) {
            return false;
        }

        // Send encrypted file content
        try {
            boost::asio::write(*socket_, boost::asio::buffer(encrypted_file.data(), encrypted_file.length()));
            std::cout << "✓ File content sent" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "❌ Failed to send file content: " << e.what() << std::endl;
            return false;
        }

        // Receive server response with CRC
        uint16_t response_code;
        std::vector<uint8_t> response_payload;
        
        if (!receiveResponse(response_code, response_payload)) {
            return false;
        }

        if (response_code == RESP_FILE_RECEIVED) {
            if (response_payload.size() >= sizeof(uint32_t)) {
                uint32_t server_crc;
                std::memcpy(&server_crc, response_payload.data(), sizeof(uint32_t));
                
                std::cout << "✓ Server CRC received: 0x" << std::hex << server_crc << std::dec << std::endl;
                
                if (handleCRCValidation(server_crc)) {
                    return true; // Success!
                } else {
                    retry_count_++;
                    if (retry_count_ >= MAX_RETRIES) {
                        // Send abort message
                        sendRequest(REQ_CRC_INVALID_ABORT, nullptr, 0);
                        std::cerr << "❌ File transfer failed after " << MAX_RETRIES << " attempts" << std::endl;
                        return false;
                    } else {
                        // Send retry message
                        sendRequest(REQ_CRC_INVALID_RESEND, nullptr, 0);
                        std::cout << "⚠ CRC mismatch, retrying..." << std::endl;
                    }
                }
            } else {
                std::cerr << "❌ Invalid CRC response from server" << std::endl;
                return false;
            }
        } else {
            std::cerr << "❌ Unexpected response to file transfer: " << response_code << std::endl;
            return false;
        }
    }

    return false;
}

bool TCPClient::handleCRCValidation(uint32_t server_crc) {
    if (server_crc == file_crc_) {
        std::cout << "✅ CRC validation successful!" << std::endl;
        
        // Send CRC valid confirmation
        if (sendRequest(REQ_CRC_VALID, nullptr, 0)) {
            // Wait for final acknowledgment
            uint16_t response_code;
            std::vector<uint8_t> response_payload;
            
            if (receiveResponse(response_code, response_payload)) {
                if (response_code == RESP_GENERIC_ACK) {
                    std::cout << "✅ File transfer completed successfully!" << std::endl;
                    return true;
                }
            }
        }
        
        std::cerr << "❌ Failed to send CRC validation" << std::endl;
        return false;
    } else {
        std::cout << "❌ CRC mismatch - Client: 0x" << std::hex << file_crc_ 
                  << ", Server: 0x" << server_crc << std::dec << std::endl;
        return false;
    }
}

std::vector<uint8_t> TCPClient::readFile(const std::string& file_path) {
    std::ifstream file(file_path, std::ios::binary);
    if (!file.is_open()) {
        return {};
    }

    file.seekg(0, std::ios::end);
    size_t file_size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::vector<uint8_t> data(file_size);
    file.read(reinterpret_cast<char*>(data.data()), file_size);
    
    return data;
}

uint32_t TCPClient::calculateFileCRC(const std::vector<uint8_t>& file_data) {
    return memcrc(reinterpret_cast<const char*>(file_data.data()), file_data.size());
}
