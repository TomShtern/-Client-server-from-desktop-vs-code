#pragma once

#include <string>
#include <vector>
#include <memory>
#include <fstream>
#include <boost/asio.hpp>
#include "AESWrapper.h"
#include "RSAWrapper.h"
#include "Base64Wrapper.h"
#include "cksum.h"

// Protocol Constants
constexpr uint8_t PROTOCOL_VERSION = 3;
constexpr size_t CLIENT_ID_SIZE = 16;
constexpr size_t USERNAME_SIZE = 255;
constexpr size_t FILENAME_SIZE = 255;
constexpr size_t RSA_PUBLIC_KEY_SIZE = 160;
constexpr size_t AES_KEY_SIZE = 32;  // 256 bits - CRITICAL: AES-256
constexpr size_t AES_IV_SIZE = 16;

// Request Codes (Client -> Server)
constexpr uint16_t REQ_REGISTER = 1025;
constexpr uint16_t REQ_SEND_PUBLIC_KEY = 1026;
constexpr uint16_t REQ_RECONNECT = 1027;
constexpr uint16_t REQ_SEND_FILE = 1028;
constexpr uint16_t REQ_CRC_VALID = 1029;
constexpr uint16_t REQ_CRC_INVALID_RESEND = 1030;
constexpr uint16_t REQ_CRC_INVALID_ABORT = 1031;

// Response Codes (Server -> Client)
constexpr uint16_t RESP_REGISTER_SUCCESS = 1600;
constexpr uint16_t RESP_REGISTER_FAILED = 1601;
constexpr uint16_t RESP_PUBLIC_KEY_RECEIVED = 1602;
constexpr uint16_t RESP_FILE_RECEIVED = 1603;
constexpr uint16_t RESP_GENERIC_ACK = 1604;
constexpr uint16_t RESP_RECONNECT_APPROVED = 1605;
constexpr uint16_t RESP_RECONNECT_DENIED = 1606;
constexpr uint16_t RESP_SERVER_ERROR = 1607;

// Binary Protocol Structures (packed for exact byte layout)
#pragma pack(push, 1)

struct RequestHeader {
    uint8_t client_id[CLIENT_ID_SIZE];
    uint8_t version;
    uint16_t code;
    uint32_t payload_size;
};

struct ResponseHeader {
    uint8_t version;
    uint16_t code;
    uint32_t payload_size;
};

struct RegistrationPayload {
    char name[USERNAME_SIZE];
};

struct PublicKeyPayload {
    char name[USERNAME_SIZE];
    uint8_t public_key[RSA_PUBLIC_KEY_SIZE];
};

struct ReconnectionPayload {
    char name[USERNAME_SIZE];
};

struct FilePayload {
    uint32_t content_size;
    char file_name[FILENAME_SIZE];
    // Followed by encrypted file content
};

#pragma pack(pop)

// Configuration structures
struct ServerConfig {
    std::string host;
    uint16_t port;
    std::string username;
    std::string file_path;
};

struct ClientCredentials {
    std::string username;
    std::string uuid;
    std::string private_key_base64;
    bool valid = false;
};

class TCPClient {
public:
    TCPClient();
    ~TCPClient();

    // Main operations
    bool initialize();
    bool run();

private:
    // Configuration and credentials
    bool loadServerConfig();
    bool loadClientCredentials();
    bool saveClientCredentials(const std::string& uuid, const std::string& private_key_base64);

    // Network operations
    bool connectToServer();
    void disconnect();
    
    // Protocol operations
    bool registerWithServer();
    bool reconnectToServer();
    bool sendPublicKey();
    bool receiveAESKey();
    bool sendFile();
    bool handleCRCValidation(uint32_t server_crc);

    // Message handling
    bool sendRequest(uint16_t code, const void* payload, uint32_t payload_size);
    bool receiveResponse(uint16_t& code, std::vector<uint8_t>& payload);
    
    // Utility functions
    void padString(char* dest, const std::string& src, size_t size);
    std::vector<uint8_t> readFile(const std::string& file_path);
    uint32_t calculateFileCRC(const std::vector<uint8_t>& file_data);

    // Member variables
    boost::asio::io_context io_context_;
    std::unique_ptr<boost::asio::ip::tcp::socket> socket_;
    
    ServerConfig server_config_;
    ClientCredentials credentials_;
    
    std::unique_ptr<RSAPrivateWrapper> rsa_private_;
    std::unique_ptr<AESWrapper> aes_;
    
    uint8_t client_id_[CLIENT_ID_SIZE];
    std::vector<uint8_t> aes_key_;
    
    // File transfer state
    std::string file_path_;
    std::vector<uint8_t> file_data_;
    uint32_t file_crc_;
    int retry_count_;
    
    static constexpr int MAX_RETRIES = 3;
    static constexpr int SOCKET_TIMEOUT_SECONDS = 60;
};
