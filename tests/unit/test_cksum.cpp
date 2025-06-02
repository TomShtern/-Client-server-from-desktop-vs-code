#include <iostream>
#include <string>
#include <vector>
#include <cassert>
#include <iomanip>
#include <fstream>
#include "../../client/cksum.h"

class CksumTest {
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

    void print_crc_result(unsigned long crc, const std::string& label) {
        std::cout << label << ": 0x" << std::hex << std::setw(8) << std::setfill('0') << crc << std::dec << std::endl;
    }

public:
    void test_empty_data() {
        std::cout << "\n=== Testing Empty Data CRC ===" << std::endl;
        
        std::string empty = "";
        unsigned long crc = memcrc(empty.c_str(), empty.length());
        
        print_crc_result(crc, "Empty string CRC");
        
        // Empty data should have a specific CRC value
        assert_test(crc != 0, "Empty data CRC is not zero");
    }

    void test_known_values() {
        std::cout << "\n=== Testing Known CRC Values ===" << std::endl;
        
        // Test with simple known data
        std::string test1 = "Hello";
        unsigned long crc1 = memcrc(test1.c_str(), test1.length());
        print_crc_result(crc1, "\"Hello\" CRC");
        
        std::string test2 = "Hello, World!";
        unsigned long crc2 = memcrc(test2.c_str(), test2.length());
        print_crc_result(crc2, "\"Hello, World!\" CRC");
        
        // Different strings should have different CRCs
        assert_test(crc1 != crc2, "Different strings have different CRCs");
        
        // Test with the exact data from your successful transfer
        std::string test_file_content = "This is a test file for the secure backup system.\nIt contains multiple lines.\nAnd some special characters: !@#$%^&*()\n";
        unsigned long crc3 = memcrc(test_file_content.c_str(), test_file_content.length());
        print_crc_result(crc3, "Test file content CRC");
        
        // This should match the CRC from your successful transfers: 0x73dbfba4
        std::cout << "Expected CRC from successful transfer: 0x73dbfba4" << std::endl;
    }

    void test_single_bytes() {
        std::cout << "\n=== Testing Single Byte CRCs ===" << std::endl;
        
        for (int i = 0; i < 10; i++) {
            std::string single_byte(1, static_cast<char>('A' + i));
            unsigned long crc = memcrc(single_byte.c_str(), single_byte.length());
            std::cout << "'" << single_byte << "' CRC: 0x" << std::hex << std::setw(8) << std::setfill('0') << crc << std::dec << std::endl;
        }
        
        // Test that different single bytes have different CRCs
        std::string a = "A";
        std::string b = "B";
        unsigned long crc_a = memcrc(a.c_str(), a.length());
        unsigned long crc_b = memcrc(b.c_str(), b.length());
        
        assert_test(crc_a != crc_b, "Different single bytes have different CRCs");
    }

    void test_incremental_data() {
        std::cout << "\n=== Testing Incremental Data ===" << std::endl;
        
        std::string base = "Test";
        std::string extended = "Test data";
        std::string longer = "Test data with more content";
        
        unsigned long crc1 = memcrc(base.c_str(), base.length());
        unsigned long crc2 = memcrc(extended.c_str(), extended.length());
        unsigned long crc3 = memcrc(longer.c_str(), longer.length());
        
        print_crc_result(crc1, "\"Test\" CRC");
        print_crc_result(crc2, "\"Test data\" CRC");
        print_crc_result(crc3, "\"Test data with more content\" CRC");
        
        // All should be different
        assert_test(crc1 != crc2, "Base and extended strings have different CRCs");
        assert_test(crc2 != crc3, "Extended and longer strings have different CRCs");
        assert_test(crc1 != crc3, "Base and longer strings have different CRCs");
    }

