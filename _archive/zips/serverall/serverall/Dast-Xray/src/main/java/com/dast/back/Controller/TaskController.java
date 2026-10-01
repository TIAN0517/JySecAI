package com.dast.back.Controller;

import com.dast.back.Bean.Task;
import com.dast.back.Service.TaskService;
import com.github.pagehelper.PageInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.net.MalformedURLException;
import java.util.*;

@CrossOrigin
@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    @Autowired
    private TaskService taskService;

    @GetMapping
    public PageInfo<Task> getTasks(@RequestParam(defaultValue = "1") int page,
                                   @RequestParam(defaultValue = "5") int size,@RequestParam int source) {
        return taskService.getAllTasks(page, size,source);
    }

    @GetMapping("/get")
    public Task getTask(@RequestParam Long taskId) {
        return taskService.getOne(taskId);
    }

    @GetMapping("/{id}/startTask")
    public Integer startTask(@PathVariable Long id,@RequestParam Integer source) throws IOException {
        if (source==null){
            source=0;
        }
        return taskService.startTask(id,source);
    }

    @GetMapping("/{id}/startTaskBygroup")
    public Integer startTaskBygroup(@PathVariable String id,@RequestParam Integer source) throws IOException {
        if (source==null){
            source=0;
        }
        return taskService.startTask(id,source);
    }

    @GetMapping("/{id}/stopTask")
    public Integer stopTask(@PathVariable Long id) throws IOException {
        return taskService.stopTask(id);
    }

    @GetMapping("/stopTaskByGroup")
    public Integer stopTask(@RequestParam String id) throws IOException {
        return taskService.stopTask(id);
    }

    @PostMapping
    public Integer addTask(@RequestBody Task task) throws MalformedURLException {
        return taskService.addTask(task);
    }



    @PostMapping("/batch")
    public List<Integer> addTasks(@RequestBody List<Task> tasks) throws MalformedURLException {
        List<Integer> ids = new ArrayList<>();
        if (tasks == null || tasks.isEmpty()) {
            throw new IllegalArgumentException("任务列表不能为空");
        }

        taskService.addTask(tasks,true);

        return ids;
    }


    @DeleteMapping("/{id}")
    public Integer deleteTask(@PathVariable Long id) {

        return taskService.deleteTask(id);
    }

    @DeleteMapping("/group/{id}")
    public Integer deleteTask(@PathVariable String id) {

        return taskService.deleteTaskByGroup(id);
    }

    @PutMapping("/{id}/status")
    public Integer updateStatus(@PathVariable Long id, @RequestBody String status) {

        return taskService.updateStatus(id, 1);
    }

    @PostMapping("/task/edit")
    public Integer updateTask(@RequestBody Task task) throws MalformedURLException {

        return taskService.updateTask(task);
    }

}
