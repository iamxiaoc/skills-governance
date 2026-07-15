package com.corp.user.service.mapper;

import org.apache.ibatis.annotations.Mapper;

import java.util.Map;

/**
 * MyBatis Mapper接口
 */
@Mapper
public interface UserMapper {

    Map<String, Object> selectById(Long id);

    int insert(Map<String, Object> userMap);

    int update(Map<String, Object> userMap);

    int deleteById(Long id);
}
