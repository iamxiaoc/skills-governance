package com.corp.user.framework.utils;

import com.corp.trace.TraceContext;
import com.corp.trace.TraceUtils;

import java.util.UUID;

/**
 * 用户Token工具类
 * FIXME: 该工具类为通用能力，不应放在模块framework中，应下沉到base-framework
 * 这是项目中实际存在的问题：通用Token工具被放在了业务模块的framework中
 */
public class UserTokenUtils {

    /**
     * 生成Token
     */
    public static String generateToken(Long userId) {
        String traceId = TraceContext.getTraceId();
        return userId + "_" + traceId + "_" + UUID.randomUUID().toString().replace("-", "");
    }

    /**
     * 从Token中解析用户ID
     */
    public static Long parseUserId(String token) {
        if (token == null || token.isEmpty()) {
            return null;
        }
        try {
            String[] parts = token.split("_");
            return Long.parseLong(parts[0]);
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 验证Token是否有效
     */
    public static boolean validateToken(String token) {
        return parseUserId(token) != null;
    }
}
