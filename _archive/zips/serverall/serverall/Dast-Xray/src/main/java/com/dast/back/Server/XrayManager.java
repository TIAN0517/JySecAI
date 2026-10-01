package com.dast.back.Server;

import com.dast.back.Bean.Task;
import com.dast.back.Bean.TaskReport;
import com.dast.back.Bean.WebHook;
import com.dast.back.Controller.LogSseController;
import com.dast.back.Service.WebHookService;
import com.dast.back.mapper.ReportMapper;
import com.dast.back.mapper.TaskMapper;
import com.dast.back.mapper.WebHookMapper;
import com.dast.back.util.CustomWebhookSender;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.ServerSocket;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class XrayManager {

    private final ReportMapper reportMapper;
    private final TaskMapper taskMapper;
    private final WebHookService webHookMapper;
    private final ConcurrentMap<Integer, Process> runningProcesses = new ConcurrentHashMap<>();
    private final ConcurrentMap<Integer, XrayProcessInfo> processInfos = new ConcurrentHashMap<>();


    private static final Logger log = LoggerFactory.getLogger(XrayManager.class);
    private static final Pattern SAFE_FILENAME = Pattern.compile("^[a-zA-Z0-9._\\-]+$");
    private static final Pattern XRAY_STATUS_PATTERN = Pattern.compile("pending:\\s*(\\d+)");

    private final Path resultDir;
    private final ExecutorService ioExecutor = Executors.newCachedThreadPool();
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);

    // 可配置参数
    private final int checkIntervalSeconds = 5;      // 每30秒检测一次
    private final int idleTimeoutSeconds = 10;        // 60秒内无新日志视为静默
    private final int consecutiveRequired = 2;        // 连续3次静默才判定完成

    public XrayManager(Path resultDir, ReportMapper reportMapper, TaskMapper taskMapper, WebHookService webHookMapper) throws IOException {
        this.resultDir = resultDir;
        this.reportMapper = reportMapper;
        this.taskMapper = taskMapper;
        this.webHookMapper = webHookMapper;
        if (!Files.exists(resultDir)) {
            Files.createDirectories(resultDir);
        }
    }

    public int startXray(String xrayPath, String format, String output,
                         Long id, String name, String url, Integer source, String uuid) throws IOException {

        Objects.requireNonNull(xrayPath);
        Objects.requireNonNull(format);
        Objects.requireNonNull(output);

        format = format.trim().toLowerCase(Locale.ROOT);
        if (!"html".equals(format) && !"json".equals(format)) {
            throw new IllegalArgumentException("format must be 'html' or 'json'");
        }

        if (!SAFE_FILENAME.matcher(output).matches()) {
            throw new IllegalArgumentException("output filename contains unsafe characters");
        }

        Path xrayExecutable = Paths.get(xrayPath);
        if (xrayExecutable.isAbsolute() &&
                (!Files.exists(xrayExecutable) || !Files.isExecutable(xrayExecutable))) {
            throw new IllegalArgumentException("xrayPath not found or not executable: " + xrayPath);
        }

        int port = allocateEphemeralPort();
        Path outPath = resultDir.resolve(output);

        List<String> cmd = new ArrayList<>();
        cmd.add(xrayPath);
        cmd.add("webscan");
        cmd.add("--listen");
        cmd.add("127.0.0.1:" + port);
        cmd.add("--html-output");
        cmd.add(outPath.toString());
        cmd.add("--json-output");
        cmd.add(outPath.toString().replace(".html",".json"));

        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.directory(xrayExecutable.getParent().toFile());
        pb.redirectErrorStream(true);

        Process proc;
        try {
            proc = pb.start();
        } catch (IOException e) {
            throw new IOException("Failed to start xray", e);
        }

        // 插入报告记录
        TaskReport report = new TaskReport();
        report.setTask_id(id);
        report.setName(name);
        report.setUrl(url);
        report.setGroupId(uuid);
        report.setReport_path(resultDir + "/" + output);
        report.setStatus(0);
        report.setSource(source);

        reportMapper.insertReport(report);

        // 启动日志读取
        XrayProcessInfo info = new XrayProcessInfo(port, uuid, id, proc,resultDir + "/" + output);
        processInfos.put(port, info);
        runningProcesses.put(port, proc);

        ioExecutor.submit(() -> streamToLogger(proc.getInputStream(), "XRAY-OUT[" + port + "]", info));
        return port;
    }

    private void streamToLogger(InputStream in, String tag, XrayProcessInfo info) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (Thread.currentThread().isInterrupted()) {
                    log.info("⏹ [{}] 日志线程检测到中断信号，安全退出", tag);
                    break;
                }

                final String logLine = line;
                log.info(tag + " " + logLine);
                LogSseController.sendLog(tag, logLine);

                info.lastLogTime = Instant.now();
                Matcher m = XRAY_STATUS_PATTERN.matcher(logLine);
                if (m.find()) {
                    info.lastPending = Integer.parseInt(m.group(1));
                }

                if (logLine.contains("All pending requests have been scanned")) {
                    startOrResetMonitor(info);
                }
            }
        } catch (IOException e) {
            log.warn("⚠️ [{}] 日志流结束或被关闭：{}", tag, e.getMessage());
        }
    }


    /** 启动或重置监控任务 */
    private void startOrResetMonitor(XrayProcessInfo info) {
        if (info.monitorTask != null && !info.monitorTask.isCancelled()) {
            info.monitorTask.cancel(false);
            log.info("🔁 重置 Xray (" + info.port + ") 监控任务");
        }
        info.monitorTask = scheduler.scheduleAtFixedRate(() -> checkScanCompletion(info),
                checkIntervalSeconds, checkIntervalSeconds, TimeUnit.SECONDS);
    }


    private void checkScanCompletion(XrayProcessInfo info) {
        long idleDuration = Duration.between(info.lastLogTime, Instant.now()).getSeconds();
        boolean idle = idleDuration >= idleTimeoutSeconds;
        boolean pendingZero = info.lastPending == 0;

        if (idle && pendingZero) {
            info.silentCount++;
            log.info("📡 [Port {}] 静默检测 {}/{} (pending=0)", info.port, info.silentCount, consecutiveRequired);
        } else {
            info.silentCount = 0;
        }

        if (info.silentCount >= consecutiveRequired) {
            log.info("✅ Xray [{}] 连续 {} 次静默，确认扫描完成，准备停止", info.port, consecutiveRequired);
            stopAndFinalize(info);
        }
    }

    private void stopAndFinalize(XrayProcessInfo info) {
        try {
            if (info.monitorTask != null) info.monitorTask.cancel(false);
            stopXray(info.port);
            Thread.sleep(300);
            reportMapper.updateStatus(info.uuid, 1);
            reportMapper.updateTaskStatus(info.taskId, 2);
            log.info("🛑 已停止 Xray [{}]", info.port);
            List<Task> tasks=taskMapper.selectByGroupId(info.uuid);
            if (tasks == null || tasks.isEmpty()) {
                log.warn("⚠️ 未找到 groupId={} 对应的任务", info.uuid);
                return;
            }
            List<TaskReport> reports = new ArrayList<>();
            WebHook webHook=null;
            for (Task task:tasks) {
                if (task.getWebhookid()!=null && !task.getWebhookid().isEmpty()){
                    webHook=webHookMapper.selectById(task.getWebhookid());
                    reports=reportMapper.getLatestReportsByGroup(task.getSource(),task.getGroupId(),info.outPath);

                }
            }

            if (reports != null && !reports.isEmpty())
            {
                for (TaskReport report:reports){
                    CustomWebhookSender.sendMain(webHook.getWebhookurl(),webHook.getSecret(),report);
                }
            }

        } catch (Exception e) {
            log.error("⚠️ 停止 Xray 进程出错 [" + info.port + "]", e);
        }
    }

    public boolean stopXray(int port) {
        Process p = runningProcesses.remove(port);
        processInfos.remove(port);
        if (p == null) return true;
        p.destroy();
        try {
            if (!p.waitFor(5, TimeUnit.SECONDS)) p.destroyForcibly();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            p.destroyForcibly();
        }
        return true;
    }

    private int allocateEphemeralPort() throws IOException {
        try (ServerSocket ss = new ServerSocket(0)) {
            ss.setReuseAddress(true);
            return ss.getLocalPort();
        }
    }

    public void shutdown() {
        for (Map.Entry<Integer, Process> e : runningProcesses.entrySet()) {
            try {
                e.getValue().destroy();
                e.getValue().waitFor(3, TimeUnit.SECONDS);
            } catch (Exception ignored) {}
        }

        runningProcesses.clear();
        processInfos.clear();
        ioExecutor.shutdownNow();
        scheduler.shutdownNow();
    }

    private static class XrayProcessInfo {
        final int port;
        final String uuid;
        final Long taskId;
        final Process process;
        volatile Instant lastLogTime = Instant.now();
        volatile int lastPending = -1;
        volatile int silentCount = 0;
        volatile ScheduledFuture<?> monitorTask;
        final String outPath;

        XrayProcessInfo(int port, String uuid, Long taskId, Process process, String outPath) {
            this.port = port;
            this.uuid = uuid;
            this.taskId = taskId;
            this.process = process;
            this.outPath=outPath;
        }
    }
}

