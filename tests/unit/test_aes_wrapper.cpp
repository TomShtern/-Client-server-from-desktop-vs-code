#include <iostream>
#include <string>
#include <vector>
#include <cassert>
#include <iomanip>
#include "../../client/AESWrapper.h"

class AESWrapperTest {
private:
    int tests_run = 0;
    int tests_passed = 0;

    void assert_test(bool condition, const std::string& test_name) {
        tests_run++;
        if (condition) {
            tests_passed++;
            std::cout << "✅ PASS: " << test_name << std::endl;
        } else {
            std::cout << "❌ FAIL: " << test_name << std::endl;
        }
    }

    void print_hex(const std::string& data, const std::string& label) {
        std::cout << label << ": ";
        for (unsigned char c : data) {
            std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)c;
        }
        std::cout << std::dec << std::endl;
    }

public:
    void test_key_generation() {
        std::cout << "\n=== Testing AES Key Generation ===" << std::endl;
        
        AESWrapper aes;
        std::string key = aes.getKey();
        
        // Test key length (should be 32 bytes for AES-256)
        assert_test(key.length() == 32, "Key length is 32 bytes (AES-256)");
        
        // Test key is not empty
        assert_test(!key.empty(), "Key is not empty");
        
        // Test key contains non-zero bytes
        bool has_non_zero = false;
        for (char c : key) {
            if (c != 0) {
                has_non_zero = true;
                break;
            }
        }
        assert_test(has_non_zero, "Key contains non-zero bytes");
        
        print_hex(key, "Generated AES Key");
    }

    void test_encryption_decryption() {
        std::cout << "\n=== Testing AES Encryption/Decryption ===" << std::endl;
        
        AESWrapper aes;
        std::string plaintext = "Hello, World! This is a test message for AES encryption.";
        
        // Test encryption
        std::string encrypted = aes.encrypt(plaintext.c_str(), plaintext.length());
        assert_test(!encrypted.empty(), "Encryption produces non-empty result");
        assert_test(encrypted != plaintext, "Encrypted data differs from plaintext");
        
        print_hex(plaintext, "Original plaintext");
        print_hex(encrypted, "Encrypted data");
        
        // Test decryption
        std::string decrypted = aes.decrypt(encrypted.c_str(), encrypted.length());
        assert_test(decrypted == plaintext, "Decryption recovers original plaintext");
        
        std::cout << "Decrypted: " << decrypted << std::endl;
    }

    void test_empty_data() {
        std::cout << "\n=== Testing Empty Data Handling ===" << std::endl;
        
        AESWrapper aes;
        
        // Test empty string encryption
        std::string empty = "";
        std::string encrypted_empty = aes.encrypt(empty.c_str(), empty.length());
        std::string decrypted_empty = aes.decrypt(encrypted_empty.c_str(), encrypted_empty.length());
        
        assert_test(decrypted_empty == empty, "Empty string encryption/decryption");
    }

    void test_large_data() {
        std::cout << "\n=== Testing Large Data Encryption ===" << std::endl;
        
        AESWrapper aes;
        
        // Create large test data (1KB)
        std::string large_data(1024, 'A');
        for (int i = 0; i < 1024; i++) {
            large_data[i] = 'A' + (i % 26);
        }
        
        std::string encrypted = aes.encrypt(large_data.c_str(), large_data.length());
        std::string decrypted = aes.decrypt(encrypted.c_str(), encrypted.length());
        
        assert_test(decrypted == large_data, "Large data (1KB) encryption/decryption");
        assert_test(encrypted.length() >= large_data.length(), "Encrypted data size >= original");
        
        std::cout << "Original size: " << large_data.length() << " bytes" << std::endl;
        std::cout << "Encrypted size: " << encrypted.length() << " bytes" << std::endl;
    }

    void test_binary_data() {
        std::cout << "\n=== Testing Binary Data Encryption ===" << std::endl;
        
        AESWrapper aes;
        
        // Create binary data with all byte values
        std::string binary_data;
        for (int i = 0; i < 256; i++) {
            binary_data += static_cast<char>(i);
        }
        
        std::string encrypted = aes.encrypt(binary_data.c_str(), binary_data.length());
        std::string decrypted = aes.decrypt(encrypted.c_str(), encrypted.length());
        
        assert_test(decrypted == binary_data, "Binary data encryption/decryption");
        assert_test(decrypted.length() == 256, "Binary data length preserved");
    }

    void test_key_consistency() {
        std::cout << "\n=== Testing Key Consistency ===" << std::endl;
        
        AESWrapper aes1, aes2;
        std::string plaintext = "Test message for key consistency";
        
        // Set same key for both instances
        std::string key = aes1.getKey();
        aes2.setKey(key);
        
        // Encrypt with first instance, decrypt with second
        std::string encrypted = aes1.encrypt(plaintext.c_str(), plaintext.length());
        std::string decrypted = aes2.decrypt(encrypted.c_str(), encrypted.length());
        
        assert_test(decrypted == plaintext, "Cross-instance encryption/decryption with same key");
    }

    void test_different_keys() {
        std::cout << "\n=== Testing Different Keys ===" << std::endl;
        
        AESWrapper aes1, aes2;
        std::string plaintext = "Test message for different keys";
        
        // Use different keys
        std::string encrypted = aes1.encrypt(plaintext.c_str(), plaintext.length());
        std::string decrypted = aes2.decrypt(encrypted.c_str(), encrypted.length());
        
        assert_test(decrypted != plaintext, "Different keys produce different results");
    }

    void run_all_tests() {
        std::cout << "🧪 AES Wrapper Unit Tests" << std::endl;
        std::cout << "=========================" << std::endl;
        
        test_key_generation();
        test_encryption_decryption();
        test_empty_data();
        test_large_data();
        test_binary_data();
        test_key_consistency();
        test_different_keys();
        
        std::cout << "\n📊 Test Results:" << std::endl;
        std::cout << "Tests run: " << tests_run << std::endl;
        std::cout << "Tests passed: " << tests_passed << std::endl;
        std::cout << "Tests failed: " << (tests_run - tests_passed) << std::endl;
        std::cout << "Success rate: " << (100.0 * tests_passed / tests_run) << "%" << std::endl;
        
        if (tests_passed == tests_run) {
            std::cout << "🎉 All tests passed!" << std::endl;
        } else {
            std::cout << "❌ Some tests failed!" << std::endl;
        }
    }
};

int main() {
    try {
        AESWrapperTest test;
        test.run_all_tests();
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "❌ Test execution failed: " << e.what() << std::endl;
        return 1;
    }
}
