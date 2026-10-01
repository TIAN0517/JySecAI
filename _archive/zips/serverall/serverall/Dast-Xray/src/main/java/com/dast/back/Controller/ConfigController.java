package com.dast.back.Controller;

import com.dast.back.Bean.ToolsSetting;
import com.dast.back.Service.TaskService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import javax.annotation.PostConstruct;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Collectors;

@CrossOrigin
@RestController
@RequestMapping("/api/config")
public class ConfigController {
    private static final Logger log = LoggerFactory.getLogger(ConfigController.class);

    @Autowired
    private TaskService taskService;

    private ToolsSetting toolsSetting;
    private String Xray_CONFIG_DIR;

    @PostConstruct
    public void init() {
        this.toolsSetting = taskService.getToolsPath();
        if (toolsSetting == null || toolsSetting.getXrayPath() == null) {
            log.warn("⚠ 工具路径未配置，后台可以进行填写");
            this.Xray_CONFIG_DIR = null; // 或者设置一个默认目录
        } else {
            this.Xray_CONFIG_DIR = new File(toolsSetting.getXrayPath()).getParent();
            log.info("✅ Xray_CONFIG_DIR 初始化成功：" + Xray_CONFIG_DIR);
        }
    }


    @GetMapping("/xray/list")
    public List<String> listConfigs() {
        File dir = new File(Xray_CONFIG_DIR);
        if (!dir.exists() || !dir.isDirectory()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "配置目录不存在");
        }
        return Arrays.stream(Objects.requireNonNull(
                        dir.listFiles((d, name) -> name.endsWith(".yaml") || name.endsWith(".yml"))
                ))
                .map(File::getName)
                .sorted()
                .collect(Collectors.toList());

    }

    @GetMapping("/xray/view")
    public ResponseEntity<String> viewConfig(@RequestParam String filename) throws IOException {
        checkFilenameSafe(filename);
        Path filePath = Paths.get(Xray_CONFIG_DIR, filename);
        if (!Files.exists(filePath)) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("文件不存在");
        }
        String content = new String(Files.readAllBytes(filePath), StandardCharsets.UTF_8);
        return ResponseEntity.ok().contentType(MediaType.TEXT_PLAIN).body(content);
    }

    @PutMapping("/save")
    public ResponseEntity<Map<String, Object>> saveConfig(@RequestBody Map<String, String> body) throws IOException {
        String filename = body.get("filename");
        String content = body.get("content");
        checkFilenameSafe(filename);
        Path filePath = Paths.get(Xray_CONFIG_DIR, filename);
        Files.write(filePath, content.getBytes(StandardCharsets.UTF_8), StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
        return ResponseEntity.ok(Collections.singletonMap("success", true));
    }

    @GetMapping("/download")
    public ResponseEntity<byte[]> downloadConfig(@RequestParam String filename) throws IOException {
        checkFilenameSafe(filename);
        String CONFIG_DIR = new File(toolsSetting.getXrayPath()).getParent();
        Path filePath = Paths.get(CONFIG_DIR, filename);
        if (!Files.exists(filePath)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "文件不存在");
        }

        byte[] fileBytes = Files.readAllBytes(filePath);
        HttpHeaders headers = new HttpHeaders();
        headers.setContentDisposition(ContentDisposition.builder("attachment").filename(filename).build());
        headers.setContentType(MediaType.parseMediaType("text/yaml"));
        return new ResponseEntity<>(fileBytes, headers, HttpStatus.OK);
    }

    private void checkFilenameSafe(String filename) {
        if (filename.contains("..") || filename.contains("/") || filename.contains("\\")) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "非法文件名");
        }
    }
}
