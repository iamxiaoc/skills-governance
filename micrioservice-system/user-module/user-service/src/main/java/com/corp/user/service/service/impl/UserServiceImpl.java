package com.corp.user.service.service.impl;

import com.corp.id.IdGenerator;
import com.corp.id.IdGeneratorFactory;
import com.corp.monitor.MonitorUtils;
import com.corp.user.service.mapper.UserMapper;
import com.corp.user.service.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * UserService实现类
 */
@Service
public class UserServiceImpl implements UserService {

    @Autowired
    private UserMapper userMapper;

    private IdGenerator idGenerator = IdGeneratorFactory.getDefault();

    @Override
    public Map<String, Object> getUserById(Long id) {
        MonitorUtils.increment("user.query.count");
        return userMapper.selectById(id);
    }

    @Override
    public Long createUser(Map<String, Object> userMap) {
        Long userId = idGenerator.nextBizId("USR");
        userMap.put("id", userId);
        userMapper.insert(userMap);
        MonitorUtils.increment("user.create.count");
        return (Long) userMap.get("id");
    }

    @Override
    public boolean updateUser(Long id, Map<String, Object> userMap) {
        userMap.put("id", id);
        return userMapper.update(userMap) > 0;
    }

    @Override
    public boolean deleteUser(Long id) {
        return userMapper.deleteById(id) > 0;
    }
}
