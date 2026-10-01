package com.dast.back.Service.impl;

import com.dast.back.Bean.WebHook;
import com.dast.back.Service.WebHookService;
import com.dast.back.mapper.WebHookMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class WebHookServiceImpl implements WebHookService {

    @Autowired
    private WebHookMapper webHookMapper;


    @Override
    public List<WebHook> selectList() {
        return webHookMapper.selectList();
    }

    @Override
    public Integer insert(WebHook webHook) {
        return webHookMapper.insert(webHook);
    }

    @Override
    public Integer update(WebHook webHook) {
        return webHookMapper.update(webHook);
    }

    @Override
    public Integer delete(String id) {
        return webHookMapper.delete(id);
    }

    @Override
    public WebHook selectById(String id) {

        return webHookMapper.selectById(id);
    }
}
