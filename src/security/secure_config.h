/**
 * Secure Configuration Management for Harmonic IoT Protocol
 *
 * Header file for secure configuration, password hashing, JWT tokens,
 * and encryption functionality.
 *
 * Copyright (c) 2025 Guilherme Gonçalves Machado
 * Licensed under CC BY-NC-SA 4.0
 */

#ifndef HARMONIC_IOT_SECURE_CONFIG_H
#define HARMONIC_IOT_SECURE_CONFIG_H

#include <string>
#include <vector>
#include <memory>

namespace harmonic_iot {
namespace security {

/**
 * Secure Configuration Manager
 *
 * Provides secure configuration management including:
 * - Argon2id password hashing
 * - JWT token generation and verification
 * - AES-256-GCM encryption/decryption
 * - Environment variable loading
 * - Secure random string generation
 */
class SecureConfig {
public:
    /**
     * Constructor - initializes secure configuration
     * Loads configuration from environment variables
     */
    SecureConfig();

    /**
     * Hash password using Argon2id
     *
     * @param password Plain text password
     * @param salt Optional salt (generated if empty)
     * @return Base64 encoded hash with salt
     */
    std::string hashPassword(const std::string& password, const std::string& salt = "");

    /**
     * Verify password against stored hash
     *
     * @param password Plain text password
     * @param hash Stored hash with salt
     * @return True if password matches
     */
    bool verifyPassword(const std::string& password, const std::string& hash);

    /**
     * Generate JWT access token
     *
     * @param user_id User identifier
     * @param role User role
     * @param expires_in_minutes Token expiration (default: 15 minutes)
     * @return JWT token string
     */
    std::string generateJWTToken(const std::string& user_id,
                                const std::string& role,
                                int expires_in_minutes = 15);

    /**
     * Generate JWT refresh token
     *
     * @param user_id User identifier
     * @return Refresh token string (7 days expiration)
     */
    std::string generateRefreshToken(const std::string& user_id);

    /**
     * Verify JWT token and extract claims
     *
     * @param token JWT token to verify
     * @param user_id Output parameter for user ID
     * @param role Output parameter for user role
     * @return True if token is valid
     */
    bool verifyJWTToken(const std::string& token, std::string& user_id, std::string& role);

    /**
     * Encrypt sensitive data using AES-256-GCM
     *
     * @param plaintext Data to encrypt
     * @return Base64 encoded encrypted data with IV and tag
     */
    std::string encryptData(const std::string& plaintext);

    /**
     * Decrypt sensitive data using AES-256-GCM
     *
     * @param ciphertext_b64 Base64 encoded encrypted data
     * @return Decrypted plaintext
     */
    std::string decryptData(const std::string& ciphertext_b64);

    /**
     * Generate cryptographically secure random string
     *
     * @param length Length of random string
     * @return Random string
     */
    std::string generateRandomString(size_t length);

    // Getters for configuration
    const std::string& getDatabaseUrl() const { return database_url_; }
    const std::string& getEncryptionKey() const { return encryption_key_; }
    const std::string& getJWTSecret() const { return jwt_secret_; }

private:
    // Configuration variables
    std::string database_url_;
    std::string encryption_key_;
    std::string jwt_secret_;
    std::string jwt_private_key_;
    std::string jwt_public_key_;

    /**
     * Load configuration from environment variables
     */
    void loadEnvironmentConfig();

    /**
     * Generate JWT signing keys
     */
    void generateJWTKeys();

    /**
     * Base64 encode binary data
     */
    std::string encodeBase64(const std::vector<uint8_t>& data);

    /**
     * Base64 decode to binary data
     */
    std::vector<uint8_t> decodeBase64(const std::string& encoded);
};

} // namespace security
} // namespace harmonic_iot

#endif // HARMONIC_IOT_SECURE_CONFIG_H
