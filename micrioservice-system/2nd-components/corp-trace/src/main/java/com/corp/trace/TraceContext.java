package com.corp.trace;

/**
 * 链路追踪上下文（二方件提供）
 * 存储当前请求的traceId和spanId
 */
public class TraceContext {

    private static final ThreadLocal<String> TRACE_ID = new ThreadLocal<>();
    private static final ThreadLocal<String> SPAN_ID = new ThreadLocal<>();
    private static final ThreadLocal<Long> START_TIME = new ThreadLocal<>();

    public static void setTraceId(String traceId) {
        TRACE_ID.set(traceId);
    }

    public static String getTraceId() {
        return TRACE_ID.get();
    }

    public static void setSpanId(String spanId) {
        SPAN_ID.set(spanId);
    }

    public static String getSpanId() {
        return SPAN_ID.get();
    }

    public static void setStartTime(long time) {
        START_TIME.set(time);
    }

    public static Long getStartTime() {
        return START_TIME.get();
    }

    public static void clear() {
        TRACE_ID.remove();
        SPAN_ID.remove();
        START_TIME.remove();
    }
}
