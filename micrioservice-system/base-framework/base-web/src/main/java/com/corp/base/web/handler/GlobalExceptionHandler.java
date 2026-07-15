package com.corp.base.web.handler;

import com.corp.base.common.exception.BizException;
import com.corp.base.common.result.Result;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.NoHandlerFoundException;

import java.util.stream.Collectors;

/**
 * Global exception handler translating thrown exceptions into the unified
 * {@link Result} envelope.
 *
 * <p>Mapping summary:
 * <ul>
 *   <li>{@link BizException} → HTTP 200, body carries the business code</li>
 *   <li>validation failures → HTTP 400, code {@code VALIDATION_ERROR}</li>
 *   <li>{@link NoHandlerFoundException} → HTTP 404</li>
 *   <li>any other {@link Throwable} → HTTP 500, code {@code INTERNAL_ERROR}</li>
 * </ul>
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BizException.class)
    public Result<Void> handleBizException(BizException ex, HttpServletRequest request) {
        log.warn("Biz exception on {}: [{}] {}",
                request.getRequestURI(), ex.getCode(), ex.getMessage());
        return Result.fail(ex.getCode(), ex.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Result<Void>> handleValidation(MethodArgumentNotValidException ex,
                                                         HttpServletRequest request) {
        String details = ex.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .collect(Collectors.joining("; "));
        log.warn("Validation failed on {}: {}", request.getRequestURI(), details);
        Result<Void> body = Result.fail("VALIDATION_ERROR", details);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(body);
    }

    @ExceptionHandler(NoHandlerFoundException.class)
    public ResponseEntity<Result<Void>> handleNotFound(NoHandlerFoundException ex,
                                                       HttpServletRequest request) {
        log.warn("No handler for {} {}", ex.getHttpMethod(), request.getRequestURI());
        Result<Void> body = Result.fail("NOT_FOUND", "Resource not found");
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(body);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Result<Void>> handleIllegalArg(IllegalArgumentException ex,
                                                          HttpServletRequest request) {
        log.warn("Illegal argument on {}: {}", request.getRequestURI(), ex.getMessage());
        Result<Void> body = Result.fail("BAD_REQUEST", ex.getMessage());
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(body);
    }

    @ExceptionHandler(Throwable.class)
    public ResponseEntity<Result<Void>> handleAny(Throwable ex, HttpServletRequest request) {
        log.error("Unhandled exception on {}", request.getRequestURI(), ex);
        Result<Void> body = Result.fail("INTERNAL_ERROR", "Internal server error");
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(body);
    }
}
