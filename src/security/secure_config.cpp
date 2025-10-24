/**
 * Secure Configuration Management for Harmonic IoT Protocol
 *
 * Implements Argon2id password hashing, JWT token management,
 * and secure credential handling for production environments.
 *
 * Copyright (c) 2025 Guilherme Gonçalves Machado
 * Licensed under CC BY-NC-SA 4.0
 */

#include "secure_config.h"
#include <argon2.h>
#include <jwt-cpp/jwt.h>
#include <openssl/rand.h>
#include <openssl/evp.h>
#include <cstdlib>
#include <stdexcept>
#include <chrono>
#include <iostream>

namespace harmonic_iot {
namespace security {

SecureConfig::SecureConfig() {
    // Initialize OpenSSL
    if (!RAND_status()) {
        throw std::runtime_error("OpenSSL random number generator not properly seeded");
    }

    // Load configuration from environment variables
    loadEnvironmentConfig();

    // Generate JWT keys if not provided
    if (jwt_private_key_.empty() || jwt_public_key_.empty()) {
        generateJWTKeys();
    }
}

void SecureConfig::loadEnvironmentConfig() {
    // Load JWT configuration
    const char* jwt_secret = std::getenv("JWT_SECRET");
    if (jwt_secret) {
        jwt_secret_ = std::string(jwt_secret);
    } else {
        // Generate random JWT secret if not provided
        jwt_secret_ = generateRandomString(64);
        std::cerr << "WARNING: JWT_SECRET not set, using generated secret" << std::endl;
    }

    const char* jwt_private_key = std::getenv("JWT_PRIVATE_KEY");
    if (jwt_private_key) {
        jwt_private_key_ = std::string(jwt_private_key);
    }

    const char* jwt_public_key = std::getenv("JWT_PUBLIC_KEY");
    if (jwt_public_key) {
        jwt_public_key_ = std::string(jwt_public_key);
    }

    // Load database configuration
    const char* db_url = std::getenv("DATABASE_URL");
    if (db_url) {
        database_url_ = std::string(db_url);
    } else {
        throw std::runtime_error("DATABASE_URL environment variable not set");
    }

    // Load encryption key
    const char* encryption_key = std::getenv("ENCRYPTION_KEY");
    if (encryption_key) {
        encryption_key_ = std::string(encryption_key);
    } else {
        encryption_key_ = generateRandomString(32);
        std::cerr << "WARNING: ENCRYPTION_KEY not set, using generated key" << std::endl;
    }
}

std::string SecureConfig::hashPassword(const std::string& password, const std::string& salt) {
    if (password.empty()) {
        throw std::invalid_argument("Password cannot be empty");
    }

    std::string actual_salt = salt;
    if (actual_salt.empty()) {
        actual_salt = generateRandomString(16);
    }

    // Argon2id parameters (OWASP recommended)
    const uint32_t t_cost = 3;      // 3 iterations
    const uint32_t m_cost = 65536;  // 64 MB memory
    const uint32_t parallelism = 4; // 4 threads
    const uint32_t hash_len = 32;   // 32 bytes output

    std::vector<uint8_t> hash(hash_len);

    int result = argon2id_hash_raw(
        t_cost, m_cost, parallelism,
        password.c_str(), password.length(),
        actual_salt.c_str(), actual_salt.length(),
        hash.data(), hash_len
    );

    if (result != ARGON2_OK) {
        throw std::runtime_error("Argon2id hashing failed: " + std::string(argon2_error_message(result)));
    }

    // Encode as base64
    return encodeBase64(hash) + ":" + encodeBase64(std::vector<uint8_t>(actual_salt.begin(), actual_salt.end()));
}

bool SecureConfig::verifyPassword(const std::string& password, const std::string& hash) {
    if (password.empty() || hash.empty()) {
        return false;
    }

    // Split hash and salt
    size_t colon_pos = hash.find(':');
    if (colon_pos == std::string::npos) {
        return false;
    }

    std::string stored_hash = hash.substr(0, colon_pos);
    std::string salt = hash.substr(colon_pos + 1);

    // Decode salt from base64
    std::vector<uint8_t> salt_bytes = decodeBase64(salt);
    std::string salt_str(salt_bytes.begin(), salt_bytes.end());

    // Hash the provided password with the stored salt
    std::string computed_hash = hashPassword(password, salt_str);

    // Compare only the hash part (before the colon)
    std::string computed_hash_only = computed_hash.substr(0, computed_hash.find(':'));

    return stored_hash == computed_hash_only;
}

std::string SecureConfig::generateJWTToken(const std::string& user_id, const std::string& role, int expires_in_minutes) {
    auto now = std::chrono::system_clock::now();
    auto exp = now + std::chrono::minutes(expires_in_minutes);

    auto token = jwt::create()
        .set_issuer("harmonic-iot-protocol")
        .set_type("JWT")
        .set_id(generateRandomString(16))
        .set_issued_at(now)
        .set_expires_at(exp)
        .set_payload_claim("user_id", jwt::claim(user_id))
        .set_payload_claim("role", jwt::claim(role))
        .set_payload_claim("harmonic_protocol_version", jwt::claim("1.1.0"))
        .sign(jwt::algorithm::hs256{jwt_secret_});

    return token;
}

std::string SecureConfig::generateRefreshToken(const std::string& user_id) {
    auto now = std::chrono::system_clock::now();
    auto exp = now + std::chrono::hours(24 * 7); // 7 days

    auto token = jwt::create()
        .set_issuer("harmonic-iot-protocol")
        .set_type("refresh")
        .set_id(generateRandomString(32))
        .set_issued_at(now)
        .set_expires_at(exp)
        .set_payload_claim("user_id", jwt::claim(user_id))
        .set_payload_claim("token_type", jwt::claim("refresh"))
        .sign(jwt::algorithm::hs256{jwt_secret_});

    return token;
}

bool SecureConfig::verifyJWTToken(const std::string& token, std::string& user_id, std::string& role) {
    try {
        auto verifier = jwt::verify()
            .allow_algorithm(jwt::algorithm::hs256{jwt_secret_})
            .with_issuer("harmonic-iot-protocol");

        auto decoded = jwt::decode(token);
        verifier.verify(decoded);

        // Extract claims
        if (decoded.has_payload_claim("user_id")) {
            user_id = decoded.get_payload_claim("user_id").as_string();
        }

        if (decoded.has_payload_claim("role")) {
            role = decoded.get_payload_claim("role").as_string();
        }

        return true;
    } catch (const std::exception& e) {
        std::cerr << "JWT verification failed: " << e.what() << std::endl;
        return false;
    }
}

std::string SecureConfig::encryptData(const std::string& plaintext) {
    if (plaintext.empty()) {
        return "";
    }

    // Generate random IV
    std::vector<uint8_t> iv(16);
    if (RAND_bytes(iv.data(), iv.size()) != 1) {
        throw std::runtime_error("Failed to generate random IV");
    }

    // Initialize encryption context
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        throw std::runtime_error("Failed to create encryption context");
    }

