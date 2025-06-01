# CMakeLists.txt for C++ backup client

cmake_minimum_required(VERSION 3.10)
project(backup_client)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find CURL package
find_package(CURL REQUIRED)
include_directories(${CURL_INCLUDE_DIRS})

# Define the executable
add_executable(client client.cpp)

# Link against CURL library
target_link_libraries(client ${CURL_LIBRARIES})

# Add installation rules
install(TARGETS client DESTINATION bin)
