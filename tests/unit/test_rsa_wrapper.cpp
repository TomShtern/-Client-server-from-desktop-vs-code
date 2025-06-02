#include <iostream>
#include <string>
#include <vector>
#include <cassert>
#include <iomanip>
#include "../../client/RSAWrapper.h"

class RSAWrapperTest {
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
        std::cout << label << " (" << data.length() << " bytes): ";
        for (size_t i = 0; i < std::min(data.length(), size_t(32)); i++) {
            std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)(unsigned char)data[i];
        }
        if (data.length() > 32) std::cout << "...";
        std::cout << std::dec << std::endl;
    }

public:
    void test_key_generation() {
        std::cout << "\n=== Testing RSA Key Generation ===" << std::endl;
        
        RSAWrapper rsa;
        
        // Test public key generation
        std::string public_key = rsa.getPublicKey();
        assert_test(!public_key.empty(), "Public key is not empty");
        assert_test(public_key.length() == 160, "Public key is 160 bytes (X.509 format)");
        
        print_hex(public_key, "Public Key");
        
        // Test private key exists (can't access directly, but test encryption/decryption)
        std::string test_data = "Hello RSA!";
        std::string encrypted = rsa.encrypt(test_data);
        assert_test(!encrypted.empty(), "Private key exists (encryption works)");
    }

    void test_encryption_decryption() {
        std::cout << "\n=== Testing RSA Encryption/Decryption ===" << std::endl;
        
        RSAWrapper rsa;
        std::string plaintext = "This is a test message for RSA encryption.";
        
        // Test encryption
        std::string encrypted = rsa.encrypt(plaintext);
        assert_test(!encrypted.empty(), "Encryption produces non-empty result");
        assert_test(encrypted != plaintext, "Encrypted data differs from plaintext");
        assert_test(encrypted.length() == 128, "Encrypted data is 128 bytes (RSA-1024)");
        
        print_hex(plaintext, "Original plaintext");
        print_hex(encrypted, "Encrypted data");
        
        // Test decryption
        std::string decrypted = rsa.decrypt(encrypted);
        assert_test(decrypted == plaintext, "Decryption recovers original plaintext");
        
        std::cout << "Decrypted: " << decrypted << std::endl;
    }

    void test_aes_key_encryption() {
        std::cout << "\n=== Testing AES Key Encryption (32 bytes) ===" << std::endl;
        
        RSAWrapper rsa;
        
        // Create 32-byte AES key
        std::string aes_key(32, 0);
        for (int i = 0; i < 32; i++) {
            aes_key[i] = static_cast<char>(i + 1);
        }
        
        print_hex(aes_key, "Original AES Key");
        
        // Test encryption of AES key
        std::string encrypted = rsa.encrypt(aes_key);
        assert_test(!encrypted.empty(), "AES key encryption produces result");
        assert_test(encrypted.length() == 128, "Encrypted AES key is 128 bytes");
        
        // Test decryption of AES key
        std::string decrypted = rsa.decrypt(encrypted);
        assert_test(decrypted == aes_key, "AES key decryption recovers original");
        assert_test(decrypted.length() == 32, "Decrypted AES key is 32 bytes");
        
        print_hex(decrypted, "Decrypted AES Key");
    }

    void test_maximum_data_size() {
        std::cout << "\n=== Testing Maximum Data Size ===" << std::endl;
        
        RSAWrapper rsa;
        
        // RSA-1024 can encrypt up to 117 bytes (1024/8 - 11 for PKCS#1 padding)
        std::string max_data(117, 'X');
        
        std::string encrypted = rsa.encrypt(max_data);
        std::string decrypted = rsa.decrypt(encrypted);
        
        assert_test(decrypted == max_data, "Maximum size data (117 bytes) encryption/decryption");
        
        std::cout << "Max data size: " << max_data.length() << " bytes" << std::endl;
    }

    void test_empty_data() {
        std::cout << "\n=== Testing Empty Data Handling ===" << std::endl;
        
        RSAWrapper rsa;
        
        std::string empty = "";
        std::string encrypted = rsa.encrypt(empty);
        std::string decrypted = rsa.decrypt(encrypted);
        
        assert_test(decrypted == empty, "Empty string encryption/decryption");
    }

    void test_binary_data() {
        std::cout << "\n=== Testing Binary Data Encryption ===" << std::endl;
        
        RSAWrapper rsa;
        
        // Create binary data with various byte values
        std::string binary_data;
        for (int i = 0; i < 50; i++) {
            binary_data += static_cast<char>(i * 5 % 256);
        }
        
        print_hex(binary_data, "Original binary data");
        
        std::string encrypted = rsa.encrypt(binary_data);
        std::string decrypted = rsa.decrypt(encrypted);
        
        assert_test(decrypted == binary_data, "Binary data encryption/decryption");
        assert_test(decrypted.length() == binary_data.length(), "Binary data length preserved");
        
        print_hex(decrypted, "Decrypted binary data");
    }

    void test_key_consistency() {
        std::cout << "\n=== Testing Key Consistency ===" << std::endl;
        
        RSAWrapper rsa;
        std::string test_data = "Consistency test message";
        
        // Multiple encryptions should produce different results (due to padding)
        std::string encrypted1 = rsa.encrypt(test_data);
        std::string encrypted2 = rsa.encrypt(test_data);
        
        // But both should decrypt to the same plaintext
        std::string decrypted1 = rsa.decrypt(encrypted1);
        std::string decrypted2 = rsa.decrypt(encrypted2);
        
        assert_test(decrypted1 == test_data, "First encryption/decryption correct");
        assert_test(decrypted2 == test_data, "Second encryption/decryption correct");
        assert_test(decrypted1 == decrypted2, "Both decryptions produce same result");
        
        // Note: encrypted1 and encrypted2 may be different due to random padding
        std::cout << "Encrypted results may differ due to random padding (this is normal)" << std::endl;
    }

    void test_public_key_format() {
        std::cout << "\n=== Testing Public Key Format ===" << std::endl;
        
        RSAWrapper rsa;
        std::string public_key = rsa.getPublicKey();
        
        // Test X.509 format characteristics
        assert_test(public_key.length() == 160, "Public key is exactly 160 bytes");
        
        // X.509 DER format should start with 0x30 (SEQUENCE)
        assert_test((unsigned char)public_key[0] == 0x30, "Public key starts with X.509 SEQUENCE tag");
        
        print_hex(public_key, "Full Public Key");
        
        // Print first few bytes to verify X.509 structure
        std::cout << "X.509 structure check:" << std::endl;
        std::cout << "  Byte 0 (SEQUENCE): 0x" << std::hex << (int)(unsigned char)public_key[0] << std::dec << std::endl;
        std::cout << "  Byte 1 (Length): 0x" << std::hex << (int)(unsigned char)public_key[1] << std::dec << std::endl;
    }

    void run_all_tests() {
        std::cout << "🔐 RSA Wrapper Unit Tests" << std::endl;
        std::cout << "=========================" << std::endl;
        
        test_key_generation();
        test_encryption_decryption();
        test_aes_key_encryption();
        test_maximum_data_size();
        test_empty_data();
        test_binary_data();
        test_key_consistency();
        test_public_key_format();
        
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
        RSAWrapperTest test;
        test.run_all_tests();
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "❌ Test execution failed: " << e.what() << std::endl;
        return 1;
    }
}
