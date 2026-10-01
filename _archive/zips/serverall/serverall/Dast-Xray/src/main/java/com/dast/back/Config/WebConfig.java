package com.dast.back.Config;

import com.dast.back.interceptor.LoginInterceptor;
import com.dast.back.interceptor.OpenapiInterceptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Autowired
    private LoginInterceptor loginInterceptor;

    @Autowired
    private OpenapiInterceptor openapiInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(openapiInterceptor)
                .addPathPatterns("/api/openapi/**");

        registry.addInterceptor(loginInterceptor)
                .addPathPatterns("/**")
                .excludePathPatterns(
                        "/api/user/login",
                        "/api/user/getUserInfo",
                        "/api/openapi/**",
                        "/sse/**"
                );
    }
}
