package com.corp.base.crypto;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Base64;
import java.util.Objects;

/**
 * AES encryptor supporting AES-128 / AES-256 in CBC or GCM mode.
 *
 * <p>The IV/nonce is prepended to the ciphertext for both modes so the same
 * key can be reused safely.
 */
public class AesEncryptor {

    public enum Mode {
        CBC("AES/CBC/PKCS5Padding"),
        GCM("AES/GCM/NoPadding");

        private final String transformation;

        Mode(String transformation) {
            this.transformation = transformation;
        }

        public String getTransformation() {
            return transformation;
        }
    }

    /** AES key length in bits. */
    public static final int KEY_128 = 128;
    public static final int KEY_256 = 256;

    /** GCM tag length in bits. */
    private static final int GCM_TAG_BITS = 128;

    private static final SecureRandom RNG = new SecureRandom();

    private final SecretKey secretKey;
    private final Mode mode;

    public AesEncryptor(byte[] keyBytes, Mode mode) {
        Objects.requireNonNull(keyBytes, "key");
        Objects.requireNonNull(mode, "mode");
        if (keyBytes.length != 16 && keyBytes.length != 32) {
            throw new IllegalArgumentException(
                    "AES key must be 16 (AES-128) or 32 (AES-256) bytes, got " + keyBytes.length);
        }
        this.secretKey = new SecretKeySpec(keyBytes, "AES");
        this.mode = mode;
    }

    public AesEncryptor(String base64Key, Mode mode) {
        this(Base64.getDecoder().decode(base64Key), mode);
    }

    /** Generate a fresh AES key of the requested length. */
    public static byte[] generateKey(int keyBits) {
        try {
            if (keyBits != KEY_128 && keyBits != KEY_256) {
                throw new IllegalArgumentException("Unsupported key length: " + keyBits);
            }
            KeyGenerator kg = KeyGenerator.getInstance("AES");
            kg.init(keyBits, RNG);
            return kg.generateKey().getEncoded();
        } catch (Exception e) {
            throw new IllegalStateException("Failed to generate AES key", e);
        }
    }

    /** Encrypt UTF-8 text, returning a Base64 string containing IV + ciphertext. */
    public String encrypt(String plaintext) {
        if (plaintext == null) {
            return null;
        }
        byte[] cipher = encrypt(plaintext.getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(cipher);
    }

    /** Encrypt raw bytes, returning IV + ciphertext. */
    public byte[] encrypt(byte[] plaintext) {
        try {
            Cipher cipher = Cipher.getInstance(mode.getTransformation());
            if (mode == Mode.GCM) {
                byte[] nonce = new byte[12];
                RNG.nextBytes(nonce);
                cipher.init(Cipher.ENCRYPT_MODE, secretKey, new GCMParameterSpec(GCM_TAG_BITS, nonce));
                byte[] encrypted = cipher.doFinal(plaintext);
                return concat(nonce, encrypted);
            } else {
                byte[] iv = new byte[16];
                RNG.nextBytes(iv);
                cipher.init(Cipher.ENCRYPT_MODE, secretKey, new IvParameterSpec(iv));
                byte[] encrypted = cipher.doFinal(plaintext);
                return concat(iv, encrypted);
            }
        } catch (Exception e) {
            throw new IllegalStateException("AES encryption failed", e);
        }
    }

    /** Decrypt a Base64 string produced by {@link #encrypt(String)}. */
    public String decrypt(String base64Cipher) {
        if (base64Cipher == null) {
            return null;
        }
        byte[] plain = decrypt(Base64.getDecoder().decode(base64Cipher));
        return new String(plain, StandardCharsets.UTF_8);
    }

    /** Decrypt raw bytes (IV + ciphertext). */
    public byte[] decrypt(byte[] ivAndCipher) {
        try {
            int ivLen = (mode == Mode.GCM) ? 12 : 16;
            if (ivAndCipher == null || ivAndCipher.length <= ivLen) {
                throw new IllegalArgumentException("Invalid ciphertext");
            }
            byte[] iv = Arrays.copyOfRange(ivAndCipher, 0, ivLen);
            byte[] cipherBytes = Arrays.copyOfRange(ivAndCipher, ivLen, ivAndCipher.length);

            Cipher cipher = Cipher.getInstance(mode.getTransformation());
            if (mode == Mode.GCM) {
                cipher.init(Cipher.DECRYPT_MODE, secretKey, new GCMParameterSpec(GCM_TAG_BITS, iv));
            } else {
                cipher.init(Cipher.DECRYPT_MODE, secretKey, new IvParameterSpec(iv));
            }
            return cipher.doFinal(cipherBytes);
        } catch (Exception e) {
            throw new IllegalStateException("AES decryption failed", e);
        }
    }

    private static byte[] concat(byte[] a, byte[] b) {
        byte[] out = new byte[a.length + b.length];
        System.arraycopy(a, 0, out, 0, a.length);
        System.arraycopy(b, 0, out, a.length, b.length);
        return out;
    }
}
