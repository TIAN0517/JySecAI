package com.dast.back.Controller;

import com.dast.back.Bean.ApiSecret;
import com.dast.back.Service.ApiSecretService;
import com.dast.back.util.ResultUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@CrossOrigin
@RestController
@RequestMapping("/api/apisecrets")
public class ApiSecretController {
    @Autowired
    private ApiSecretService apiSecretService;


    @GetMapping
    public List<ApiSecret> list() {
        return apiSecretService.selectList();
    }

    @GetMapping("/generate")
    public ResponseEntity<?> generate(String name) {
        ApiSecret apiSecret = new ApiSecret();
        apiSecret.setId(UUID.randomUUID().toString().replace("-","").substring(0,8));
        apiSecret.setApiSecret(UUID.randomUUID().toString().replace("-",""));
        apiSecret.setName(name);
        apiSecret.setStatus(1);

        if (apiSecretService.insert(apiSecret) == 1) {
            return ResponseEntity.ok(ResultUtil.result("200", null,apiSecret));
        } else {
            return ResponseEntity.ok(ResultUtil.result("400", null,"error"));
        }
    }

    @GetMapping("/reset")
    public ResponseEntity<?> reset(String id) {
        ApiSecret apiSecret = new ApiSecret();
        apiSecret.setApiSecret(UUID.randomUUID().toString().replace("-",""));
        apiSecret.setId(id);
        if (apiSecretService.update(apiSecret) == 1) {
            return ResponseEntity.ok(ResultUtil.result("200", null,"success"));
        } else {
            return ResponseEntity.ok(ResultUtil.result("400", null,"error"));
        }
    }

    @GetMapping("/delete")
    public ResponseEntity<?> delete(String id) {
        if (apiSecretService.delete(id) == 1) {
            return ResponseEntity.ok(ResultUtil.result("200", null,"success"));
        } else {
            return ResponseEntity.ok(ResultUtil.result("400", null,"error"));
        }
    }

    @GetMapping("/changeStatus")
    public ResponseEntity<?> changeStatus(String id, Integer status) {
        if (apiSecretService.updateStatus(id, status) == 1) {
            return ResponseEntity.ok(ResultUtil.result("200", null,"success"));
        } else {
            return ResponseEntity.ok(ResultUtil.result("400", null,"error"));
        }
    }

}
