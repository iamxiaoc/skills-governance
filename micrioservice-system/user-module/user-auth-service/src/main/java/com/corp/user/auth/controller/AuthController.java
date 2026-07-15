package com.corp.user.auth.controller;

import com.corp.base.common.result.Result;
import com.corp.user.auth.service.TokenService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 认证Controller
 * 提供登录/登出/刷新Token接口
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private TokenService tokenService;

    @PostMapping("/login")
    public Result<Map<String, String>> login(@RequestBody Map<String, String> credentials) {
        String username = credentials.get("username");
        String password = credentials.get("password");
        Map<String, String> tokenMap = tokenService.login(username, password);
        return Result.success(tokenMap);
    }

    @PostMapping("/logout")
    public Result<Boolean> logout(@RequestHeader("Authorization") String token) {
        return Result.success(tokenService.logout(token));
    }

    @PostMapping("/refresh")
    public Result<Map<String, String>> refreshToken(@RequestHeader("Authorization") String token) {
        return Result.success(tokenService.refreshToken(token));
    }
}
