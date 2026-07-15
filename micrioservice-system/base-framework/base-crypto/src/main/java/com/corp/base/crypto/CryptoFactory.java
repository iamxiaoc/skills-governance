package com.corp.base.crypto;

import java.util.Locale;
import java.util.Objects;

/**
 * Factory that creates encryptor instances based on algorithm identifier.
 *
 * <p>Supported algorithms: {@code AES-128-CBC}, {@code AES-256-CBC},
 * {@code AES-128-GCM}, {@code AES-256-GCM}, {@code RSA}, {@code SM2}, {@code SM4}.
 */
public final class CryptoFactory {

    public enum AlgorithmType {
        AES_128_CBC,
        AES_256_CBC,
        AES_128_GCM,
        AES_256_GCM,
        RSA,
        SM2,
        SM4
    }

    private CryptoFactory() {
    }

    /**
     * Resolve an algorithm type from a string identifier such as
     * {@code "AES-256-GCM"} or {@code "sm2"}.
     */
    public static AlgorithmType resolve(String algorithm) {
        Objects.requireNonNull(algorithm, "algorithm");
        String normalized = algorithm.trim().toUpperCase(Locale.ROOT)
                .replace("-", "_")
                .replace("/", "_");
        try {
            return AlgorithmType.valueOf(normalized);
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("Unsupported algorithm: " + algorithm);
        }
    }

    /**
     * Create an {@link AesEncryptor} for the given AES variant.
     *
     * @param keyBytes raw key bytes (16 or 32 bytes long depending on variant)
     */
    public static AesEncryptor createAes(AlgorithmType type, byte[] keyBytes) {
        return switch (type) {
            case AES_128_CBC, AES_256_CBC -> new AesEncryptor(keyBytes, AesEncryptor.Mode.CBC);
            case AES_128_GCM, AES_256_GCM -> new AesEncryptor(keyBytes, AesEncryptor.Mode.GCM);
            default -> throw new IllegalArgumentException("Not an AES variant: " + type);
        };
    }

    /**
     * Create an AES encryptor by auto-generating a key of the right length.
     */
    public static AesEncryptor createAesWithGeneratedKey(AlgorithmType type) {
        int keyBits = switch (type) {
            case AES_128_CBC, AES_128_GCM -> AesEncryptor.KEY_128;
            case AES_256_CBC, AES_256_GCM -> AesEncryptor.KEY_256;
            default -> throw new IllegalArgumentException("Not an AES variant: " + type);
        };
        return createAes(type, AesEncryptor.generateKey(keyBits));
    }

    /**
     * Create an {@link RsaEncryptor} from Base64-encoded keys. Either key may
     * be null when only signing or only encryption is needed.
     */
    public static RsaEncryptor createRsa(String base64PublicKey, String base64PrivateKey) throws Exception {
        return new RsaEncryptor(base64PublicKey, base64PrivateKey);
    }

    /**
     * Create an SM2 encryptor.
     */
    public static SmEncryptor createSm2(String base64PublicKey, String base64PrivateKey) throws Exception {
        return new SmEncryptor(base64PublicKey, base64PrivateKey);
    }

    /**
     * Create an SM4 encryptor.
     */
    public static SmEncryptor createSm4(byte[] key) {
        return new SmEncryptor(key);
    }

    /**
     * Convenience: create an encryptor by algorithm string, delegating to the
     * type-specific factory methods.
     */
    public static Object create(String algorithm, Object... params) throws Exception {
        AlgorithmType type = resolve(algorithm);
        switch (type) {
            case AES_128_CBC, AES_256_CBC, AES_128_GCM, AES_256_GCM -> {
                byte[] key = params.length > 0 ? (byte[]) params[0] : null;
                if (key == null) {
                    return createAesWithGeneratedKey(type);
                }
                return createAes(type, key);
            }
            case RSA -> {
                String pub = params.length > 0 ? (String) params[0] : null;
                String priv = params.length > 1 ? (String) params[1] : null;
                return createRsa(pub, priv);
            }
            case SM2 -> {
                String pub = params.length > 0 ? (String) params[0] : null;
                String priv = params.length > 1 ? (String) params[1] : null;
                return createSm2(pub, priv);
            }
            case SM4 -> {
                byte[] key = (byte[]) params[0];
                return createSm4(key);
            }
            default -> throw new IllegalArgumentException("Unsupported type: " + type);
        }
    }
}
