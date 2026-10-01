package com.dast.back.mapper;

import com.dast.back.Bean.ApiSecret;
import com.dast.back.Bean.WebHook;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface ApiSecretMapper {
    Integer insert(ApiSecret ApiSecret);

    Integer update(ApiSecret ApiSecret);
    Integer updateStatus(@Param("id") String id,@Param("status") Integer status);
    Integer delete(@Param("id") String id);
    List<ApiSecret> selectList();
    ApiSecret selectOne(@Param("api") String api);
}
