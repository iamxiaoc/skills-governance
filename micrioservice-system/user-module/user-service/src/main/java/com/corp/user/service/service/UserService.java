package com.corp.user.service.service;

import java.util.Map;

/**
 * 用户Service接口
 */
public interface UserService {

    Map<String, Object> getUserById(Long id);

    Long createUser(Map<String, Object> userMap);

    boolean updateUser(Long id, Map<String, Object> userMap);

    boolean deleteUser(Long id);
}
