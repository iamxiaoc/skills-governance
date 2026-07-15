package com.corp.base.crypto;

import org.bouncycastle.asn1.gm.GMNamedCurves;
import org.bouncycastle.asn1.x9.X9ECParameters;
import org.bouncycastle.crypto.engines.SM4Engine;
import org.bouncycastle.crypto.params.KeyParameter;
import org.bouncycastle.crypto.params.ParametersWithIV;
import org.bouncycastle.jcajce.provider.asymmetric.ec.BCECPrivateKey;
import org.bouncycastle.jcajce.provider.asymmetric.ec.BCECPublicKey;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.jce.spec.ECParameterSpec;
import org.bouncycastle.jce.spec.ECPrivateKeySpec;
import org.bouncycastle.jce.spec.ECPublicKeySpec;

import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.SecureRandom;
import java.security.Security;
import java.security.Signature;
import java.util.Base64;
import java.util.Objects;

/**
 * Chinese national cryptography (国密) encryptor covering SM2 (asymmetric)
 * and SM4 (symmetric) algorithms, backed by BouncyCastle.
 */
public class SmEncryptor {

    public static final String SM2_CURVE = "sm2p256v1";
    public static final String SM4_ALGORITHM = "SM4";
    public static final String SM2_SIGN_ALGORITHM = "SHA256withSM2";

    private static final X9ECParameters EC_PARAMETERS = GMNamedCurves.getByName(SM2_CURVE);
    private static final ECParameterSpec EC_SPEC =
            new ECParameterSpec(EC_PARAMETERS.getCurve(), EC_PARAMETERS.getG(),
                    EC_PARAMETERS.getN(), EC_PARAMETERS.getH());

    static {
        if (Security.getProvider(BouncyCastleProvider.PROVIDER_NAME) == null) {
            Security.addProvider(new BouncyCastleProvider());
        }
    }

    private final PublicKey sm2PublicKey;
    private final PrivateKey sm2PrivateKey;
    private final byte[] sm4Key;

    /**
     * Build an SM2-only encryptor (no SM4 key).
     */
    public SmEncryptor(String base64PublicKey, String base64PrivateKey) throws Exception {
        this.sm2PublicKey = base64PublicKey == null ? null : toSm2PublicKey(base64PublicKey);
        this.sm2PrivateKey = base64PrivateKey == null ? null : toSm2PrivateKey(base64PrivateKey);
        this.sm4Key = null;
        if (sm2PublicKey == null && sm2PrivateKey == null) {
            throw new IllegalArgumentException("SM2 keys must be provided");
        }
    }

    /**
     * Build an SM4-only encryptor.
     */
    public SmEncryptor(byte[] sm4Key) {
        Objects.requireNonNull(sm4Key, "sm4Key");
        if (sm4Key.length != 16) {
            throw new IllegalArgumentException("SM4 key must be 16 bytes, got " + sm4Key.length);
        }
        this.sm2PublicKey = null;
        this.sm2PrivateKey = null;
        this.sm4Key = sm4Key.clone();
    }

    // ---------- key conversion ----------
    public static PublicKey toSm2PublicKey(String base64) throws Exception {
        byte[] decoded = Base64.getDecoder().decode(base64);
        KeyFactory kf = KeyFactory.getInstance("EC", BouncyCastleProvider.PROVIDER_NAME);
        return kf.generatePublic(new ECPublicKeySpec(EC_PARAMETERS.getCurve().decodePoint(decoded), EC_SPEC));
    }

    public static PrivateKey toSm2PrivateKey(String base64) throws Exception {
        byte[] decoded = Base64.getDecoder().decode(base64);
        KeyFactory kf = KeyFactory.getInstance("EC", BouncyCastleProvider.PROVIDER_NAME);
        return kf.generatePrivate(new ECPrivateKeySpec(EC_PARAMETERS.getN(), EC_SPEC));
    }

    // ---------- SM2 encrypt / decrypt ----------
    public String sm2Encrypt(String plaintext) {
        if (sm2PublicKey == null) {
            throw new IllegalStateException("SM2 public key not configured");
        }
        try {
            org.bouncycastle.crypto.engines.SM2Engine engine =
                    new org.bouncycastle.crypto.engines.SM2Engine();
            engine.init(true, new org.bouncycastle.crypto.params.ParametersWithRandom(
                    ((BCECPublicKey) sm2PublicKey).getParameters(),
                    new SecureRandom()));
            byte[] data = plaintext.getBytes(StandardCharsets.UTF_8);
            return Base64.getEncoder().encodeToString(engine.processBlock(data, 0, data.length));
        } catch (Exception e) {
            throw new IllegalStateException("SM2 encryption failed", e);
        }
    }

