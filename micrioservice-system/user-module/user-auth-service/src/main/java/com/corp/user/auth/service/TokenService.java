package com.corp.user.auth.service;

import java.util.Map;

/**
 * Token服务
 * 处理JWT生成和验证
 */
public interface TokenService {

    Map<String, String> login(String username, String password);

    boolean logout(String token);

    Map<String, String> refreshToken(String token);
}
