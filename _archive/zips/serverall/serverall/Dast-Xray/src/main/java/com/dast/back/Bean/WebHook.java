package com.dast.back.Bean;

import lombok.Data;

@Data
public class WebHook {
    private String id;
    private String name;
    private String webhookurl;
    private String secret;
}
