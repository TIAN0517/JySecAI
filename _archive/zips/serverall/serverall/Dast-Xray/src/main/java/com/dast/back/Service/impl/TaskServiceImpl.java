package com.dast.back.Service.impl;

import com.dast.back.Bean.Task;
import com.dast.back.Bean.TaskReport;
import com.dast.back.Bean.ToolsSetting;
import com.dast.back.Server.CrawlergoManager;
import com.dast.back.Server.XrayManager;
import com.dast.back.Service.TaskService;
import com.dast.back.Service.WebHookService;
import com.dast.back.mapper.TaskMapper;
import com.dast.back.mapper.ReportMapper;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
public class TaskServiceImpl implements TaskService {
    private static final Logger log = LoggerFactory.getLogger(TaskServiceImpl.class);

    @Autowired
    private TaskMapper taskMapper;

    @Autowired
    private ReportMapper reportMapper;

    @Autowired
    private WebHookService webHookService;



    private String xray_path;
    private String crawlergo_path;
    private String chromepath;
    private Path xrayDir;
    private Path resultDir;
    private XrayManager m;
    private CrawlergoManager mgr;
    private ExecutorService executor;

    @PostConstruct
    public void init() {
        try {
            reloadToolSetting();
        } catch (Exception e) {
            // 不抛异常，只记录日志
            log.warn("[WARN] 工具路径未配置或初始化失败，可在后台填写配置后重新加载：" + e.getMessage());
        }
    }


    public synchronized void reloadToolSetting() {
        ToolsSetting toolPath = taskMapper.getToolsPath();

        if (toolPath == null || isInvalidPath(toolPath.getXrayPath())) {
            log.warn("[WARN] 工具路径未配置或无效，请在系统设置中填写配置。");
            return; // 不再抛异常
        }

        this.xray_path = toolPath.getXrayPath();
        this.crawlergo_path = toolPath.getCrawlergoPath();
        this.chromepath = toolPath.getChromePath();

        try {
            this.xrayDir = Paths.get(xray_path).getParent();
            this.resultDir = xrayDir.resolve("result");

            if (Files.notExists(resultDir)) {
                Files.createDirectories(resultDir);
            }

            this.m = new XrayManager(resultDir, reportMapper, taskMapper, webHookService);
            this.mgr = new CrawlergoManager();

            log.info("[INFO] xray工具初始化完成：" + xray_path);
        } catch (Exception e) {
            log.error("[ERROR] 初始化工具路径失败：" + e.getMessage());
            e.printStackTrace();
        }
    }


    private boolean isInvalidPath(String path) {
        if (path == null || path.trim().isEmpty()) return true;
        try {
            Paths.get(path); // 校验路径格式
            return false;
        } catch (InvalidPathException e) {
            return true;
        }
    }





    @Override
    public PageInfo<Task> getAllTasks(int pageNum, int pageSize,int source) {
        PageHelper.startPage(pageNum, pageSize);
        List<Task> list = taskMapper.getAllTasks(source);
        return new PageInfo<>(list);
    }

    @Override
    public List<Task> getTaskList(int pageNum, int pageSize,int source) {
        List<Task> list = taskMapper.getAllTasks(source);
        return list;
    }

