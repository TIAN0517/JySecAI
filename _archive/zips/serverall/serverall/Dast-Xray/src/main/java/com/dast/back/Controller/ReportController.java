package com.dast.back.Controller;

import com.dast.back.Bean.TaskReport;
import com.dast.back.Service.ReportService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.List;

@CrossOrigin
@RestController
@RequestMapping("/api/report")
public class ReportController {



    @Autowired
    private ReportService reportService;

    @GetMapping("/list")
    public List<TaskReport> getTasks(@RequestParam(defaultValue = "1") int page,
                                   @RequestParam(defaultValue = "10") int size,@RequestParam int source) {
        return  reportService.getTaskReports(page,size,source);
    }


    @GetMapping("/view")
    public ResponseEntity<String> viewReport(@RequestParam("id") Integer id,@RequestParam("task_id") Long taskid) throws IOException {
        String reportPath = reportService.getReportPathById(id,taskid);
        if (reportPath == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("报告不存在");
        }
        File file = new File(reportPath);
        if (!file.exists()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("文件不存在");
        }

        byte[] bytes = Files.readAllBytes(file.toPath());
        String html = new String(bytes, StandardCharsets.UTF_8);
        return ResponseEntity.ok()
                .contentType(MediaType.TEXT_HTML)
                .body(html);
    }

    @DeleteMapping("/delete")
    public ResponseEntity<String> deleteReport(@RequestParam("id") Integer id,@RequestParam("task_id") Long task_id,@RequestParam("path") String path) {
        try {
            int rows = reportService.deleteReportById(id,task_id,path);
            if (rows > 0) {
                return ResponseEntity.ok("删除成功");
            } else {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body("报告不存在");
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("删除失败: " + e.getMessage());
        }
    }

}

