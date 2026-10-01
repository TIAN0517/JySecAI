#!/usr/bin/env python3
"""
phish_server supervisor - 釣魚伺服器自動重啟守護進程
功能:
  - 啟動 phish_server.py
  - 監控進程是否存活
  - 異常退出時自動重啟 (最多 max_restarts 次)
  - 記錄重啟日誌
  - 健康檢查 endpoint

Usage:
  python3 phish_supervisor.py              # 前台運行 (阻塞)
  python3 phish_supervisor.py --daemon     # 背景守護進程
"""
import subprocess
import time
import os
import sys
import signal
import logging
from datetime import datetime

SERVER_SCRIPT = "/mnt/c/Users/Administrator/desktop/JySecAI/data/poc_scripts/phish_server.py"
LOG_FILE = "/mnt/c/Users/Administrator/desktop/JySecAI/data/poc_scripts/phish_supervisor.log"
PORT = 9090
MAX_RESTARTS = 10
RESTART_DELAY = 3  # seconds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


def check_health(port=PORT):
    """Check if the server is responding."""
    try:
        import urllib.request
        urllib.request.urlopen(f"http://localhost:{port}/login", timeout=5)
        return True
    except Exception:
        return False


def run_server():
    """Start and monitor the phish server with auto-restart."""
    restart_count = 0
    process = None

    def signal_handler(signum, frame):
        logger.info("Received shutdown signal, stopping server...")
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info(f"Supervisor started, monitoring {SERVER_SCRIPT}")
    logger.info(f"Health check port: {PORT}")

    while True:
        try:
            # Start the server
            logger.info(f"Starting phish_server.py (attempt {restart_count + 1}/{MAX_RESTARTS + 1})...")
            process = subprocess.Popen(
                [sys.executable, SERVER_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd="/mnt/c/Users/Administrator/desktop/JySecAI"
            )
            logger.info(f"Server started with PID {process.pid}")

            # Wait for it to be ready
            for i in range(10):
                time.sleep(1)
                if check_health(PORT):
                    logger.info(f"Server is healthy (responded to health check)")
                    break
            else:
                logger.warning("Server did not respond to health check within 10s")

            # Wait for the process to exit
            exit_code = process.wait()
            logger.info(f"Server exited with code {exit_code}")

            if exit_code == 0:
                logger.info("Server exited cleanly, not restarting")
                break

            # Auto-restart on crash
            restart_count += 1
            if restart_count > MAX_RESTARTS:
                logger.error(f"Max restarts ({MAX_RESTARTS}) exceeded, giving up")
                break

            logger.warning(f"Server crashed, restarting in {RESTART_DELAY}s... (restart {restart_count}/{MAX_RESTARTS})")
            time.sleep(RESTART_DELAY)

        except Exception as e:
            logger.error(f"Supervisor error: {e}")
            time.sleep(RESTART_DELAY)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="Run as background daemon")
    parser.add_argument("--health", action="store_true", help="Check health only")
    args = parser.parse_args()

    if args.health:
        if check_health(PORT):
            print(f"✅ Server is healthy on port {PORT}")
            sys.exit(0)
        else:
            print(f"❌ Server is NOT responding on port {PORT}")
            sys.exit(1)

    if args.daemon:
        # Fork to background
        pid = os.fork()
        if pid > 0:
            print(f"Supervisor daemonized, PID: {pid}")
            sys.exit(0)
        os.setsid()
        # Redirect stdin/stdout/stderr
        sys.stdin = open("/dev/null", "r")
        sys.stdout = open(os.devnull, "w")

    run_server()
