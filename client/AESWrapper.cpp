#include "AESWrapper.h"

// CryptoPP Includes - these would be needed for the code to compile
#include <cryptopp/modes.h>
#include <cryptopp/aes.h>
#include <cryptopp/filters.h>

#include <stdexcept> // For std::length_error, std::runtime_error

// _rdrand32_step might require specific compiler flags or intrinsics headers
// For MSVC: <immintrin.h>
// For GCC/Clang: <x86intrin.h> or <immintrin.h> with -mrdrnd flag
#if defined(_MSC_VER)
#include <immintrin.h>
#elif defined(__GNUC__) || defined(__clang__)
    #if defined(__RDRND__) // Check if RDRAND is enabled by compiler flags
        #include <immintrin.h> // or <x86intrin.h>
    #else
        // Fallback or error if RDRAND intrinsic is not available/enabled
        // This is a simple random number generator as a fallback
        #warning "RDRAND intrinsic not available or not enabled. Using pseudo-random fallback for AESWrapper::GenerateKey."
        #include <cstdlib> // For rand()
        #include <ctime>   // For time() for seeding
        bool rdrand_fallback_seeded = false;
        void _rdrand32_step(unsigned int* val) {
            if (!rdrand_fallback_seeded) {
                srand(static_cast<unsigned int>(time(0)));
                rdrand_fallback_seeded = true;
            }
            *val = rand();
        }
    #endif
#else
    // Fallback for other compilers
    #warning "RDRAND intrinsic not available for this compiler. Using pseudo-random fallback for AESWrapper::GenerateKey."
    #include <cstdlib> // For rand()
    #include <ctime>   // For time() for seeding
    bool rdrand_fallback_seeded_other = false;
    void _rdrand32_step(unsigned int* val) {
        if (!rdrand_fallback_seeded_other) {
            srand(static_cast<unsigned int>(time(0)));
            rdrand_fallback_seeded_other = true;
        }
        *val = rand();
    }
#endif

unsigned char* AESWrapper::GenerateKey(unsigned char* buffer, unsigned int length)
{
	for (size_t i = 0; i < length; i += sizeof(unsigned int)) {
        unsigned int random_val;
		_rdrand32_step(&random_val);
        // Ensure we don't write past the buffer if length is not a multiple of sizeof(unsigned int)
        size_t bytes_to_copy = sizeof(unsigned int);
        if (i + sizeof(unsigned int) > length) {
            bytes_to_copy = length - i;
        }
        memcpy(&buffer[i], &random_val, bytes_to_copy);
    }
	return buffer;
}

AESWrapper::AESWrapper()
{
	GenerateKey(_key, DEFAULT_KEYLENGTH);
}

AESWrapper::AESWrapper(const unsigned char* key, unsigned int length)
{
	// CRITICAL FIX: Changed from 16 to 32 bytes for AES-256 compliance
	if (length != DEFAULT_KEYLENGTH)
		throw std::length_error("key length must be 32 bytes");
	memcpy_s(_key, DEFAULT_KEYLENGTH, key, length);
}

AESWrapper::~AESWrapper()
{
}

const unsigned char* AESWrapper::getKey() const 
{ 
	return _key; 
}

std::string AESWrapper::encrypt(const char* plain, unsigned int length)
{
	CryptoPP::byte iv[CryptoPP::AES::BLOCKSIZE] = { 0 };	// for practical use iv should never be a fixed value!

	CryptoPP::AES::Encryption aesEncryption(_key, DEFAULT_KEYLENGTH);
	CryptoPP::CBC_Mode_ExternalCipher::Encryption cbcEncryption(aesEncryption, iv);

	std::string cipher;
	CryptoPP::StreamTransformationFilter stfEncryptor(cbcEncryption, new CryptoPP::StringSink(cipher));
	stfEncryptor.Put(reinterpret_cast<const CryptoPP::byte*>(plain), length);
	stfEncryptor.MessageEnd();
	return cipher;
}

std::string AESWrapper::decrypt(const char* cipher, unsigned int length)
{
	CryptoPP::byte iv[CryptoPP::AES::BLOCKSIZE] = { 0 };	// for practical use iv should never be a fixed value!
	
	CryptoPP::AES::Decryption aesDecryption(_key, DEFAULT_KEYLENGTH);
	CryptoPP::CBC_Mode_ExternalCipher::Decryption cbcDecryption(aesDecryption, iv);

	std::string decrypted;
	CryptoPP::StreamTransformationFilter stfDecryptor(cbcDecryption, new CryptoPP::StringSink(decrypted));
	stfDecryptor.Put(reinterpret_cast<const CryptoPP::byte*>(cipher), length);
	stfDecryptor.MessageEnd();
	return decrypted;
}
