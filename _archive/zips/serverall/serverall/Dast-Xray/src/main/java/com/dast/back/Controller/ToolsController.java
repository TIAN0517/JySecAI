package com.dast.back.Controller;

import com.dast.back.Bean.ToolsSetting;
import com.dast.back.Service.TaskService;
import com.dast.back.Service.impl.TaskServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@CrossOrigin
@RestController
@RequestMapping("/api/tools")
public class ToolsController {

    private final TaskServiceImpl taskServiceImpl;

    public ToolsController(TaskServiceImpl taskService) {
        this.taskServiceImpl = taskService;
    }

    @Autowired
    private TaskService taskService;

    @GetMapping
    public ToolsSetting gettools(){
        return taskService.getToolsPath();
    }

    @PutMapping
    public Integer updatetools(@RequestBody ToolsSetting toolsSetting){
        return taskService.updateTools(toolsSetting);
    }

    @PostMapping("/reload")
    public ResponseEntity<String> reloadTools() {
        try {
            taskServiceImpl.reloadToolSetting();
            return ResponseEntity.ok("工具路径重新加载成功！");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("重新加载失败: " + e.getMessage());
        }
    }
}
