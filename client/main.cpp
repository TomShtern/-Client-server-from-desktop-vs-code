#include <iostream>
#include <exception>
#include "tcp_client.h"

int main() {
    try {
        std::cout << "=== Secure File Backup Client ===" << std::endl;
        std::cout << "Version: 1.0" << std::endl;
        std::cout << "Protocol Version: " << static_cast<int>(PROTOCOL_VERSION) << std::endl;
        std::cout << "AES Key Size: " << AES_KEY_SIZE << " bytes (AES-256)" << std::endl;
        std::cout << "RSA Key Size: " << RSA_PUBLIC_KEY_SIZE << " bytes (RSA-1024)" << std::endl;
        std::cout << "=======================================" << std::endl;

        TCPClient client;
        
        if (!client.initialize()) {
            std::cerr << "❌ Client initialization failed" << std::endl;
            return 1;
        }

        if (!client.run()) {
            std::cerr << "❌ Client execution failed" << std::endl;
            return 1;
        }

        std::cout << "\n✅ Client completed successfully!" << std::endl;
        return 0;

    } catch (const std::exception& e) {
        std::cerr << "❌ Fatal error: " << e.what() << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "❌ Unknown fatal error occurred" << std::endl;
        return 1;
    }
}
