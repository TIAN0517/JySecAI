package com.dast.back.Bean;

import lombok.Data;

@Data
public class TaskReport {
    private Integer id;
    private Long task_id;
    private String report_path;
    private String create_time;
    private Integer status;
    private Integer source;
    private String name;
    private String url;
    private String groupId;

}
