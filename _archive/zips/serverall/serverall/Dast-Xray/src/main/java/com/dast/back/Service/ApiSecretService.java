package com.dast.back.Service;

import com.dast.back.Bean.ApiSecret;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface ApiSecretService {
    Integer insert(ApiSecret ApiSecret);
    Integer update(ApiSecret ApiSecret);
    Integer updateStatus(String id,Integer status);
    Integer delete(String id);
    List<ApiSecret> selectList();
    ApiSecret selectOne(String api);
}
