package com.dast.back.mapper;

import com.dast.back.Bean.Task;
import com.dast.back.Bean.ToolsSetting;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface TaskMapper {
    List<Task> getAllTasks(@Param("source") int source);
    Task getTaskList(@Param("offset") int offset, @Param("size") int size);
    int insertTask(Task task);
    int updateTask(Task task);
    int deleteTask(@Param("id") Long id);
    int deleteTaskbyGroup(@Param("id") String id);
    int updateStatus(@Param("id") Long id, @Param("status") Integer status);
    int updateStatusByGroup(@Param("id") String id, @Param("status") Integer status);
    Task getOne(@Param("id") Long id);

    Integer updateTaskcol(Long id, String xyport, String crawlerid);
    ToolsSetting getToolsPath();

    List<Task> selectByGroupId(@Param("groupId") String groupId);
    Long selectDistinctGroupIds();
    int updateTool(ToolsSetting toolsSetting);

}

