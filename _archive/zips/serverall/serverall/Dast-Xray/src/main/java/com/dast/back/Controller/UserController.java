package com.dast.back.Controller;

import com.dast.back.Bean.User;
import com.dast.back.Service.UserService;
import com.dast.back.util.ResultUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import java.util.Map;

@CrossOrigin
@RestController
@RequestMapping("/api/user")
public class UserController {

    private static final Logger log = LoggerFactory.getLogger(UserController.class);
    @Autowired
    UserService userService;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody User user) {
        if (user==null){
            return ResponseEntity.ok(ResultUtil.result("400", "error", null));
        }
        String token = userService.Login(user);
        if(token == null){
            return ResponseEntity.ok(ResultUtil.result("401", "账号密码错误", null));
        }else {
            log.info("token:"+token);
            return ResponseEntity.ok(ResultUtil.result("200", "success", token));
        }
    }
    @PostMapping("/logout")
    public Boolean logout(HttpServletRequest httpServletRequest) {

        return userService.logout(httpServletRequest.getHeader("Token"));
    }

    @GetMapping("/getUserInfo")
    public String getUserInfo(String token) {return userService.getUserToken(token);}


    @PostMapping("/updatePw")
    public Integer updatePw(@RequestBody Map<String, Object> requestBody,HttpServletRequest httpServletRequest) {
        String username = httpServletRequest.getHeader("Token").split("_")[0];
        String oldpw = (String) requestBody.get("oldPassword");
        String newpw = (String) requestBody.get("newPassword");
        return userService.updatePassword(username,oldpw,newpw);
    }


}
