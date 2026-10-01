package com.dast.back.Service.impl;

import com.dast.back.Bean.ApiSecret;
import com.dast.back.Service.ApiSecretService;
import com.dast.back.mapper.ApiSecretMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;

@Service
public class ApiSecretServiceImpl implements ApiSecretService {
    @Autowired
    private ApiSecretMapper apiSecretMapper;

    @Override
    public Integer insert(ApiSecret ApiSecret) {
        return apiSecretMapper.insert(ApiSecret);
    }

    @Override
    public Integer update(ApiSecret ApiSecret) {
        return apiSecretMapper.update(ApiSecret);
    }

    @Override
    public Integer updateStatus(String id, Integer status) {
        return apiSecretMapper.updateStatus(id,status);
    }

    @Override
    public Integer delete(String id) {
        return apiSecretMapper.delete(id);
    }

    @Override
    public List<ApiSecret> selectList() {
        return apiSecretMapper.selectList();
    }

    @Override
    public ApiSecret selectOne(String api) {
        return apiSecretMapper.selectOne(api);
    }
}
