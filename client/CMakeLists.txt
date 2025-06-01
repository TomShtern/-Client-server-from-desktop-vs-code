# CMakeLists.txt for C++ backup client
# NOTE: This CMake is for the HTTP-based client (current implementation)
# The specifications require a different binary TCP client with Crypto++ and Boost.Asio

cmake_minimum_required(VERSION 3.10)
project(backup_client)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Option to build HTTP client (current) or TCP client (specifications)
option(BUILD_HTTP_CLIENT "Build HTTP-based client (current implementation)" ON)
option(BUILD_TCP_CLIENT "Build TCP-based client (per specifications)" OFF)

if(BUILD_HTTP_CLIENT)
    # HTTP Client (current implementation)
    find_package(CURL REQUIRED)
    include_directories(${CURL_INCLUDE_DIRS})

    add_executable(http_client client.cpp)
    target_link_libraries(http_client ${CURL_LIBRARIES})

    install(TARGETS http_client DESTINATION bin)
endif()

if(BUILD_TCP_CLIENT)
    # TCP Client (per specifications) - requires Crypto++ and Boost
    # find_package(cryptopp REQUIRED)
    # find_package(Boost REQUIRED COMPONENTS system)

    # add_executable(tcp_client tcp_client.cpp)
    # target_link_libraries(tcp_client cryptopp Boost::system)

    message(STATUS "TCP client build not implemented yet - requires Crypto++ and Boost.Asio")
endif()