    void test_binary_data() {
        std::cout << "\n=== Testing Binary Data CRC ===" << std::endl;
        
        // Create binary data with all byte values
        std::string binary_data;
        for (int i = 0; i < 256; i++) {
            binary_data += static_cast<char>(i);
        }
        
        unsigned long crc = memcrc(binary_data.c_str(), binary_data.length());
        print_crc_result(crc, "Binary data (0-255) CRC");
        
        assert_test(crc != 0, "Binary data CRC is not zero");
        
        // Test partial binary data
        std::string partial_binary = binary_data.substr(0, 128);
        unsigned long partial_crc = memcrc(partial_binary.c_str(), partial_binary.length());
        print_crc_result(partial_crc, "Partial binary data (0-127) CRC");
        
        assert_test(crc != partial_crc, "Full and partial binary data have different CRCs");
    }

    void test_large_data() {
        std::cout << "\n=== Testing Large Data CRC ===" << std::endl;
        
        // Create large data (10KB)
        std::string large_data;
        for (int i = 0; i < 10240; i++) {
            large_data += static_cast<char>('A' + (i % 26));
        }
        
        unsigned long crc = memcrc(large_data.c_str(), large_data.length());
        print_crc_result(crc, "Large data (10KB) CRC");
        
        assert_test(crc != 0, "Large data CRC is not zero");
        
        std::cout << "Large data size: " << large_data.length() << " bytes" << std::endl;
    }

    void test_consistency() {
        std::cout << "\n=== Testing CRC Consistency ===" << std::endl;
        
        std::string test_data = "Consistency test data for CRC calculation";
        
        // Calculate CRC multiple times
        unsigned long crc1 = memcrc(test_data.c_str(), test_data.length());
        unsigned long crc2 = memcrc(test_data.c_str(), test_data.length());
        unsigned long crc3 = memcrc(test_data.c_str(), test_data.length());
        
        print_crc_result(crc1, "First calculation");
        print_crc_result(crc2, "Second calculation");
        print_crc_result(crc3, "Third calculation");
        
        assert_test(crc1 == crc2, "First and second calculations match");
        assert_test(crc2 == crc3, "Second and third calculations match");
        assert_test(crc1 == crc3, "First and third calculations match");
    }

    void test_null_terminator_handling() {
        std::cout << "\n=== Testing Null Terminator Handling ===" << std::endl;
        
        // Test data with embedded null bytes
        std::string with_null = "Test\0data";
        with_null.resize(9); // Ensure the null byte is included
        
        std::string without_null = "Testdata";
        
        unsigned long crc_with = memcrc(with_null.c_str(), with_null.length());
        unsigned long crc_without = memcrc(without_null.c_str(), without_null.length());
        
        print_crc_result(crc_with, "Data with null byte CRC");
        print_crc_result(crc_without, "Data without null byte CRC");
        
        assert_test(crc_with != crc_without, "Data with and without null bytes have different CRCs");
        
        std::cout << "With null length: " << with_null.length() << " bytes" << std::endl;
        std::cout << "Without null length: " << without_null.length() << " bytes" << std::endl;
    }

    void test_file_simulation() {
        std::cout << "\n=== Testing File Content Simulation ===" << std::endl;
        
        // Simulate the exact content that was successfully transferred
        std::string file_content = "This is a test file for the secure backup system.\nIt contains multiple lines.\nAnd some special characters: !@#$%^&*()\n";
        
        unsigned long crc = memcrc(file_content.c_str(), file_content.length());
        print_crc_result(crc, "Simulated file content CRC");
        
        std::cout << "File content length: " << file_content.length() << " bytes" << std::endl;
        std::cout << "Expected from successful transfer: 0x73dbfba4" << std::endl;
        
        // Check if this matches the known good CRC
        bool matches_expected = (crc == 0x73dbfba4);
        assert_test(matches_expected, "CRC matches expected value from successful transfer");
        
        if (!matches_expected) {
            std::cout << "Note: CRC mismatch might be due to different file content or line endings" << std::endl;
        }
    }

    void run_all_tests() {
        std::cout << "🔍 CRC/cksum Unit Tests" << std::endl;
        std::cout << "=======================" << std::endl;
        
        test_empty_data();
        test_known_values();
        test_single_bytes();
        test_incremental_data();
        test_binary_data();
        test_large_data();
        test_consistency();
        test_null_terminator_handling();
        test_file_simulation();
        
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
        CksumTest test;
        test.run_all_tests();
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "❌ Test execution failed: " << e.what() << std::endl;
        return 1;
    }
}
