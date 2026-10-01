package com.dast.back.Controller;

import com.dast.back.Bean.Task;
import com.dast.back.Service.TaskService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.*;

@CrossOrigin
@RestController
@RequestMapping("/api/openapi")
public class OpenApiController {
    @Autowired
    private TaskService taskService;

    @PostMapping("/scans")
    public ResponseEntity<?> scans(@RequestBody Map<String, Object> requestBody) throws IOException {
        Map<String, Object> result = new HashMap<>();
        List<String> tasks = (List<String>) requestBody.get("tasks");
        String webhookid = (String) requestBody.get("webhookid");
        Integer scan = (Integer) requestBody.get("scan");
        if (tasks == null || tasks.isEmpty()) {
            throw new IllegalArgumentException("任务列表不能为空");
        }
        if (tasks.size() == 1){
            List<Task> tasksList = new ArrayList<>();
            Task task = new Task();
            if (webhookid != null){
                task.setWebhookid(webhookid);
                task.setGroupId(UUID.randomUUID().toString());
                task.setUrl(tasks.get(0));
                task.setStatus(0);
                task.setSource(2);
                task.setFormat("html");
                task.setName("OpenApi-"+UUID.randomUUID().toString().replace("-","").substring(0,10));
            }else {
                task.setGroupId(UUID.randomUUID().toString());
                task.setUrl(tasks.get(0));
                task.setStatus(0);
                task.setSource(2);
                task.setFormat("html");
                task.setName("OpenApi-"+UUID.randomUUID().toString().replace("-","").substring(0,10));
            }


            tasksList.add(task);
            List<String> ids = taskService.addTaskByOpenapi(tasksList);
            if (scan!=null){
                if (scan == 1){
                    taskService.startTask(ids.get(0),2);
                }
            }


            result.put("message","success");
            result.put("code",200);
            result.put("result",ids);
            return ResponseEntity.ok(result);
        }else {
            List<Task> tasksList = new ArrayList<>();
            for (String task : tasks) {
                Task task1 = new Task();
                if (webhookid != null){
                    task1.setWebhookid(webhookid);
                    task1.setGroupId(UUID.randomUUID().toString());
                    task1.setUrl(task);
                    task1.setStatus(0);
                    task1.setSource(2);
                    task1.setFormat("html");
                    task1.setName("OpenApi-"+UUID.randomUUID().toString().replace("-","").substring(0,10));
                }else {
                    task1.setGroupId(UUID.randomUUID().toString());
                    task1.setUrl(tasks.get(0));
                    task1.setStatus(0);
                    task1.setSource(2);
                    task1.setFormat("html");
                    task1.setName("OpenApi-"+UUID.randomUUID().toString().replace("-","").substring(0,10));
                }
                tasksList.add(task1);
            }
            List<String> ids = taskService.addTaskByOpenapi(tasksList);
            if (scan!=null){
                if (scan == 1){
                    taskService.startTask(ids.get(0),2);
                }
            }
            result.put("message","success");
            result.put("code",200);
            result.put("result",ids);
            return ResponseEntity.ok(result);
        }


    }
}
