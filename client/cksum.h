#pragma once

#include <cstddef>

/**
 * Calculate Linux cksum compatible checksum
 * This is the exact same algorithm used by the Linux cksum command
 * and ported to the Python server.
 * 
 * @param b Pointer to data buffer
 * @param n Size of data in bytes
 * @return CRC32 checksum value
 */
unsigned long memcrc(const char* b, size_t n);
