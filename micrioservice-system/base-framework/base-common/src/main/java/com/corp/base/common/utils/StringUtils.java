package com.corp.base.common.utils;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * String utilities providing common null-safe operations.
 *
 * <p>Acts as a thin layer on top of {@link org.apache.commons.lang3.StringUtils}
 * with some additions specific to the base framework.
 */
public final class StringUtils {

    public static final String EMPTY = "";
    public static final String[] EMPTY_STRING_ARRAY = new String[0];

    private StringUtils() {
    }

    /**
     * Return true when the input is null or has zero length after trimming.
     */
    public static boolean isEmpty(CharSequence cs) {
        return cs == null || cs.length() == 0;
    }

    /**
     * Return true when the input is null, empty, or whitespace only.
     */
    public static boolean isBlank(CharSequence cs) {
        if (isEmpty(cs)) {
            return true;
        }
        for (int i = 0; i < cs.length(); i++) {
            if (!Character.isWhitespace(cs.charAt(i))) {
                return false;
            }
        }
        return true;
    }

    /**
     * Inverse of {@link #isBlank}.
     */
    public static boolean isNotBlank(CharSequence cs) {
        return !isBlank(cs);
    }

    /**
     * Null-safe trim.
     */
    public static String trim(String str) {
        return str == null ? null : str.trim();
    }

    /**
     * Null-safe equals.
     */
    public static boolean equals(String a, String b) {
        return Objects.equals(a, b);
    }

    /**
     * Null-safe equals ignoring case.
     */
    public static boolean equalsIgnoreCase(String a, String b) {
        if (a == null || b == null) {
            return a == b;
        }
        return a.equalsIgnoreCase(b);
    }

    /**
     * Join a collection of objects into a single string using the given separator.
     */
    public static String join(Collection<?> items, String separator) {
        if (items == null || items.isEmpty()) {
            return EMPTY;
        }
        return items.stream()
                .map(o -> o == null ? EMPTY : o.toString())
                .collect(Collectors.joining(separator == null ? EMPTY : separator));
    }

    /**
     * Join an array of objects using the given separator.
     */
    public static String join(Object[] items, String separator) {
        if (items == null || items.length == 0) {
            return EMPTY;
        }
        return join(Arrays.asList(items), separator);
    }

    /**
     * Split a string by a single-character separator. Empty input yields an
     * empty array (never {@code null}).
     */
    public static String[] split(String str, char separator) {
        if (isEmpty(str)) {
            return EMPTY_STRING_ARRAY;
        }
        List<String> result = new ArrayList<>();
        int start = 0;
        for (int i = 0; i < str.length(); i++) {
            if (str.charAt(i) == separator) {
                result.add(str.substring(start, i));
                start = i + 1;
            }
        }
        result.add(str.substring(start));
        return result.toArray(EMPTY_STRING_ARRAY);
    }

    /**
     * Split a string by a literal separator string.
     */
    public static String[] split(String str, String separator) {
        if (isEmpty(str)) {
            return EMPTY_STRING_ARRAY;
        }
        if (isEmpty(separator)) {
            return new String[]{str};
        }
        List<String> result = new ArrayList<>();
        int start = 0;
        int idx;
        while ((idx = str.indexOf(separator, start)) >= 0) {
            result.add(str.substring(start, idx));
            start = idx + separator.length();
        }
        result.add(str.substring(start));
        return result.toArray(EMPTY_STRING_ARRAY);
    }

    /**
     * Null-safe substring. Returns empty string when input is null.
     */
    public static String substring(String str, int start, int end) {
        if (str == null) {
            return EMPTY;
        }
        if (start < 0) {
            start = 0;
        }
        if (end > str.length()) {
            end = str.length();
        }
        if (end <= start) {
            return EMPTY;
        }
        return str.substring(start, end);
    }

    /**
     * Repeat a string {@code n} times.
     */
    public static String repeat(String str, int n) {
        if (str == null || n <= 0) {
            return EMPTY;
        }
        StringBuilder sb = new StringBuilder(str.length() * n);
        for (int i = 0; i < n; i++) {
            sb.append(str);
        }
        return sb.toString();
    }

    /**
     * Mask a string keeping the first {@code prefix} and last {@code suffix}
     * characters visible — useful for log masking of sensitive data.
     */
    public static String mask(String str, int prefix, int suffix) {
        if (isEmpty(str)) {
            return EMPTY;
        }
        int len = str.length();
        if (prefix + suffix >= len) {
            // Keep at least one masked character.
            prefix = Math.max(0, len - suffix - 1);
        }
        StringBuilder sb = new StringBuilder();
        if (prefix > 0) {
            sb.append(str, 0, prefix);
        }
        sb.append(repeat("*", len - prefix - suffix));
        if (suffix > 0) {
            sb.append(str, len - suffix, len);
        }
        return sb.toString();
    }
}
