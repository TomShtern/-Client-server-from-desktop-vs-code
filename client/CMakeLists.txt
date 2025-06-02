cmake_minimum_required(VERSION 3.20)
project(SecureBackupClient)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(cryptopp CONFIG REQUIRED)
find_package(Boost REQUIRED)

# Add wrapper test executable
add_executable(test_wrappers
    AESWrapper.cpp
    RSAWrapper.cpp
    Base64Wrapper.cpp
    cksum.cpp
    test_wrappers.cpp
)

# Add TCP client executable
add_executable(tcp_client
    AESWrapper.cpp
    RSAWrapper.cpp
    Base64Wrapper.cpp
    cksum.cpp
    tcp_client.cpp
    tcp_client_file_ops.cpp
    main.cpp
)

# Link libraries
target_link_libraries(test_wrappers PRIVATE cryptopp::cryptopp)
target_link_libraries(tcp_client PRIVATE cryptopp::cryptopp)

# Include Boost headers (header-only for what we need)
target_include_directories(test_wrappers PRIVATE ${Boost_INCLUDE_DIRS})
target_include_directories(tcp_client PRIVATE ${Boost_INCLUDE_DIRS})

# Windows-specific libraries
if(WIN32)
    target_link_libraries(test_wrappers PRIVATE ws2_32)
    target_link_libraries(tcp_client PRIVATE ws2_32)
endif()

# Set output directory
set_target_properties(test_wrappers PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)
set_target_properties(tcp_client PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)
