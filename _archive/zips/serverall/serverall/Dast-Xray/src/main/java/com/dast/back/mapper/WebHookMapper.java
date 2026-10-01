package com.dast.back.mapper;

import com.dast.back.Bean.WebHook;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface WebHookMapper {
    Integer insert(WebHook webHook);
//    WebHook selectById(Integer id);
    Integer update(WebHook webHook);
    Integer delete(@Param("id") String id);
    WebHook selectById(@Param("id") String id);
    List<WebHook> selectList();
}
