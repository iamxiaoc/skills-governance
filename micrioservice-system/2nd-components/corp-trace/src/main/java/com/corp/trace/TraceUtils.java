package com.corp.trace;

import java.util.UUID;

/**
 * 链路追踪工具类（二方件提供）
 */
public class TraceUtils {

    /**
     * 生成新的traceId
     */
    public static String generateTraceId() {
        return UUID.randomUUID().toString().replace("-", "");
    }

    /**
     * 生成新的spanId
     */
    public static String generateSpanId() {
        return Long.toHexString(System.currentTimeMillis());
    }

    /**
     * 开始一个新的trace
     */
    public static void startTrace() {
        TraceContext.setTraceId(generateTraceId());
        TraceContext.setSpanId(generateSpanId());
        TraceContext.setStartTime(System.currentTimeMillis());
    }

    /**
     * 从传入的traceId恢复上下文（用于跨服务调用）
     */
    public static void continueTrace(String traceId, String spanId) {
        TraceContext.setTraceId(traceId);
        TraceContext.setSpanId(spanId != null ? spanId : generateSpanId());
        TraceContext.setStartTime(System.currentTimeMillis());
    }

    /**
     * 结束当前trace
     */
    public static void endTrace() {
        TraceContext.clear();
    }

    /**
     * 获取当前耗时（毫秒）
     */
    public static long getDuration() {
        Long start = TraceContext.getStartTime();
        return start != null ? System.currentTimeMillis() - start : 0;
    }
}
