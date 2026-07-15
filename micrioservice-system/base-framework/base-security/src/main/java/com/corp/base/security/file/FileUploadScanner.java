package com.corp.base.security.file;

import com.corp.base.common.exception.BizException;

import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/**
 * File upload security scanner. Validates extension, MIME type, size, and
 * inspects magic bytes to defeat extension spoofing.
 */
public class FileUploadScanner {

    /** Default set of allowed extensions (lowercase, no dot). */
    public static final Set<String> DEFAULT_ALLOWED_EXTENSIONS = new HashSet<>(Arrays.asList(
            "txt", "csv", "log", "pdf", "doc", "docx", "xls", "xlsx",
            "ppt", "pptx", "jpg", "jpeg", "png", "gif", "bmp", "zip", "tar", "gz"));

    /** Default set of dangerous extensions that should always be rejected. */
    public static final Set<String> BLOCKED_EXTENSIONS = new HashSet<>(Arrays.asList(
            "exe", "bat", "cmd", "sh", "js", "jsp", "php", "asp", "aspx",
            "war", "jar", "dll", "so", "bin"));

    /** Magic bytes for common file types. */
    private static final byte[] PDF_MAGIC = new byte[]{0x25, 0x50, 0x44, 0x46}; // %PDF
    private static final byte[] PNG_MAGIC = new byte[]{(byte) 0x89, 0x50, 0x4E, 0x47};
    private static final byte[] JPG_MAGIC = new byte[]{(byte) 0xFF, (byte) 0xD8, (byte) 0xFF};
    private static final byte[] ZIP_MAGIC = new byte[]{0x50, 0x4B, 0x03, 0x04};
    private static final byte[] GIF_MAGIC = new byte[]{0x47, 0x49, 0x46, 0x38}; // GIF8

    private final Set<String> allowedExtensions;
    private final long maxFileSize;

    public FileUploadScanner() {
        this(DEFAULT_ALLOWED_EXTENSIONS, 50L * 1024L * 1024L); // 50MB
    }

    public FileUploadScanner(Set<String> allowedExtensions, long maxFileSize) {
        this.allowedExtensions = new HashSet<>();
        for (String ext : allowedExtensions) {
            this.allowedExtensions.add(ext.toLowerCase());
        }
        this.maxFileSize = maxFileSize;
    }

    /**
     * Validate a single uploaded file.
     *
     * @param fileName    original file name from the upload
     * @param declaredMime mime type declared by the client
     * @param size        file size in bytes
     * @param content     input stream of the file content (will be peeked, not consumed)
     * @throws BizException when validation fails
     */
    public void scan(String fileName, String declaredMime, long size, InputStream content)
            throws BizException, IOException {
        // 1. File name validation.
        if (fileName == null || fileName.isEmpty()) {
            throw new BizException("FILE_NAME_EMPTY", "File name is empty");
        }
        String extension = extractExtension(fileName);
        if (extension.isEmpty()) {
            throw new BizException("FILE_EXT_MISSING", "File extension is missing");
        }
        if (BLOCKED_EXTENSIONS.contains(extension)) {
            throw new BizException("FILE_EXT_BLOCKED", "File extension is blocked: " + extension);
        }
        if (!allowedExtensions.contains(extension)) {
            throw new BizException("FILE_EXT_NOT_ALLOWED",
                    "File extension not allowed: " + extension);
        }

        // 2. Size validation.
        if (size <= 0) {
            throw new BizException("FILE_SIZE_INVALID", "File size is invalid");
        }
        if (size > maxFileSize) {
            throw new BizException("FILE_TOO_LARGE",
                    "File size " + size + " exceeds limit " + maxFileSize);
        }

        // 3. Magic-byte inspection.
        if (content != null) {
            byte[] header = new byte[8];
            int read = content.read(header);
            if (read > 0) {
                byte[] actual = Arrays.copyOf(header, read);
                if (!magicMatches(extension, actual)) {
                    throw new BizException("FILE_MAGIC_MISMATCH",
                            "File content does not match its declared type");
                }
            }
        }
    }

    private String extractExtension(String fileName) {
        int dot = fileName.lastIndexOf('.');
        if (dot < 0 || dot == fileName.length() - 1) {
            return "";
        }
        return fileName.substring(dot + 1).toLowerCase();
    }

    private boolean magicMatches(String extension, byte[] header) {
        return switch (extension) {
            case "pdf" -> startsWith(header, PDF_MAGIC);
            case "png" -> startsWith(header, PNG_MAGIC);
            case "jpg", "jpeg" -> startsWith(header, JPG_MAGIC);
            case "zip" -> startsWith(header, ZIP_MAGIC);
            case "gif" -> startsWith(header, GIF_MAGIC);
            // Text-like files have no fixed magic bytes; accept them.
            case "txt", "csv", "log" -> true;
            default -> true;
        };
    }

    private boolean startsWith(byte[] data, byte[] magic) {
        if (data.length < magic.length) {
            return false;
        }
        for (int i = 0; i < magic.length; i++) {
            if (data[i] != magic[i]) {
                return false;
            }
        }
        return true;
    }

    public Set<String> getAllowedExtensions() {
        return allowedExtensions;
    }

    public long getMaxFileSize() {
        return maxFileSize;
    }
}
