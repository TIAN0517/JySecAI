package com.dast.back.Controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.concurrent.*;

@RestController
@RequestMapping("/sse")
@CrossOrigin(origins = "*")
public class LogSseController {
    private static final Logger log = LoggerFactory.getLogger(LogSseController.class);

    private static final ConcurrentMap<String, SseEmitter> CLIENTS = new ConcurrentHashMap<>();

    private static final ExecutorService SSE_EXECUTOR = Executors.newCachedThreadPool();

    @GetMapping("/logs")
    public SseEmitter streamLogs(@RequestParam String tag) {
        SseEmitter emitter = new SseEmitter(30 * 60 * 1000L);
        CLIENTS.put(tag, emitter);


        log.info("[SSE] connected: " + tag);

        emitter.onCompletion(() -> {
            CLIENTS.remove(tag);
            log.info("[SSE] completed: " + tag);
        });
        emitter.onTimeout(() -> {
            CLIENTS.remove(tag);
            log.info("[SSE] timeout: " + tag);
        });
        emitter.onError(e -> {
            CLIENTS.remove(tag);
            log.info("[SSE] error: " + tag + " => " + e.getMessage());
        });

        try {
            emitter.send(SseEmitter.event().data("✅ Connected to " + tag));
        } catch (IOException ignored) {}

        return emitter;
    }

    public static void sendLog(String tag, String line) {
        SseEmitter emitter = CLIENTS.get(tag);
        if (emitter == null) return;
        SSE_EXECUTOR.submit(() -> {
            try {
                emitter.send(SseEmitter.event().data(line));
            } catch (IOException e) {
                CLIENTS.remove(tag);
                log.info("[SSE] disconnected (send failed): " + tag);
            } catch (IllegalStateException closed) {
                CLIENTS.remove(tag);
                log.info("[SSE] already closed: " + tag);
            }
        });
    }
}
