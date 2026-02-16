cmake_minimum_required(VERSION 3.10)
project(V2XSystem)

set(CMAKE_CXX_STANDARD 17)

# Include directories
include_directories(include)

# V2X Library
add_library(v2x
    src/v2x/comm_manager.cpp
)

# Test Executable
add_executable(test_v2x tests/test_v2x.cpp)
target_link_libraries(test_v2x v2x)
