package com.dast.back.interceptor;

import com.dast.back.Service.UserService;
import com.dast.back.util.ResultUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.Arrays;
import java.util.List;

@Component
public class LoginInterceptor implements HandlerInterceptor {

    // 白名单URL列表，不需要登录校验
    private static final List<String> EXCLUDED_URLS = Arrays.asList("/api/user/login", "/api/user/getUserInfo","/api/user/logout");
    @Autowired
    private UserService userService;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String requestURI = request.getServletPath();
        if (EXCLUDED_URLS.contains(requestURI)) {
            return true;
        }

        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            response.setStatus(HttpServletResponse.SC_OK);
            return true;
        }

        if (isStaticResource(requestURI)) {
            return true;
        }

        String token = request.getHeader("Token");

        if (token == null || userService.getUserToken(token)==null) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            ResponseEntity.ok(ResultUtil.result("401", "请先登录", null));
            return false; // 拦截请求
        }
        return true;
    }


    private boolean isStaticResource(String uri) {
        return uri.matches(".*(\\.js|\\.css|\\.png|\\.jpg|\\.jpeg|\\.gif|\\.ico|\\.svg|\\.ttf|\\.woff2?)$");
    }


    @Override
    public void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler, ModelAndView modelAndView) throws Exception {
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
    }
}