    // Initialize encryption with AES-256-GCM
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to initialize encryption");
    }

    // Set IV
    if (EVP_EncryptInit_ex(ctx, nullptr, nullptr,
                          reinterpret_cast<const uint8_t*>(encryption_key_.c_str()),
                          iv.data()) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to set encryption key and IV");
    }

    // Encrypt data
    std::vector<uint8_t> ciphertext(plaintext.length() + 16);
    int len;
    if (EVP_EncryptUpdate(ctx, ciphertext.data(), &len,
                         reinterpret_cast<const uint8_t*>(plaintext.c_str()),
                         plaintext.length()) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to encrypt data");
    }

    int ciphertext_len = len;

    // Finalize encryption
    if (EVP_EncryptFinal_ex(ctx, ciphertext.data() + len, &len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to finalize encryption");
    }

    ciphertext_len += len;

    // Get authentication tag
    std::vector<uint8_t> tag(16);
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag.data()) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to get authentication tag");
    }

    EVP_CIPHER_CTX_free(ctx);

    // Combine IV + ciphertext + tag and encode as base64
    std::vector<uint8_t> result;
    result.insert(result.end(), iv.begin(), iv.end());
    result.insert(result.end(), ciphertext.begin(), ciphertext.begin() + ciphertext_len);
    result.insert(result.end(), tag.begin(), tag.end());

    return encodeBase64(result);
}

