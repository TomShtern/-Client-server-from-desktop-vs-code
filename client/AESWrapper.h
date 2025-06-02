#pragma once

#include <string>

// Placeholder for memcpy_s if not available (e.g. on non-Windows/non-C++11 standard lib)
#if defined(_MSC_VER) || __cplusplus >= 201103L
#include <cstring> // For memcpy_s or memcpy
#else
// Manual definition or alternative for older systems
#include <string.h> // For memcpy
#define memcpy_s(dest, destsz, src, count) memcpy(dest, src, count)
#endif

class AESWrapper
{
public:
	// CRITICAL FIX: Changed from 16 to 32 for AES-256 compliance
	static const unsigned int DEFAULT_KEYLENGTH = 32;
private:
	unsigned char _key[DEFAULT_KEYLENGTH];
	AESWrapper(const AESWrapper& aes); // Declared private, not defined (copy constructor)
    // AESWrapper& operator=(const AESWrapper& aes); // Should also declare copy assignment
public:
	static unsigned char* GenerateKey(unsigned char* buffer, unsigned int length);

	AESWrapper();
	AESWrapper(const unsigned char* key, unsigned int size);
	~AESWrapper();

	const unsigned char* getKey() const;

	std::string encrypt(const char* plain, unsigned int length);
	std::string decrypt(const char* cipher, unsigned int length);
};
