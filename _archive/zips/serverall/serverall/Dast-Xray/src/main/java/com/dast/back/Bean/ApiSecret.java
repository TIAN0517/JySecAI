package com.dast.back.Bean;

import lombok.Data;

@Data
public class ApiSecret {
    private String id;
    private String name;
    private String apiSecret;
    private Integer status;
}
