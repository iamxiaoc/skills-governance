package com.corp.base.common.result;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.io.Serializable;
import java.util.Objects;

/**
 * Unified API response wrapper.
 *
 * <pre>
 *   {
 *     "code": "0",
 *     "message": "ok",
 *     "data": { ... }
 *   }
 * </pre>
 *
 * <p>Success uses {@code code = "0"}; business errors use a non-zero string
 * code, typically the {@link com.corp.base.common.exception.BizException#getCode()}.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Result<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    public static final String SUCCESS_CODE = "0";
    public static final String SUCCESS_MESSAGE = "ok";

    private String code;
    private String message;
    private T data;

    public Result() {
    }

    public Result(String code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    // ---------- factory methods ----------
    public static <T> Result<T> success() {
        return new Result<>(SUCCESS_CODE, SUCCESS_MESSAGE, null);
    }

    public static <T> Result<T> success(T data) {
        return new Result<>(SUCCESS_CODE, SUCCESS_MESSAGE, data);
    }

    public static <T> Result<T> success(T data, String message) {
        return new Result<>(SUCCESS_CODE, message, data);
    }

    public static <T> Result<T> fail(String code, String message) {
        return new Result<>(code, message, null);
    }

    public static <T> Result<T> fail(String code, String message, T data) {
        return new Result<>(code, message, data);
    }

    // ---------- predicates ----------
    public boolean isSuccess() {
        return Objects.equals(SUCCESS_CODE, code);
    }

    public boolean isFailure() {
        return !isSuccess();
    }

    // ---------- getters / setters ----------
    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public T getData() {
        return data;
    }

    public void setData(T data) {
        this.data = data;
    }

    @Override
    public String toString() {
        return "Result{code='" + code + "', message='" + message + "', data=" + data + '}';
    }
}
