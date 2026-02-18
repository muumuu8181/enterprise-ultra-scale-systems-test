cmake_minimum_required(VERSION 3.10)
project(TradingSystem VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add source files
file(GLOB_RECURSE SOURCES "src/*.cpp")

# Create executable
add_executable(trading_system ${SOURCES})

# Include directories
target_include_directories(trading_system PRIVATE src)
