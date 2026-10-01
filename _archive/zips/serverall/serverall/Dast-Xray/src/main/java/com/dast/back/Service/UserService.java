package com.dast.back.Service;

import com.dast.back.Bean.User;

public interface UserService {
    String Login(User user);
    Integer updatePassword(String username,String oldpw,String newpw);
    String generateUserToken(String username);
    String getUserToken(String token);
    Boolean logout(String token);
}
