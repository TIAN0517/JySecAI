package com.dast.back.mapper;

import com.dast.back.Bean.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper {
    User Login(User user);
    Integer updatePassword(String username,String password);
    User getPasswordByName(String username);
}
