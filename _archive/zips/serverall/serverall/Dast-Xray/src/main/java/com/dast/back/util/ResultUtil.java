package com.dast.back.util;

import java.util.HashMap;
import java.util.Map;

public class ResultUtil {

    public static Map<String, Object> result(String code, String msg,Object data){
        Map<String, Object> result = new HashMap<>();
        result.put("code", code);

        if (msg != null){
            result.put("msg", msg);
        }

        if (data != null){
            result.put("data", data);
        }
        return result;
    }
}
