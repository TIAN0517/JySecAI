package com.dast.back.Service.impl;

import com.dast.back.Bean.Task;
import com.dast.back.Bean.TaskReport;
import com.dast.back.Service.ReportService;
import com.dast.back.Service.TaskService;
import com.dast.back.mapper.ReportMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

@Service
public class ReportServiceImpl implements ReportService {


    @Autowired
    private TaskService taskService;

    @Autowired
    private ReportMapper reportMapper;




    @Override
    public List<TaskReport> getReportsByTaskId(Long id,Integer source,String groupId) {
        return reportMapper.getReportsByTaskId(id,source,groupId);
    }


    @Override
    public List<TaskReport> getTaskReports(Integer page, Integer size,Integer source) {
        int offset = (page - 1) * size;
        List<Task> tasks = taskService.getTaskList(offset, size,source);
        List<TaskReport> result = new ArrayList<>();

        for (Task task : tasks) {
            List<TaskReport> reports = getReportsByTaskId(task.getId(),source,task.getGroupId());
            if (reports != null) {
                result.addAll(reports); // 合并列表
            }
        }

        return result;
    }

    @Override
    public String getReportPathById(Integer id,Long task_id) {
        return reportMapper.getReportPathById(id,task_id);
    }

    @Override
    public Integer deleteReportById(Integer id, Long task_id, String path) throws IOException {
        if (reportMapper.deleteReportById(id,task_id)==1){
            deleteReport(path);
            return 1;
        }

        return 0;
    }

    private void deleteReport(String path) throws IOException {
        checkFilenameSafe(path);
        Files.delete(Paths.get(path));
        Files.delete(Paths.get(path.replace(".html",".json")));
    }

    private void checkFilenameSafe(String filename) {
        if (filename.contains("..") || filename.contains("../") || filename.contains("\\")|| filename.contains("./")) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "非法文件名");
        }
    }


}

