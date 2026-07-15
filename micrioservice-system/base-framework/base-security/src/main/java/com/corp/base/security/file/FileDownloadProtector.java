package com.corp.base.security.file;

import com.corp.base.common.exception.BizException;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Objects;

/**
 * Protects file download endpoints against path traversal and access control
 * bypass by validating that the requested path stays within an allowed
 * directory.
 */
public class FileDownloadProtector {

    private final Path baseDirectory;
    private final boolean requireCaseSensitiveMatch;

    /**
     * @param baseDirectory absolute path of the directory from which downloads
     *                      are permitted; subdirectories are allowed.
     */
    public FileDownloadProtector(String baseDirectory) {
        this(baseDirectory, true);
    }

    public FileDownloadProtector(String baseDirectory, boolean requireCaseSensitiveMatch) {
        Objects.requireNonNull(baseDirectory, "baseDirectory");
        this.baseDirectory = Paths.get(baseDirectory).toAbsolutePath().normalize();
        this.requireCaseSensitiveMatch = requireCaseSensitiveMatch;
    }

    /**
     * Resolve and validate a user-supplied path.
     *
     * @param requestedPath relative or absolute path requested by the user
     * @return the resolved, normalized {@link Path} guaranteed to be inside
     *         the base directory
     * @throws BizException when the path escapes the base directory or points
     *         to a non-existent / non-regular file
     */
    public Path validate(String requestedPath) throws BizException, IOException {
        if (requestedPath == null || requestedPath.isEmpty()) {
            throw new BizException("PATH_EMPTY", "Requested path is empty");
        }

        // Block obvious traversal sequences before resolving.
        String normalized = requestedPath.replace('\\', '/');
        if (normalized.contains("../") || normalized.contains("..\\")
                || normalized.contains("%2e") || normalized.contains("%2E")) {
            throw new BizException("PATH_TRAVERSAL_DETECTED",
                    "Path traversal sequences are not allowed");
        }

        Path candidate = baseDirectory.resolve(requestedPath).normalize();

        // Containment check: candidate must start with baseDirectory.
        String candidateStr = requireCaseSensitiveMatch
                ? candidate.toString()
                : candidate.toString().toLowerCase();
        String baseStr = requireCaseSensitiveMatch
                ? baseDirectory.toString()
                : baseDirectory.toString().toLowerCase();
        if (!candidateStr.startsWith(baseStr)) {
            throw new BizException("PATH_OUTSIDE_BASE",
                    "Requested path escapes the allowed directory");
        }

        // File existence and type checks.
        File file = candidate.toFile();
        if (!file.exists()) {
            throw new BizException("FILE_NOT_FOUND", "File does not exist: " + requestedPath);
        }
        if (!file.isFile()) {
            throw new BizException("NOT_A_FILE", "Path does not point to a regular file");
        }

        // Verify on the filesystem that no symlinks tricked us out of the base.
        Path realCandidate = Files.readSymbolicLink(candidate).toAbsolutePath().normalize();
        if (Files.exists(realCandidate)) {
            String realStr = requireCaseSensitiveMatch
                    ? realCandidate.toString()
                    : realCandidate.toString().toLowerCase();
            if (!realStr.startsWith(baseStr)) {
                throw new BizException("SYMLINK_ESCAPE",
                        "Resolved real path escapes the allowed directory");
            }
        }

        return candidate;
    }

    /**
     * Determine the content type for a path using the platform's mime table.
     */
    public String contentType(Path path) throws IOException {
        return Files.probeContentType(path);
    }

    public Path getBaseDirectory() {
        return baseDirectory;
    }
}
