package com.corp.base.security.filter;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.FilterConfig;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletRequestWrapper;

import java.io.IOException;
import java.util.Enumeration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * XSS protection filter that sanitizes request parameters and headers by
 * stripping dangerous HTML/JS sequences.
 *
 * <p>This is a defence-in-depth measure; output encoding at the view layer
 * remains the primary XSS mitigation.
 */
public class XssFilter implements Filter {

    // Matches common dangerous patterns: <script>, on*=, javascript:, etc.
    private static final Pattern SCRIPT_PATTERN =
            Pattern.compile("<script.*?>.*?</script>", Pattern.CASE_INSENSITIVE | Pattern.DOTALL);
    private static final Pattern ON_EVENT_PATTERN =
            Pattern.compile("on\\w+\\s*=", Pattern.CASE_INSENSITIVE);
    private static final Pattern JS_PROTOCOL_PATTERN =
            Pattern.compile("(javascript|vbscript|data):", Pattern.CASE_INSENSITIVE);
    private static final Pattern TAG_PATTERN =
            Pattern.compile("<[^>]+>", Pattern.CASE_INSENSITIVE);

    private boolean stripHtmlTags = true;

    @Override
    public void init(FilterConfig filterConfig) {
        String param = filterConfig.getInitParameter("stripHtmlTags");
        if (param != null) {
            stripHtmlTags = Boolean.parseBoolean(param);
        }
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        if (request instanceof HttpServletRequest httpReq) {
            chain.doFilter(new XssRequestWrapper(httpReq), response);
        } else {
            chain.doFilter(request, response);
        }
    }

    @Override
    public void destroy() {
        // No-op.
    }

    /**
     * Sanitize a string value by removing XSS vectors.
     */
    public String sanitize(String value) {
        if (value == null || value.isEmpty()) {
            return value;
        }
        String out = value;
        out = SCRIPT_PATTERN.matcher(out).replaceAll("");
        out = ON_EVENT_PATTERN.matcher(out).replaceAll("");
        out = JS_PROTOCOL_PATTERN.matcher(out).replaceAll("$1_");
        if (stripHtmlTags) {
            out = TAG_PATTERN.matcher(out).replaceAll("");
        }
        // Encode remaining angle brackets.
        out = out.replace("<", "&lt;").replace(">", "&gt;");
        return out;
    }

    public boolean isStripHtmlTags() {
        return stripHtmlTags;
    }

    public void setStripHtmlTags(boolean stripHtmlTags) {
        this.stripHtmlTags = stripHtmlTags;
    }

    /**
     * Wrapper that returns sanitized parameter values.
     */
    class XssRequestWrapper extends HttpServletRequestWrapper {

        XssRequestWrapper(HttpServletRequest request) {
            super(request);
        }

        @Override
        public String getParameter(String name) {
            return sanitize(super.getParameter(name));
        }

        @Override
        public String[] getParameterValues(String name) {
            String[] values = super.getParameterValues(name);
            if (values == null) {
                return null;
            }
            String[] sanitized = new String[values.length];
            for (int i = 0; i < values.length; i++) {
                sanitized[i] = sanitize(values[i]);
            }
            return sanitized;
        }

        @Override
        public Map<String, String[]> getParameterMap() {
            Map<String, String[]> original = super.getParameterMap();
            Map<String, String[]> result = new LinkedHashMap<>(original.size());
            for (Map.Entry<String, String[]> entry : original.entrySet()) {
                result.put(entry.getKey(), sanitize(entry.getValue()));
            }
            return result;
        }

        @Override
        public String getHeader(String name) {
            return sanitize(super.getHeader(name));
        }

        @Override
        public Enumeration<String> getHeaders(String name) {
            Enumeration<String> original = super.getHeaders(name);
            if (original == null) {
                return null;
            }
            java.util.List<String> sanitized = new java.util.ArrayList<>();
            while (original.hasMoreElements()) {
                sanitized.add(sanitize(original.nextElement()));
            }
            return java.util.Collections.enumeration(sanitized);
        }

        private String[] sanitize(String[] values) {
            if (values == null) {
                return null;
            }
            String[] out = new String[values.length];
            for (int i = 0; i < values.length; i++) {
                out[i] = sanitize(values[i]);
            }
            return out;
        }
    }
}
