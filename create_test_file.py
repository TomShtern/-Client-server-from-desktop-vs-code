# Simple testing script for backup client
import os
import sys
import random
import string

# Create a test file
def create_test_file(filename, size_kb):
    """Create a test file with random content of specified size in KB"""
    with open(filename, 'w') as f:
        # Generate random content
        for _ in range(size_kb):
            # Write about 1KB of random data per iteration
            f.write(''.join(random.choices(string.ascii_letters + string.digits, k=1024)))
    
    print(f"Created test file: {filename} ({size_kb} KB)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_test_file.py <filename> <size_kb>")
        sys.exit(1)
    
    filename = sys.argv[1]
    try:
        size_kb = int(sys.argv[2])
    except ValueError:
        print("Error: size must be an integer (KB)")
        sys.exit(1)
    
    create_test_file(filename, size_kb)
    print(f"File created successfully: {os.path.abspath(filename)}")