    @Override
    public Integer addTask(Task task) {
        task.setStatus(0);
        task.setGroupId(null);
        task.setGroupId(UUID.randomUUID().toString());
        task.setWebhookid(task.getWebhookid());
        if (!task.getUrl().startsWith("http")) {
            return 0;
        }
        task.setCreatetime(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        return taskMapper.insertTask(task);
    }


    @Override
    public List<Long> addTask(List<Task> tasks, boolean isList) {

        String groupId = UUID.randomUUID().toString(); // 时间戳作 groupId
        List<Long> ids = new ArrayList<>();


        for (Task task : tasks) {
            if (task.getUrl() == null || !task.getUrl().startsWith("http")) continue;
            task.setGroupId(groupId);
            task.setStatus(0);
            if (task.getFormat() == null) task.setFormat("html");
            task.setCreatetime(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
            if (task.getWebhookid() == null) {
                task.setWebhookid("");
            }else {
                task.setWebhookid(task.getWebhookid());
            }
            taskMapper.insertTask(task);
            ids.add(task.getId());
        }
        return ids;
    }


    @Override
    public List<String> addTaskByOpenapi(List<Task> tasks) {

        String groupId = UUID.randomUUID().toString(); // 时间戳作 groupId
        List<String> ids = new ArrayList<>();


        for (Task task : tasks) {
            if (task.getUrl() == null || !task.getUrl().startsWith("http")) continue;
            task.setGroupId(groupId);
            task.setStatus(0);
            if (task.getFormat() == null) task.setFormat("html");
            task.setCreatetime(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
            if (task.getWebhookid() == null) {
                task.setWebhookid("");
            }else {
                task.setWebhookid(task.getWebhookid());
            }
            taskMapper.insertTask(task);
            ids.add(task.getGroupId());
        }
        return ids;
    }






    @Override
    public Integer deleteTask(Long id) {
        return taskMapper.deleteTask(id);
    }


    @Override
    public Integer deleteTaskByGroup(String id) {
        return taskMapper.deleteTaskbyGroup(id);
    }

    @Override
    public Integer updateStatus(Long id, Integer status) {
        return taskMapper.updateStatus(id, status);
    }

    @Override
    public Integer startTask(Long id,Integer source) throws IOException {
        Task taskInfo = getOne(id);

        if (taskInfo == null) {
            return 0; // 没查到任务
        }
        String host = new URL(taskInfo.getUrl()).getHost().replace(".", "_");
        LocalDateTime now = LocalDateTime.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd-HHmmss");
        String filename = host + "_" + now.format(formatter);

        String reportPath;
        if ("html".equals(taskInfo.getFormat())) {
            reportPath = filename.replace(" ","-") + ".html";
        } else {
            reportPath = filename.replace(" ","-") + ".json";
        }
        updateStatus(id,1);


        if (runTask(taskInfo.getName(),taskInfo.getUrl(),reportPath,taskInfo.getFormat(),id,source,taskInfo.getGroupId())==1){
            return 1;
        }else {
            return 0;
        }

    }

    @Override
    public Integer startTask(String id, Integer source) throws IOException {
        List<Task> taskInfo = selectByGroupId(id);

        if (taskInfo == null || taskInfo.isEmpty()) {
            return 0;
        }

        // 动态调整线程池大小
        int poolSize = Math.min(taskInfo.size(), 10);
        executor = Executors.newFixedThreadPool(poolSize);

        for (Task task : taskInfo) {
            executor.submit(() -> {
                try {
                    String host = new URL(task.getUrl()).getHost().replace(".", "_");
                    LocalDateTime now = LocalDateTime.now();
                    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd-HHmmss");
                    String filename = host + "_" + now.format(formatter);

                    String reportPath = filename.replace(" ", "-") +
                            ("html".equalsIgnoreCase(task.getFormat()) ? ".html" : ".json");

                    updateStatus(task.getId(), 1);
                    runTask(task.getName(), task.getUrl(), reportPath, task.getFormat(), task.getId(), source,task.getGroupId());
                    log.info("扫描中: " + task.getUrl());
                    Thread.sleep(1000);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            });
        }
        return 1;
    }

    @Override
    public Integer updateTools(ToolsSetting toolsSetting) {
        return taskMapper.updateTool(toolsSetting);
    }


    @Override
    public Integer updateTaskcol(Long id, String xyport, String crawlerid) throws IOException {
        return taskMapper.updateTaskcol(id,xyport,crawlerid);
    }

    @Override
    public Integer stopTask(Long id) {
        Task task=getOne(id);
        if (task==null){
            return 13001; //关闭任务异常
        }
        try {
            mgr.stopCrawlergo(task.getCrawlerid());
            m.stopXray(Integer.parseInt(task.getXyport()));
            List<TaskReport> reports =reportMapper.getReportsByGroupIdAll(task.getGroupId());
            for (TaskReport report : reports){
                reportMapper.deleteReportById(report.getId(),report.getTask_id());
            }
            taskMapper.updateStatus(id,3);
        }catch (NullPointerException e){
            taskMapper.updateStatus(id,3);
            return 13000;
        }catch (Exception e1){
            return 13001;
        }

        return 13000;//关闭任务成功
    }


    @Override
    public Integer stopTask(String id) {
        List<Task> tasks=selectByGroupId(id);
        if (tasks==null){
            return 13001; //关闭任务异常
        }
        for (Task task : tasks){
            try {

                mgr.stopCrawlergo(task.getCrawlerid());
                m.stopXray(Integer.parseInt(task.getXyport()));
                List<TaskReport> reports =reportMapper.getReportsByGroupIdAll(task.getGroupId());
                for (TaskReport report : reports){
                    reportMapper.deleteReportById(report.getId(),report.getTask_id());
                }
                taskMapper.updateStatusByGroup(task.getGroupId(),3);
            }catch (NullPointerException e){
                taskMapper.updateStatusByGroup(task.getGroupId(),3);
                return 13000;
            }catch (Exception e1){
                return 13001;
            }

        }

        return 13000;//关闭任务成功
    }

    @Override
    public Integer updateTask(Task task) throws MalformedURLException {
//        task.setUpdatetime(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        return taskMapper.updateTask(task);
    }

    @Override
    public Task getOne(Long id) {
        return taskMapper.getOne(id);
    }

    public List<Task> selectByGroupId(String id) {
        return taskMapper.selectByGroupId(id);
    }

    @Override
    public ToolsSetting getToolsPath() {
        return taskMapper.getToolsPath();
    }


    public Integer runTask(String name,String url,String output,String format,Long id,Integer source,String uuid) throws IOException {

        if (!new File(xray_path).exists()){
            return 12001;
        }
        int xrayport=startXaryProxy(xray_path, format, output,id,name,url,source,uuid);
        String xrayProxyLis="127.0.0.1:"+ xrayport;




        if(!new File(crawlergo_path).exists()){
            return 12002; //crawlergo path不存在
        }

        if(!new File(chromepath).exists()){
            return 12003; //chromepath path不存在
        }

        CrawlergoManager.CrawlergoProcessInfo info = mgr.startCrawlergo(crawlergo_path,chromepath,url,formatToHttpUrl(xrayProxyLis),null);


        updateTaskcol(id, String.valueOf(xrayport),info.getId());
        return 1;
    }

    public static String formatToHttpUrl(String hostPort) {
        if (hostPort == null || hostPort.isEmpty()) {
            return "";
        }

        if (hostPort.startsWith("http://") || hostPort.startsWith("https://")) {
            return hostPort.endsWith("/") ? hostPort : hostPort + "/";
        }

        return "http://" + hostPort + (hostPort.endsWith("/") ? "" : "/");
    }


    public Integer startXaryProxy(String xrayPath,String format,String output,Long id,String name,String url,Integer source,String uuid) throws IOException {
        if (format.equals("html")){
            return m.startXray(xrayPath,"html",output,id,name,url,source,uuid);
        }else if(format.equals("json")) {
            return m.startXray(xrayPath,"json",output,id,name,url,source,uuid);
        }

        return 0;
    }
}
