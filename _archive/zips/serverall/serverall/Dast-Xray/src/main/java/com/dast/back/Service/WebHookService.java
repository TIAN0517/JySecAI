package com.dast.back.Service;

import com.dast.back.Bean.WebHook;

import java.util.List;


public interface WebHookService {
    List<WebHook> selectList();
    Integer insert(WebHook webHook);
//    WebHook selectById(Integer id);
    Integer update(WebHook webHook);
    Integer delete(String id);
    WebHook selectById(String id);
}
