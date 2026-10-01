package com.dast.back.Bean;

import lombok.Data;

@Data
public class Task {
    private Long id;
    private String name;
    private String url;
    private String output;
    private String format;
    private Integer status;
    private String xyport;
    private String crawlerid;
    private String createuser;
    private String createtime;
    private Integer source;
    private String groupId;
    private String webhookid;
}

