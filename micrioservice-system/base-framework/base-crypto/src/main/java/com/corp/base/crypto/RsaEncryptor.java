package com.corp.base.crypto;

import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import java.util.Objects;

import javax.crypto.Cipher;

/**
 * RSA encryptor supporting public-key encrypt / private-key decrypt and
 * signature verification.
 *
 * <p>Uses SHA256withRSA for signing. Cipher transformation is
 * {@code RSA/ECB/PKCS1Padding} which is suitable for short payloads and key
 * wrapping; for larger payloads a hybrid scheme with AES is recommended.
 */
public class RsaEncryptor {

    private static final String CIPHER_TRANSFORMATION = "RSA/ECB/PKCS1Padding";
    private static final String SIGNATURE_ALGORITHM = "SHA256withRSA";
    private static final int MAX_ENCRYPT_BLOCK = 117; // 1024-bit key
    private static final int MAX_DECRYPT_BLOCK = 128;

    private final PublicKey publicKey;
    private final PrivateKey privateKey;

    public RsaEncryptor(String base64PublicKey, String base64PrivateKey) throws Exception {
        this.publicKey = base64PublicKey == null ? null : toPublicKey(base64PublicKey);
        this.privateKey = base64PrivateKey == null ? null : toPrivateKey(base64PrivateKey);
        if (publicKey == null && privateKey == null) {
            throw new IllegalArgumentException("At least one of public/private key must be provided");
        }
    }

    public RsaEncryptor(PublicKey publicKey, PrivateKey privateKey) {
        if (publicKey == null && privateKey == null) {
            throw new IllegalArgumentException("At least one of public/private key must be provided");
        }
        this.publicKey = publicKey;
        this.privateKey = privateKey;
    }

    // ---------- key conversion helpers ----------
    public static PublicKey toPublicKey(String base64) throws Exception {
        Objects.requireNonNull(base64, "public key");
        byte[] decoded = Base64.getDecoder().decode(base64);
        return KeyFactory.getInstance("RSA").generatePublic(new X509EncodedKeySpec(decoded));
    }

    public static PrivateKey toPrivateKey(String base64) throws Exception {
        Objects.requireNonNull(base64, "private key");
        byte[] decoded = Base64.getDecoder().decode(base64);
        return KeyFactory.getInstance("RSA").generatePrivate(new PKCS8EncodedKeySpec(decoded));
    }

    // ---------- encrypt / decrypt ----------
    public String encryptWithPublicKey(String plaintext) {
        if (publicKey == null) {
            throw new IllegalStateException("Public key not configured");
        }
        byte[] data = plaintext.getBytes(StandardCharsets.UTF_8);
        return Base64.getEncoder().encodeToString(doEncrypt(data, publicKey));
    }

    public String decryptWithPrivateKey(String base64Cipher) {
        if (privateKey == null) {
            throw new IllegalStateException("Private key not configured");
        }
        byte[] data = Base64.getDecoder().decode(base64Cipher);
        return new String(doDecrypt(data, privateKey), StandardCharsets.UTF_8);
    }

    private byte[] doEncrypt(byte[] data, PublicKey key) {
        try {
            Cipher cipher = Cipher.getInstance(CIPHER_TRANSFORMATION);
            cipher.init(Cipher.ENCRYPT_MODE, key);
            return segmentalProcess(cipher, data, MAX_ENCRYPT_BLOCK);
        } catch (Exception e) {
            throw new IllegalStateException("RSA encryption failed", e);
        }
    }

    private byte[] doDecrypt(byte[] data, PrivateKey key) {
        try {
            Cipher cipher = Cipher.getInstance(CIPHER_TRANSFORMATION);
            cipher.init(Cipher.DECRYPT_MODE, key);
            return segmentalProcess(cipher, data, MAX_DECRYPT_BLOCK);
        } catch (Exception e) {
            throw new IllegalStateException("RSA decryption failed", e);
        }
    }

    private byte[] segmentalProcess(Cipher cipher, byte[] data, int blockSize) throws Exception {
        java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
        int offset = 0;
        while (offset < data.length) {
            int len = Math.min(blockSize, data.length - offset);
            out.write(cipher.doFinal(data, offset, len));
            offset += len;
        }
        return out.toByteArray();
    }

    // ---------- signing ----------
    public String sign(String content) {
        if (privateKey == null) {
            throw new IllegalStateException("Private key not configured");
        }
        try {
            Signature sig = Signature.getInstance(SIGNATURE_ALGORITHM);
            sig.initSign(privateKey);
            sig.update(content.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(sig.sign());
        } catch (Exception e) {
            throw new IllegalStateException("RSA signing failed", e);
        }
    }

    public boolean verify(String content, String base64Signature) {
        if (publicKey == null) {
            throw new IllegalStateException("Public key not configured");
        }
        try {
            Signature sig = Signature.getInstance(SIGNATURE_ALGORITHM);
            sig.initVerify(publicKey);
            sig.update(content.getBytes(StandardCharsets.UTF_8));
            return sig.verify(Base64.getDecoder().decode(base64Signature));
        } catch (Exception e) {
            throw new IllegalStateException("RSA verification failed", e);
        }
    }
}
