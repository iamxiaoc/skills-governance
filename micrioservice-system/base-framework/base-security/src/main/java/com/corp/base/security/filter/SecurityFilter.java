package com.corp.base.security.filter;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.FilterConfig;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.util.Set;
import java.util.UUID;

/**
 * Base security filter performing common request checks:
 * <ul>
 *   <li>Generates and propagates a request id for tracing.</li>
 *   <li>Enforces an allow-list of HTTP methods.</li>
 *   <li>Rejects requests with missing/oversized {@code Content-Length}.</li>
 * </ul>
 *
 * <p>Subclasses can override {@link #doFilterInternal} to add domain specific
 * checks while still benefiting from the tracing id.
 */
public class SecurityFilter implements Filter {

    public static final String REQUEST_ID_HEADER = "X-Request-Id";

    private static final Set<String> ALLOWED_METHODS =
            Set.of("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS");

    /** Reject request bodies larger than 10MB by default. */
    private long maxContentLength = 10L * 1024L * 1024L;

    @Override
    public void init(FilterConfig filterConfig) {
        // No-op; configuration via setters / Spring properties.
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        if (!(request instanceof HttpServletRequest httpReq)
                || !(response instanceof HttpServletResponse httpResp)) {
            chain.doFilter(request, response);
            return;
        }

        // 1. Tracing id propagation.
        String requestId = httpReq.getHeader(REQUEST_ID_HEADER);
        if (requestId == null || requestId.isEmpty()) {
            requestId = UUID.randomUUID().toString();
        }
        httpResp.setHeader(REQUEST_ID_HEADER, requestId);
        httpReq.setAttribute(REQUEST_ID_HEADER, requestId);

        // 2. Method allow-list.
        String method = httpReq.getMethod();
        if (!ALLOWED_METHODS.contains(method)) {
            httpResp.sendError(HttpServletResponse.SC_METHOD_NOT_ALLOWED,
                    "HTTP method not allowed: " + method);
            return;
        }

        // 3. Content length guard.
        long contentLength = httpReq.getContentLengthLong();
        if (contentLength > maxContentLength) {
            httpResp.sendError(HttpServletResponse.SC_REQUEST_ENTITY_TOO_LARGE,
                    "Request body too large: " + contentLength);
            return;
        }

        doFilterInternal(httpReq, httpResp, chain);
    }

    /**
     * Extension hook for subclasses.
     */
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws IOException, ServletException {
        chain.doFilter(request, response);
    }

    @Override
    public void destroy() {
        // No-op.
    }

    public long getMaxContentLength() {
        return maxContentLength;
    }

    public void setMaxContentLength(long maxContentLength) {
        this.maxContentLength = maxContentLength;
    }
}
