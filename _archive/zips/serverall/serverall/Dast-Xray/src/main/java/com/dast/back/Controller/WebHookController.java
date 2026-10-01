package com.dast.back.Controller;

import com.dast.back.Bean.WebHook;
import com.dast.back.Service.WebHookService;
import com.dast.back.util.CustomWebhookSender;
import com.dast.back.util.ResultUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@CrossOrigin
@RestController
@RequestMapping("/api/webhook")
public class WebHookController {

    @Autowired
    private WebHookService webHookService;

    @GetMapping("/test")
    public ResponseEntity<?> test(String id) {
        if (id.isEmpty() || id.equals("") || id == null){
            return ResponseEntity.ok(ResultUtil.result("400", null,"请求错误"));
        }
        WebHook webHook = webHookService.selectById(id);
        CustomWebhookSender.sendTest(webHook.getWebhookurl(),webHook.getSecret());
        return ResponseEntity.ok(ResultUtil.result("200", null,"测试成功"));
    }


    @GetMapping
    public List<WebHook> webhooklist() {
        return webHookService.selectList();
    }

    @PostMapping("/insert")
    public Integer insert(@RequestBody WebHook webHook) {
        return webHookService.insert(webHook);
    }

    @PostMapping("/update")
    public Integer update(@RequestBody WebHook webHook) {
        return webHookService.update(webHook);
    }

    @PostMapping("/delete")
    public Integer delete(String id) {
        return webHookService.delete(id);
    }

    @GetMapping("/selectById")
    public WebHook selectById(String id) {
        return webHookService.selectById(id);
    }
}
