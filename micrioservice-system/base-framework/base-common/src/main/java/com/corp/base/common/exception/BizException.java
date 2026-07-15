package com.corp.base.common.exception;

/**
 * Standard business exception carrying an error code and a user-facing
 * message. Designed to be translated into a {@code Result} payload by the
 * global exception handler.
 */
public class BizException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    /** Generic error code used when none is specified. */
    public static final String DEFAULT_CODE = "BIZ_ERROR";

    private final String code;
    private final String message;

    public BizException(String message) {
        this(DEFAULT_CODE, message, null);
    }

    public BizException(String code, String message) {
        this(code, message, null);
    }

    public BizException(String code, String message, Throwable cause) {
        super(message, cause);
        this.code = code == null ? DEFAULT_CODE : code;
        this.message = message;
    }

    public BizException(String message, Throwable cause) {
        this(DEFAULT_CODE, message, cause);
    }

    public String getCode() {
        return code;
    }

    @Override
    public String getMessage() {
        return message;
    }

    @Override
    public String toString() {
        return "BizException{code='" + code + "', message='" + message + "'}";
    }
}