    public String sm2Decrypt(String base64Cipher) {
        if (sm2PrivateKey == null) {
            throw new IllegalStateException("SM2 private key not configured");
        }
        try {
            org.bouncycastle.crypto.engines.SM2Engine engine =
                    new org.bouncycastle.crypto.engines.SM2Engine();
            engine.init(false,
                    new org.bouncycastle.crypto.params.ParametersWithRandom(
                            ((BCECPrivateKey) sm2PrivateKey).getParameters(),
                            new SecureRandom()));
            byte[] data = Base64.getDecoder().decode(base64Cipher);
            byte[] plain = engine.processBlock(data, 0, data.length);
            return new String(plain, StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new IllegalStateException("SM2 decryption failed", e);
        }
    }

    // ---------- SM2 sign / verify ----------
    public String sm2Sign(String content) {
        if (sm2PrivateKey == null) {
            throw new IllegalStateException("SM2 private key not configured");
        }
        try {
            Signature sig = Signature.getInstance(SM2_SIGN_ALGORITHM,
                    BouncyCastleProvider.PROVIDER_NAME);
            sig.initSign(sm2PrivateKey);
            sig.update(content.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(sig.sign());
        } catch (Exception e) {
            throw new IllegalStateException("SM2 signing failed", e);
        }
    }

    public boolean sm2Verify(String content, String base64Signature) {
        if (sm2PublicKey == null) {
            throw new IllegalStateException("SM2 public key not configured");
        }
        try {
            Signature sig = Signature.getInstance(SM2_SIGN_ALGORITHM,
                    BouncyCastleProvider.PROVIDER_NAME);
            sig.initVerify(sm2PublicKey);
            sig.update(content.getBytes(StandardCharsets.UTF_8));
            return sig.verify(Base64.getDecoder().decode(base64Signature));
        } catch (Exception e) {
            throw new IllegalStateException("SM2 verification failed", e);
        }
    }

    // ---------- SM4 symmetric ----------
    public String sm4Encrypt(String plaintext) {
        return Base64.getEncoder().encodeToString(sm4Encrypt(plaintext.getBytes(StandardCharsets.UTF_8)));
    }

    public byte[] sm4Encrypt(byte[] data) {
        ensureSm4Key();
        try {
            SM4Engine engine = new SM4Engine();
            byte[] iv = new byte[16];
            new SecureRandom().nextBytes(iv);
            engine.init(true, new ParametersWithIV(new KeyParameter(sm4Key), iv));
            byte[] out = processBlockAligned(engine, data);
            byte[] result = new byte[iv.length + out.length];
            System.arraycopy(iv, 0, result, 0, iv.length);
            System.arraycopy(out, 0, result, iv.length, out.length);
            return result;
        } catch (Exception e) {
            throw new IllegalStateException("SM4 encryption failed", e);
        }
    }

    public String sm4Decrypt(String base64Cipher) {
        return new String(sm4Decrypt(Base64.getDecoder().decode(base64Cipher)), StandardCharsets.UTF_8);
    }

    public byte[] sm4Decrypt(byte[] ivAndCipher) {
        ensureSm4Key();
        try {
            byte[] iv = new byte[16];
            System.arraycopy(ivAndCipher, 0, iv, 0, 16);
            byte[] cipherBytes = new byte[ivAndCipher.length - 16];
            System.arraycopy(ivAndCipher, 16, cipherBytes, 0, cipherBytes.length);
            SM4Engine engine = new SM4Engine();
            engine.init(false, new ParametersWithIV(new KeyParameter(sm4Key), iv));
            return processBlockAligned(engine, cipherBytes);
        } catch (Exception e) {
            throw new IllegalStateException("SM4 decryption failed", e);
        }
    }

    private void ensureSm4Key() {
        if (sm4Key == null) {
            throw new IllegalStateException("SM4 key not configured");
        }
    }

    private byte[] processBlockAligned(SM4Engine engine, byte[] input) {
        // SM4 block size is 16 bytes. PKCS7 padding handled externally here.
        int blockSize = 16;
        int padded = (input.length / blockSize + 1) * blockSize;
        byte[] paddedInput = new byte[padded];
        System.arraycopy(input, 0, paddedInput, 0, input.length);
        int pad = padded - input.length;
        for (int i = input.length; i < padded; i++) {
            paddedInput[i] = (byte) pad;
        }
        byte[] out = new byte[padded];
        for (int i = 0; i < padded; i += blockSize) {
            engine.processBlock(paddedInput, i, out, i);
        }
        return out;
    }
}