std::string SecureConfig::decryptData(const std::string& ciphertext_b64) {
    if (ciphertext_b64.empty()) {
        return "";
    }

    // Decode from base64
    std::vector<uint8_t> data = decodeBase64(ciphertext_b64);

    if (data.size() < 32) { // IV (16) + tag (16) minimum
        throw std::runtime_error("Invalid ciphertext length");
    }

    // Extract IV, ciphertext, and tag
    std::vector<uint8_t> iv(data.begin(), data.begin() + 16);
    std::vector<uint8_t> tag(data.end() - 16, data.end());
    std::vector<uint8_t> ciphertext(data.begin() + 16, data.end() - 16);

    // Initialize decryption context
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        throw std::runtime_error("Failed to create decryption context");
    }

    // Initialize decryption with AES-256-GCM
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to initialize decryption");
    }

    // Set IV and key
    if (EVP_DecryptInit_ex(ctx, nullptr, nullptr,
                          reinterpret_cast<const uint8_t*>(encryption_key_.c_str()),
                          iv.data()) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to set decryption key and IV");
    }

    // Decrypt data
    std::vector<uint8_t> plaintext(ciphertext.size());
    int len;
    if (EVP_DecryptUpdate(ctx, plaintext.data(), &len, ciphertext.data(), ciphertext.size()) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to decrypt data");
    }

    int plaintext_len = len;

    // Set authentication tag
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, tag.data()) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to set authentication tag");
    }

    // Finalize decryption
    if (EVP_DecryptFinal_ex(ctx, plaintext.data() + len, &len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Failed to finalize decryption - authentication failed");
    }

    plaintext_len += len;
    EVP_CIPHER_CTX_free(ctx);

    return std::string(plaintext.begin(), plaintext.begin() + plaintext_len);
}

std::string SecureConfig::generateRandomString(size_t length) {
    std::vector<uint8_t> random_bytes(length);
    if (RAND_bytes(random_bytes.data(), length) != 1) {
        throw std::runtime_error("Failed to generate random bytes");
    }

    return encodeBase64(random_bytes).substr(0, length);
}

void SecureConfig::generateJWTKeys() {
    // For simplicity, we'll use HMAC with a strong secret
    // In production, consider using RSA keys for better security
    jwt_private_key_ = generateRandomString(64);
    jwt_public_key_ = jwt_private_key_; // HMAC uses same key for sign/verify
}

std::string SecureConfig::encodeBase64(const std::vector<uint8_t>& data) {
    // Simple base64 encoding implementation
    const std::string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string result;

    for (size_t i = 0; i < data.size(); i += 3) {
        uint32_t val = 0;
        int padding = 0;

        for (int j = 0; j < 3; j++) {
            val <<= 8;
            if (i + j < data.size()) {
                val |= data[i + j];
            } else {
                padding++;
            }
        }

        for (int j = 0; j < 4; j++) {
            if (j < 4 - padding) {
                result += chars[(val >> (18 - j * 6)) & 0x3F];
            } else {
                result += '=';
            }
        }
    }

    return result;
}

std::vector<uint8_t> SecureConfig::decodeBase64(const std::string& encoded) {
    // Simple base64 decoding implementation
    std::vector<uint8_t> result;
    std::vector<int> decode_table(256, -1);

    // Build decode table
    const std::string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    for (size_t i = 0; i < chars.length(); i++) {
        decode_table[chars[i]] = i;
    }

    for (size_t i = 0; i < encoded.length(); i += 4) {
        uint32_t val = 0;
        int padding = 0;

        for (int j = 0; j < 4; j++) {
            val <<= 6;
            if (i + j < encoded.length() && encoded[i + j] != '=') {
                val |= decode_table[encoded[i + j]];
            } else {
                padding++;
            }
        }

        for (int j = 0; j < 3 - padding; j++) {
            result.push_back((val >> (16 - j * 8)) & 0xFF);
        }
    }

    return result;
}

} // namespace security
} // namespace harmonic_iot
