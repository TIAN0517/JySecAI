package com.dast.back.Service;

import com.dast.back.Bean.TaskReport;

import java.io.IOException;
import java.util.List;

public interface ReportService {

    List<TaskReport> getReportsByTaskId(Long id,Integer source,String groupId);

    List<TaskReport> getTaskReports(Integer page, Integer size,Integer source);

    String getReportPathById(Integer id,Long task_id);
    Integer deleteReportById(Integer id,Long task_id,String path) throws IOException;
}
