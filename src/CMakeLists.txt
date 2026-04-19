cmake_minimum_required(VERSION 3.10)

project(HarmonicProtocol
    VERSION 1.0.0
    DESCRIPTION "Harmonic IoT Protocol - Proof of Concept"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# ─── Core executable ──────────────────────────────────────────────────────────
add_executable(harmonic_protocol main.cpp)

set_target_properties(harmonic_protocol PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

install(TARGETS harmonic_protocol RUNTIME DESTINATION bin)

# ─── Security module (opt-in) ─────────────────────────────────────────────────
# Build with: cmake .. -DENABLE_SECURITY=ON
# Requires: libssl-dev libargon2-dev jwt-cpp (header-only)
#
# Ubuntu/Debian:  sudo apt-get install libssl-dev libargon2-dev
# macOS:          brew install openssl argon2
# jwt-cpp:        https://github.com/Thalhammer/jwt-cpp (header-only, copy to /usr/local/include)
option(ENABLE_SECURITY "Build security module (requires OpenSSL, argon2, jwt-cpp)" OFF)

if(ENABLE_SECURITY)
    find_package(OpenSSL REQUIRED)

    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(ARGON2 REQUIRED libargon2)
    else()
        # Fallback: search for argon2 manually
        find_library(ARGON2_LIBRARIES NAMES argon2 REQUIRED)
        find_path(ARGON2_INCLUDE_DIRS argon2.h REQUIRED)
    endif()

    # jwt-cpp is header-only — find its include path
    find_path(JWTCPP_INCLUDE_DIR jwt-cpp/jwt.h
        PATHS /usr/local/include /usr/include
        REQUIRED
    )

    add_library(harmonic_security STATIC
        security/secure_config.cpp
    )

    target_include_directories(harmonic_security PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${OPENSSL_INCLUDE_DIR}
        ${ARGON2_INCLUDE_DIRS}
        ${JWTCPP_INCLUDE_DIR}
    )

    target_link_libraries(harmonic_security
        OpenSSL::SSL
        OpenSSL::Crypto
        ${ARGON2_LIBRARIES}
    )

    message(STATUS "Security module: ENABLED")
    message(STATUS "  OpenSSL: ${OPENSSL_VERSION}")
    message(STATUS "  Argon2:  ${ARGON2_LIBRARIES}")
    message(STATUS "  jwt-cpp: ${JWTCPP_INCLUDE_DIR}")
else()
    message(STATUS "Security module: DISABLED (use -DENABLE_SECURITY=ON to enable)")
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID}")
