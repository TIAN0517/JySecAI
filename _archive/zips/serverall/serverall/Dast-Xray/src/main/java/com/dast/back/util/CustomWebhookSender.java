package com.dast.back.util;

import com.dast.back.Bean.TaskReport;
import com.dast.back.Server.XrayManager;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.codec.binary.Base64;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class CustomWebhookSender {
    private static final Logger log = LoggerFactory.getLogger(CustomWebhookSender.class);
    public static void sendbyFeishu(String webhookUrl, String jsonBody) {
        try {
            String finalUrl = webhookUrl;

            URL url = new URL(finalUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            conn.setDoOutput(true);

            try (OutputStream os = conn.getOutputStream()) {
                os.write(jsonBody.getBytes("UTF-8"));
            }

            int code = conn.getResponseCode();
            System.out.println("HTTP 响应码: " + code);

            // 读取响应体
            InputStream is = code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream();
            StringBuilder response = new StringBuilder();
            try (BufferedReader br = new BufferedReader(new InputStreamReader(is, "UTF-8"))) {
                String line;
                while ((line = br.readLine()) != null) {
                    response.append(line);
                }
            }

            System.out.println("HTTP 响应内容: " + response.toString());

        } catch (Exception e) {
            e.printStackTrace();
        }
    }


    public static void sendbyDingtalk(String webhookUrl, String secret, String jsonBody) {
        try {
            String finalUrl = webhookUrl;
            if (secret != null && !secret.isEmpty()) {
                long timestamp = System.currentTimeMillis();
                String sign = genSignByDingtalk(secret, timestamp);
                finalUrl = webhookUrl + "&timestamp=" + timestamp + "&sign=" + sign;
            }

            URL url = new URL(finalUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            conn.setDoOutput(true);

            try (OutputStream os = conn.getOutputStream()) {
                os.write(jsonBody.getBytes("UTF-8"));
            }

            int code = conn.getResponseCode();
            System.out.println("HTTP 响应码: " + code);

            // 读取响应体
            InputStream is = code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream();
            StringBuilder response = new StringBuilder();
            try (BufferedReader br = new BufferedReader(new InputStreamReader(is, "UTF-8"))) {
                String line;
                while ((line = br.readLine()) != null) {
                    response.append(line);
                }
            }

            System.out.println("HTTP 响应内容: " + response.toString());

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static String genSignByDingtalk(String secret, long timestamp) throws Exception {
        String stringToSign = timestamp + "\n" + secret;
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret.getBytes("UTF-8"), "HmacSHA256"));
        byte[] signData = mac.doFinal(stringToSign.getBytes("UTF-8"));
        return URLEncoder.encode(new String(org.apache.commons.codec.binary.Base64.encodeBase64(signData)), "UTF-8");
    }


    private static String GenSignByFeishu(String secret, int timestamp) throws NoSuchAlgorithmException, InvalidKeyException, NoSuchAlgorithmException, InvalidKeyException {
        //把timestamp+"\n"+密钥当做签名字符串
        String stringToSign = timestamp + "\n" + secret;
        //使用HmacSHA256算法计算签名
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(stringToSign.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        byte[] signData = mac.doFinal(new byte[]{});
        return new String(Base64.encodeBase64(signData));
    }


    public static String buildJsonByDingtalk(String webhookUrl, String message){
        Map<String, Object> root = new HashMap<>();
        root.put("msgtype", "text");
        Map<String, Object> text = new HashMap<>();
        text.put("content", message);
        root.put("text", text);
        try {
            ObjectMapper mapper = new ObjectMapper();
            return mapper.writeValueAsString(root);
        } catch (Exception e) {
            throw new RuntimeException("JSON 构造失败: " + e.getMessage(), e);
        }
    }


    public static String buildJsonByFeishu(String webhookUrl, String message,String sign,Long timestamp){
        Map<String, Object> root = new HashMap<>();
        root.put("msg_type", "text");
        root.put("sign",sign);
        root.put("timestamp",timestamp);
        Map<String, Object> content = new HashMap<>();
        content.put("text", message);
        root.put("content", content);
        try {
            ObjectMapper mapper = new ObjectMapper();
            return mapper.writeValueAsString(root);
        } catch (Exception e) {
            throw new RuntimeException("JSON 构造失败: " + e.getMessage(), e);
        }
    }




    public static String getMessageTemple(TaskReport taskReport) {
        StringBuilder sb = new StringBuilder();

        // 1. 任务基础信息
        sb.append(String.format("🔔 任务名称：%s\n", taskReport.getName()));
        sb.append(String.format("🆔 任务组ID：%s\n", taskReport.getGroupId()));
        sb.append(String.format("📁 任务输出报告：%s\n", taskReport.getReport_path()));
        sb.append(String.format("📌 任务状态：%s\n\n", taskReport.getStatus()));
        sb.append("------\n");

        Path jsonPath = Paths.get(taskReport.getReport_path().replace(".html", ".json"));
        if (!Files.exists(jsonPath)) {
            sb.append("⚠️ json报告文件未找到，暂不解析报告详情\n");
            return sb.toString();
        }

        ObjectMapper mapper = new ObjectMapper();
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
                .withZone(ZoneId.of("Asia/Shanghai"));

        try (BufferedReader br = Files.newBufferedReader(jsonPath, StandardCharsets.UTF_8)) {
            List<JsonNode> nodes = new ArrayList<>();
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                try {
                    nodes.add(mapper.readTree(line));
                } catch (Exception ex) {
                    // 某行解析失败，记录日志但继续
                    log.error("解析 JSON 行失败: " + (line.length() > 100 ? line.substring(0, 100) + "..." : line));
                }
            }

            if (nodes.isEmpty()) {
                sb.append("ℹ️ 报告中未发现漏洞条目。\n");
                return sb.toString();
            }

            sb.append(String.format("🔎 共发现漏洞 %d 条：\n", nodes.size()));

            int index = 1;
            for (JsonNode item : nodes) {
                long createTimeMs = item.path("create_time").asLong(0L);
                String timeStr = createTimeMs > 0 ? fmt.format(Instant.ofEpochMilli(createTimeMs)) : "未知时间";

                String addr = item.path("detail").path("addr").asText("");
                String plugin = item.path("plugin").asText("");
                String payload = item.path("detail").path("payload").asText("");

                // 获取漏洞路径
                String vulnPath = "";
                JsonNode params = item.path("target").path("params");
                if (params.isArray() && params.size() > 0) {
                    JsonNode p0 = params.get(0);
                    JsonNode pathNode = p0.path("path");
                    if (pathNode.isArray() && pathNode.size() > 0) {
                        List<String> parts = new ArrayList<>();
                        for (JsonNode p : pathNode) parts.add(p.asText());
                        vulnPath = String.join("/", parts);
                    } else {
                        vulnPath = p0.path("path").asText("");
                    }
                }

                // 漏洞条目输出
                sb.append(String.format("%d. 漏洞类型: %s\n", index++, plugin.isEmpty() ? "未知插件" : plugin));
                sb.append(String.format("⏰time：%s\n", timeStr));
                if (!addr.isEmpty()) sb.append(String.format("🔗url：%s\n", addr));
                if (!vulnPath.isEmpty()) sb.append(String.format("🧭source：%s\n", vulnPath));
                if (!payload.isEmpty()) {
                    String displayPayload = payload.length() > 200 ? payload.substring(0, 200) + "..." : payload;
                    sb.append(String.format("🧩Payload：%s\n", displayPayload));
                }
                sb.append("\n");
            }

            return sb.toString();

        } catch (Exception ex) {
            log.error("⚠️ 解析 JSON 文件时发生异常，部分漏洞可能未显示。\n");
            return sb.toString();
        }
    }











    public static void sendMain(String webhookurl,String secret,TaskReport taskReport){
            try {
                 String message = getMessageTemple(taskReport);
                if (webhookurl.contains("feishu")||webhookurl.contains("lark")){
                    long timestamp = System.currentTimeMillis() / 1000L;
                    sendbyFeishu(webhookurl, buildJsonByFeishu(webhookurl, message,secret,timestamp));
                }else{
                    sendbyDingtalk(webhookurl, secret, buildJsonByDingtalk(webhookurl, message));
                }
            } catch (Exception e) {
                log.error("发送 webhook 失败: taskId=" + taskReport.getId(), e);
            }
    }





    public static void sendTest(String webhookurl,String secret){
        try {
            String message = "Xray-web测试效果";
            if (webhookurl.contains("feishu")||webhookurl.contains("lark")){
                long timestamp = System.currentTimeMillis() / 1000L;
                sendbyFeishu(webhookurl, buildJsonByFeishu(webhookurl, message,secret,timestamp));
            }else{
                sendbyDingtalk(webhookurl, secret, buildJsonByDingtalk(webhookurl, message));
            }
        } catch (Exception e) {
            log.error("测试失败：", e);
        }
    }

    public static void main(String[] args) throws Exception {

        long timestamp = System.currentTimeMillis() / 1000L;

//        String sign = GenSignByFeishu(secret, (int) timestamp);
//        String webhookParam = buildJsonByFeishu(webhook, "测试消息",sign,timestamp);
//        System.out.println("请求体: " + webhookParam);
//        String webhookParam2 = buildJsonByDingtalk(webhook2, testtemp());


//        sendbyFeishu(webhook, webhookParam);
//        sendbyDingtalk(webhook2, secret2, webhookParam2);



    }
}
