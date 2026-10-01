package com.dast.back.Service;

import com.dast.back.Bean.Task;
import com.dast.back.Bean.ToolsSetting;
import com.github.pagehelper.PageInfo;

import java.io.IOException;
import java.net.MalformedURLException;
import java.util.List;

public interface TaskService {
    PageInfo<Task> getAllTasks(int pageNum, int pageSize,int source);
    List<Task> getTaskList(int pageNum, int pageSize,int getTaskList);
    Integer addTask(Task task) throws MalformedURLException;



    Integer deleteTask(Long id);
    Integer deleteTaskByGroup(String id);
    Integer updateStatus(Long id, Integer status);
    Integer startTask(Long id,Integer source) throws IOException;
    Integer updateTaskcol(Long id,String xyport,String crawlerid) throws IOException;
    Integer stopTask(Long id);
    Integer stopTask(String id);
    Integer updateTask(Task task) throws MalformedURLException;
    Task getOne(Long id);
    ToolsSetting getToolsPath();
    List<Long> addTask(List<Task> task,boolean isList);
    List<String> addTaskByOpenapi(List<Task> task);
    Integer startTask(String id,Integer source) throws IOException;
    Integer updateTools(ToolsSetting toolsSetting);


}

