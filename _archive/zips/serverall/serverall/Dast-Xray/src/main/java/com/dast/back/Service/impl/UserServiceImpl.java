package com.dast.back.Service.impl;

import com.dast.back.Bean.User;
import com.dast.back.Service.UserService;
import com.dast.back.mapper.UserMapper;
import org.apache.commons.codec.digest.Md5Crypt;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import javax.cache.Cache;
import javax.cache.CacheManager;

import java.security.MessageDigest;
import java.util.UUID;

@Service
public class UserServiceImpl implements UserService {
    @Autowired
    private UserMapper userMapper;
    @Autowired
    private CacheManager cacheManager;

    private Cache<String, String> cache;

    @PostConstruct
    public void initCache() {
        cache = cacheManager.getCache("userTokenCache", String.class, String.class);
    }
    @Override
    public String Login(User user) {
        user.setPassword(md5(user.getPassword()));
        User userinfo=userMapper.Login(user);
        if (userinfo!=null){

            String userToken = generateUserToken(userinfo.getUsername());

            if (cache != null) {
                cache.put(userToken, userToken);
            }
            return userToken;
        }else {
            return null;
        }
    }

    @Override
    public Integer updatePassword(String username,String oldpw,String newpw) {

        if (!md5(oldpw).equals(userMapper.getPasswordByName(username).getPassword())){
            return 0;
        }



        return userMapper.updatePassword(username,md5(newpw));
    }

    @Override
    public String generateUserToken(String username) {
        return username + "_" + UUID.randomUUID().toString().replace("-","");
    }
    @Override
    public String getUserToken(String token) {
        if (cache != null) {
            return cache.get(token);
        }
        return null;
    }

    @Override
    public Boolean logout(String token) {

        return cache.remove(token);
    }

    public static String md5(String str) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest(str.getBytes());
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b & 0xff));
            }
            return sb.toString();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
