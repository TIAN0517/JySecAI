package com.dast.back.mapper;

import com.dast.back.Bean.TaskReport;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface ReportMapper {
    Integer insertReport(TaskReport taskReport);
    Integer updateStatus(@Param("groupId") String groupId, @Param("status") Integer status);
    Integer updateTaskStatus(@Param("id") Long id, @Param("status") Integer status);
    List<TaskReport>  getReportsByTaskId(@Param("task_id") Long id,@Param("source") int source,@Param("groupId") String groupId);
    List<TaskReport>  getReportsByGroupIdAll(@Param("groupId") String groupId);
    String getReportPathById(@Param("id") Integer id,@Param("task_id") Long task_id);
    Integer deleteReportById(@Param("id") Integer id,@Param("task_id") Long task_id);
    List<TaskReport> getLatestReportByTaskId(@Param("task_id") Long id,@Param("source") int source,@Param("groupId") String groupId,@Param("size") int size);
    List<TaskReport> getLatestReportsByGroup(
            @Param("source") Integer source,
            @Param("groupId") String groupId,
            @Param("report_path") String report_path);

}
