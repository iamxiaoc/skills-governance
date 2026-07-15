package com.corp.base.web.interceptor;

import com.corp.monitor.MonitorUtils;
import com.corp.trace.TraceContext;
import com.corp.trace.TraceUtils;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.UUID;

/**
 * Base interceptor handling request logging and trace-id propagation.
 *
 * <p>A trace id is taken from the {@code X-Trace-Id} header when present and
 * otherwise generated; the same id is exposed on the response and stored in
 * the SLF4J {@link MDC} under the {@code traceId} key for the duration of the
 * request so log entries can be correlated.
 */
public class BaseInterceptor implements HandlerInterceptor {

    public static final String TRACE_ID_HEADER = "X-Trace-Id";
    public static final String TRACE_ID_MDC = "traceId";
    public static final String START_TIME_ATTR = "base.request.startTime";

    private static final Logger log = LoggerFactory.getLogger(BaseInterceptor.class);

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) {
        String traceId = request.getHeader(TRACE_ID_HEADER);
        if (traceId == null || traceId.isEmpty()) {
            traceId = UUID.randomUUID().toString().replace("-", "");
        }
        MDC.put(TRACE_ID_MDC, traceId);
        response.setHeader(TRACE_ID_HEADER, traceId);
        request.setAttribute(TRACE_ID_HEADER, traceId);
        request.setAttribute(START_TIME_ATTR, System.currentTimeMillis());

        log.info("--> {} {} traceId={}",
                request.getMethod(),
                request.getRequestURI(),
                traceId);
        TraceUtils.startTrace();
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        Long start = (Long) request.getAttribute(START_TIME_ATTR);
        long elapsed = start == null ? -1L : System.currentTimeMillis() - start;
        int status = response.getStatus();
        String traceId = MDC.get(TRACE_ID_MDC);

        if (ex != null) {
            log.error("<-- {} {} status={} elapsed={}ms traceId={} ex={}",
                    request.getMethod(),
                    request.getRequestURI(),
                    status,
                    elapsed,
                    traceId,
                    ex.toString());
        } else {
            log.info("<-- {} {} status={} elapsed={}ms traceId={}",
                    request.getMethod(),
                    request.getRequestURI(),
                    status,
                    elapsed,
                    traceId);
        }
        MDC.remove(TRACE_ID_MDC);
        MonitorUtils.recordTime("request.duration", TraceUtils.getDuration());
        TraceUtils.endTrace();
    }
}
