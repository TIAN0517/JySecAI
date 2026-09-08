"""Tests use only temporary config, mocked networking, and a benign Python child."""

import errno
import io
import os
from pathlib import Path
import queue
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unittest
from unittest.mock import Mock, call, patch

import desktop_runtime as runtime

_REAL_POPEN = subprocess.Popen
_CONFIG = "version: test-version\nserver:\n  host: 0.0.0.0\n  port: 6688\nauth:\n  api_key: yaml-secret-sentinel\n"


def wait_for(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError("Timed out waiting for a test condition")
        time.sleep(0.005)


class TempConfig(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parent
        self.assertTrue(parent.is_dir())
        temporary = tempfile.TemporaryDirectory(prefix="desktop-runtime-test-", dir=parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "config.yaml"
        self.write(_CONFIG)

    def write(self, text):
        self.path.write_text(text, encoding="utf-8")


class SettingsTests(TempConfig):
    def test_nested_fields_comments_and_tls_default(self):
        self.write("version: v2 # comment\nport: 9999\nother:\n  port: 1111\nserver:\n  port: 6688 # local\n")
        settings = runtime.read_settings(self.path)
        self.assertEqual((settings.host, settings.port, settings.tls, settings.version),
                         ("127.0.0.1", 6688, False, "v2"))
        self.assertEqual(settings.url, "http://127.0.0.1:6688")

    def test_wildcards_and_ipv6(self):
        for host, expected in [("", "127.0.0.1"), ("0.0.0.0", "127.0.0.1"),
                               ("localhost", "127.0.0.1"), ("LOCALHOST", "127.0.0.1"),
                               ("127.0.0.2", "127.0.0.2"), ("::", "::1"),
                               ("::1", "::1"), ("[::]", "::1"), ("[::1]", "::1")]:
            with self.subTest(host=host):
                self.write(f"server:\n  host: '{host}'\n  port: 6688\n")
                settings = runtime.read_settings(self.path)
                self.assertEqual(settings.host, expected)
                url_host = f"[{expected}]" if ":" in expected else expected
                self.assertEqual(settings.url, f"http://{url_host}:6688")

    def test_tls_flags_and_certificate_pair(self):
        for extra, expected in [("", False), ("tls_enabled: true", True),
                                ("tls_auto_self_sign: true", True),
                                ("tls_cert_path: cert.pem\n  tls_key_path: key.pem", True),
                                ("tls_cert_path: cert.pem", False),
                                ("tls_enabled: false\n  tls_auto_self_sign: false", False)]:
            with self.subTest(extra=extra):
                self.write("server:\n  port: 6688\n  " + extra + "\n")
                self.assertIs(runtime.read_settings(self.path).tls, expected)

    def test_invalid_settings(self):
        documents = ["", "[]", "server: []", "server: {}", "server:\n  port: 0",
                     "server:\n  port: -1", "server:\n  port: 65536", "server:\n  port: true",
                     "server:\n  port: '6688'", "server:\n  port: 6688\n  tls_enabled: 'false'",
                     "server:\n  port: 6688\n  tls_key_path: []", "version: []\nserver:\n  port: 6688"]
        for document in documents:
            with self.subTest(document=document):
                self.write(document)
                with self.assertRaises(ValueError):
                    runtime.read_settings(self.path)

    def test_non_loopback_hosts_rejected(self):
        for host in ["192.0.2.1", "example.invalid", "localhost.example.invalid", "https://localhost",
                     "user:password@localhost", "2001:db8::1", "::1%eth0", "*", "2130706433"]:
            with self.subTest(host=host):
                self.write(f"server:\n  host: '{host}'\n  port: 6688")
                with self.assertRaisesRegex(ValueError, "Non-loopback"):
                    runtime.read_settings(self.path)

    def test_server_env_expansion_is_rejected_even_when_defined(self):
        with patch.dict(os.environ, {"DESKTOP_TEST_PORT": "6688"}):
            for field, value in [("port", "${DESKTOP_TEST_PORT}"), ("port", "${UNSET:-6688}"),
                                 ("host", "${HOST:-localhost}"), ("tls_enabled", "${TLS:-true}"),
                                 ("tls_key_path", "${KEY}"), ("tls_cert_path", "${BROKEN")]:
                with self.subTest(field=field, value=value):
                    base = "server:\n" + ("  port: 6688\n" if field != "port" else "")
                    self.write(base + f"  {field}: '{value}'\n")
                    with self.assertRaisesRegex(ValueError, "placeholders"):
                        runtime.read_settings(self.path)

    def test_invalid_yaml_never_exposes_source_or_unsafe_tags(self):
        for document in ["server: [private-secret-sentinel", "!!python/object/apply:os.system ['DO_NOT_RUN']"]:
            self.write(document)
            try:
                runtime.read_settings(self.path)
            except ValueError as exc:
                rendered = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                self.assertNotIn(document, rendered)
                self.assertNotIn("private-secret-sentinel", rendered)
                self.assertNotIn("DO_NOT_RUN", str(exc))
            else:
                self.fail("Invalid YAML was accepted")

    def test_missing_file_and_oversized_config(self):
        self.path.unlink()
        with self.assertRaises(ValueError):
            runtime.read_settings(self.path)
        self.write("#" + "x" * (2 * 1024 * 1024))
        with self.assertRaises(ValueError):
            runtime.read_settings(self.path)

    def test_secret_collection_handles_nested_alias_cycles(self):
        self.write(_CONFIG + "recursive: &cycle\n  self: *cycle\n  credentials:\n    values: [hidden-value]\n")
        settings, secrets = runtime._read_config(self.path)
        self.assertIn("hidden-value", secrets)
        self.assertNotIn("yaml-secret-sentinel", repr(settings))
        self.assertEqual(runtime.redact("hidden-value yaml-secret-sentinel", secrets),
                         "[REDACTED] [REDACTED]")


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.tcp = self.enterContext(patch.object(runtime.socket, "create_connection"))
        self.http = self.enterContext(patch.object(runtime.http.client, "HTTPConnection"))
        self.https = self.enterContext(patch.object(runtime.http.client, "HTTPSConnection"))
        self.response = self.http.return_value.getresponse.return_value
        self.response.status = 200
        self.response.read.return_value = b"<html><title>JySecAI Console</title></html>"

    def test_bounded_get_no_proxy_auth_body_or_redirects(self):
        with patch.dict(os.environ, {"HTTP_PROXY": "http://example.invalid", "HTTPS_PROXY": "http://example.invalid"}):
            occupied, status, latency, matched = runtime._probe(runtime.EndpointSettings("localhost", 6688, False))
        self.assertEqual((occupied, status, matched), (True, 200, True))
        self.assertGreaterEqual(latency, 0.0)
        self.tcp.assert_called_once_with(("127.0.0.1", 6688), timeout=1)
        self.http.assert_called_once_with("127.0.0.1", 6688, timeout=1)
        self.http.return_value.request.assert_called_once_with("GET", "/", headers={"Connection": "close"})
        self.response.read.assert_called_once_with(8192)
        self.http.return_value.close.assert_called_once()
        self.https.assert_not_called()

    def test_redirect_is_not_followed(self):
        self.response.status = 302
        self.response.read.return_value = b""
        self.response.getheader.return_value = "https://example.invalid/"
        self.assertEqual(runtime._probe(runtime.EndpointSettings("127.0.0.1", 6688, False))[1::2], (302, False))
        self.assertEqual(self.http.return_value.request.call_count, 1)
        self.assertEqual(self.tcp.call_count, 1)
        self.response.getheader.assert_not_called()

    def test_ipv6_local_unverified_tls(self):
        self.https.return_value.getresponse.return_value = self.response
        runtime._probe(runtime.EndpointSettings("::", 6688, True))
        self.tcp.assert_called_once_with(("::1", 6688), timeout=1)
        args, kwargs = self.https.call_args
        self.assertEqual(args, ("::1", 6688))
        self.assertEqual(kwargs["timeout"], 1)
        self.assertEqual(kwargs["context"].verify_mode, ssl.CERT_NONE)
        self.assertFalse(kwargs["context"].check_hostname)
        self.http.assert_not_called()

    def test_network_boundary_rejects_remote_settings(self):
        with self.assertRaises(ValueError):
            runtime._probe(runtime.EndpointSettings("192.0.2.1", 6688, True))
        self.tcp.assert_not_called()
        self.http.assert_not_called()
        self.https.assert_not_called()

    def test_refused_unknown_and_non_http_listener(self):
        settings = runtime.EndpointSettings("127.0.0.1", 6688, False)
        self.tcp.side_effect = ConnectionRefusedError(errno.ECONNREFUSED, "refused")
        self.assertEqual(runtime._probe(settings), (False, None, None, False))
        self.tcp.side_effect = TimeoutError("timeout")
        self.assertEqual(runtime._probe(settings), (None, None, None, False))
        self.tcp.side_effect = None
        self.http.return_value.request.side_effect = OSError("private-error-sentinel")
        self.assertEqual(runtime._probe(settings), (True, None, None, False))
        self.http.return_value.close.assert_called_once()

    def test_body_timeout_retains_http_availability_not_identity(self):
        self.response.read.side_effect = TimeoutError()
        occupied, status, _, matched = runtime._probe(runtime.EndpointSettings("127.0.0.1", 6688, False))
        self.assertEqual((occupied, status, matched), (True, 200, False))


class FakeProcess:
    def __init__(self, output=b"", code=None):
        self.pid, self.returncode, self.stdout = 12345, code, io.BytesIO(output)
        self.terminate = Mock(side_effect=self.exit)
        self.kill = Mock(side_effect=self.exit)
        self.wait = Mock(side_effect=self.wait_for_exit)

    def exit(self):
        self.returncode = 0

    def poll(self):
        return self.returncode

    def wait_for_exit(self, timeout):
        if self.returncode is None:
            raise subprocess.TimeoutExpired("benign-mock", timeout)
        return self.returncode


class RuntimeTests(TempConfig):
    def setUp(self):
        super().setUp()
        self.executable = self.root / ("jysecai.exe" if runtime._WINDOWS else "jysecai")
        self.executable.touch()
        self.executable.chmod(0o700)
        self.probe = self.enterContext(patch.object(runtime, "_probe", return_value=(False, None, None, False)))
        self.enterContext(patch.object(runtime, "psutil", None))
        self.process = FakeProcess()
        self.popen = self.enterContext(patch.object(runtime.subprocess, "Popen", return_value=self.process))
        self.monitor_patch = patch.object(runtime.DesktopRuntime, "begin_monitoring")
        self.monitor_patch.start()
        self.addCleanup(self.monitor_patch.stop)
        self.backend = runtime.DesktopRuntime(self.root)
        self.addCleanup(self.backend.close)

    def idle(self):
        wait_for(lambda: not self.backend.snapshot()["busy"] and not self.backend._operation.locked())

    def start_owned(self):
        self.assertIs(self.backend.start(), True)
        self.idle()
        self.assertTrue(self.backend.snapshot()["owned"])

    def messages(self):
        events = []
        while True:
            try:
                events.append(self.backend.events.get_nowait())
            except queue.Empty:
                return events

    def test_constructor_and_snapshot_interface(self):
        self.popen.assert_not_called()
        self.probe.assert_not_called()
        self.assertIsNone(self.backend._monitor)
        self.assertEqual(self.backend.events.maxsize, 1000)
        snapshot = self.backend.snapshot()
        self.assertEqual(set(snapshot), {"state", "detail", "busy", "owned", "pid", "http_ok", "http_status",
                                        "latency_ms", "cpu_percent", "memory_mb", "uptime_seconds", "checked_at", "config_error"})
        self.assertIsNone(snapshot["checked_at"])
        self.assertIsNone(snapshot["pid"])
        snapshot["state"] = "changed"
        self.assertEqual(self.backend.snapshot()["state"], "stopped")
        self.assertNotIn("yaml-secret-sentinel", repr(self.backend.snapshot()))

    def test_reload_and_changed_config_invalid_at_start(self):
        self.write("server: [yaml-secret-sentinel")
        self.assertTrue(self.backend.start())
        self.idle()
        self.assertIsNone(self.backend.settings)
        self.assertTrue(self.backend.config_error)
        self.assertNotIn("yaml-secret-sentinel", repr(self.backend.snapshot()) + repr(self.messages()))
        self.popen.assert_not_called()
        self.write(_CONFIG.replace("6688", "7788"))
        self.assertTrue(self.backend.reload_config())
        self.assertEqual(self.backend.settings.port, 7788)
        self.start_owned()
        self.assertFalse(self.backend.reload_config())

    def test_invalid_initial_config_and_reload_return_false(self):
        self.write("server: [yaml-secret-sentinel")
        other = runtime.DesktopRuntime(self.root)
        self.addCleanup(other.close)
        self.assertIsNone(other.settings)
        self.assertEqual(other.snapshot()["state"], "error")
        self.assertIs(other.reload_config(), False)
        self.assertNotIn("yaml-secret-sentinel", other.config_error)

    def test_missing_executable_and_launch_failure(self):
        self.executable.unlink()
        self.assertTrue(self.backend.start())
        self.idle()
        self.assertEqual(self.backend.snapshot()["state"], "error")
        self.popen.assert_not_called()
        self.executable.touch()
        self.executable.chmod(0o700)
        self.popen.side_effect = OSError("private-error-sentinel")
        self.assertTrue(self.backend.start())
        self.idle()
        self.assertFalse(self.backend.snapshot()["owned"])
        self.assertNotIn("private-error-sentinel", repr(self.messages()) + repr(self.backend.snapshot()))

    def test_occupancy_external_conflict_unknown_never_owned_or_terminated(self):
        for result, state in [((True, 200, 1.0, True), "external"), ((True, 200, 1.0, False), "conflict"),
                              ((True, None, None, False), "conflict"), ((None, None, None, False), "error")]:
            with self.subTest(state=state):
                self.probe.return_value = result
                self.assertTrue(self.backend.start())
                self.idle()
                snapshot = self.backend.snapshot()
                self.assertEqual(snapshot["state"], state)
                self.assertFalse(snapshot["owned"])
                self.assertIsNone(snapshot["pid"])
                self.assertFalse(self.backend.stop())
                self.assertFalse(self.backend.restart())
                if state == "external":
                    self.assertIn("heuristic", snapshot["detail"])
                    self.assertIn("not readiness", snapshot["detail"])
        self.popen.assert_not_called()
        self.process.terminate.assert_not_called()
        self.process.kill.assert_not_called()

    def test_duplicate_operations_rejected_without_blocking(self):
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)

        def blocked_probe(settings):
            entered.set()
            self.assertTrue(release.wait(3))
            return False, None, None, False

        self.probe.side_effect = blocked_probe
        self.assertTrue(self.backend.start())
        self.assertTrue(entered.wait(1))
        self.assertTrue(self.backend.snapshot()["busy"])
        for operation in (self.backend.start, self.backend.stop, self.backend.restart, self.backend.reload_config):
            self.assertIs(operation(), False)
        release.set()
        self.idle()
        self.assertFalse(self.backend.start())
        self.assertEqual(self.popen.call_count, 1)

    def test_cwd_shell_flags_and_continuous_bounded_redacted_output(self):
        self.process.stdout = io.BytesIO(b"hello yaml-secret-sentinel\npassword=unknown-secret\n" +
                                        b"x" * 100000 + b"\nlast ordinary line\n")
        self.start_owned()
        wait_for(lambda: self.process.stdout.closed)
        args, kwargs = self.popen.call_args
        self.assertEqual(args[0], [str(self.executable), "--config", str(self.path), "--http"])
        self.assertEqual(kwargs["cwd"], str(self.root))
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["stdout"], subprocess.PIPE)
        self.assertEqual(kwargs["stderr"], subprocess.STDOUT)
        self.assertEqual(kwargs["creationflags"], 0x08000000 if runtime._WINDOWS else 0)
        events = self.messages()
        text = repr(events)
        self.assertNotIn("yaml-secret-sentinel", text)
        self.assertNotIn("unknown-secret", text)
        self.assertIn("last ordinary line", text)
        self.assertIn("Dropped an oversized log line", text)
        self.assertTrue(all(level in {"info", "warning", "error", "success"} and len(message) <= 4096
                            for level, message in events))

    def test_queue_overflow_reports_count_when_capacity_returns(self):
        self.messages()
        for _ in range(1007):
            self.backend._emit("info", "ordinary")
        self.assertEqual(self.backend.events.qsize(), 1000)
        self.messages()
        self.backend._emit()
        self.assertEqual(self.messages(), [("warning", "Dropped 7 messages: event queue was full.")])

    def test_early_exit_stays_visible_without_auto_restart(self):
        self.process.returncode = 7
        self.assertTrue(self.backend.start())
        self.idle()
        self.backend._sample()
        self.assertEqual(self.backend.snapshot()["state"], "error")
        self.assertIn("code 7", self.backend.snapshot()["detail"])
        self.assertFalse(self.backend.snapshot()["owned"])
        self.backend._sample()
        self.assertEqual(self.backend.snapshot()["state"], "error")
        self.assertEqual(self.popen.call_count, 1)

    def test_monitor_http_availability_and_optional_metrics_absent(self):
        self.start_owned()
        self.backend._started = time.monotonic() - 11
        self.backend._sample()
        self.assertEqual(self.backend.snapshot()["state"], "unresponsive")
        self.probe.return_value = (True, 503, 1.25, False)
        self.backend._sample()
        snapshot = self.backend.snapshot()
        self.assertEqual(snapshot["state"], "running")
        self.assertTrue(snapshot["http_ok"])
        self.assertEqual(snapshot["http_status"], 503)
        self.assertIn("availability only", snapshot["detail"])
        self.assertIsNone(snapshot["cpu_percent"])
        self.assertIsNone(snapshot["memory_mb"])
        self.assertGreaterEqual(snapshot["uptime_seconds"], 11)
        self.assertLess(abs(snapshot["checked_at"] - time.time()), 1)

    def test_metrics_are_only_created_for_owned_process(self):
        metrics_module = Mock(Error=RuntimeError)
        metrics = metrics_module.Process.return_value
        metrics.cpu_percent.return_value = 12.5
        metrics.memory_info.return_value.rss = 3 * 1024 * 1024
        with patch.object(runtime, "psutil", metrics_module):
            self.probe.return_value = (True, 200, 1.0, True)
            self.backend._sample()
            metrics_module.Process.assert_not_called()
            self.probe.return_value = (False, None, None, False)
            self.start_owned()
            self.backend._sample()
            metrics_module.Process.assert_called_once_with(self.process.pid)
            self.assertEqual(self.backend.snapshot()["cpu_percent"], 12.5)
            self.assertEqual(self.backend.snapshot()["memory_mb"], 3.0)

    def test_stop_timeout_kills_only_owned_handle(self):
        self.start_owned()
        self.process.terminate.side_effect = None
        self.assertTrue(self.backend.stop())
        self.idle()
        self.process.terminate.assert_called_once_with()
        self.process.kill.assert_called_once_with()
        self.assertEqual(self.process.wait.call_args_list, [call(timeout=5), call(timeout=1)])
        self.assertEqual(self.backend.snapshot()["state"], "stopped")
        self.assertFalse(self.backend.snapshot()["owned"])

    def test_restart_is_sequential_and_stop_failure_blocks_start(self):
        self.start_owned()
        history, second = [], FakeProcess()

        def terminate():
            history.append("terminate")
            self.process.exit()

        def wait(timeout):
            history.append("wait")
            return 0

        self.process.terminate.side_effect = terminate
        self.process.wait.side_effect = wait
        self.popen.side_effect = lambda *a, **k: (history.append("launch") or second)
        self.assertTrue(self.backend.restart())
        self.idle()
        self.assertEqual(history, ["terminate", "wait", "launch"])
        second.terminate.side_effect = OSError("private-error-sentinel")
        self.assertTrue(self.backend.restart())
        self.idle()
        self.assertEqual(self.popen.call_count, 2)
        self.assertTrue(self.backend.snapshot()["owned"])
        self.assertEqual(self.backend.snapshot()["state"], "error")
        self.assertNotIn("private-error-sentinel", repr(self.messages()))

    def test_kill_failure_retains_ownership_and_blocks_restart(self):
        self.start_owned()
        self.process.terminate.side_effect = None
        self.process.kill.side_effect = OSError("denied")
        self.assertTrue(self.backend.restart())
        self.idle()
        self.assertTrue(self.backend.snapshot()["owned"])
        self.assertEqual(self.backend.snapshot()["state"], "error")
        self.assertEqual(self.popen.call_count, 1)

    def test_stale_monitor_cannot_overwrite_reloaded_settings(self):
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)

        def blocked_probe(settings):
            entered.set()
            release.wait(3)
            return True, 200, 1.0, True

        self.probe.side_effect = blocked_probe
        sample = threading.Thread(target=self.backend._sample, daemon=True)
        sample.start()
        self.assertTrue(entered.wait(1))
        self.write(_CONFIG.replace("6688", "7788"))
        self.assertTrue(self.backend.reload_config())
        release.set()
        sample.join(1)
        self.assertFalse(sample.is_alive())
        self.assertEqual(self.backend.snapshot()["state"], "stopped")
        self.assertEqual(self.backend.settings.port, 7788)

    def test_monitor_starts_once_and_close_does_not_terminate(self):
        self.start_owned()
        self.monitor_patch.stop()
        self.backend.begin_monitoring()
        monitor = self.backend._monitor
        self.backend.begin_monitoring()
        self.assertIs(self.backend._monitor, monitor)
        self.assertTrue(monitor.daemon)
        self.backend.close()
        self.assertFalse(monitor.is_alive())
        self.assertTrue(self.backend.snapshot()["owned"])
        self.process.terminate.assert_not_called()
        self.process.kill.assert_not_called()
        self.backend.begin_monitoring()
        self.assertIs(self.backend._monitor, monitor)

    def test_benign_python_child_actual_launch_drain_and_stop(self):
        children = []

        def launch_benign(*args, **kwargs):
            child = _REAL_POPEN([sys.executable, "-B", "-u", "-c",
                                "import sys,time; print('yaml-secret-sentinel', flush=True); "
                                "print('benign stderr', file=sys.stderr, flush=True); time.sleep(30)"], **kwargs)
            children.append(child)
            return child

        def cleanup():
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.wait(timeout=2)
                wait_for(lambda: child.stdout.closed)

        self.addCleanup(cleanup)
        self.popen.side_effect = launch_benign
        self.start_owned()
        events = []

        def drained():
            events.extend(self.messages())
            return "benign stderr" in repr(events)

        wait_for(drained)
        self.assertNotIn("yaml-secret-sentinel", repr(events))
        self.assertIsNone(children[0].poll())
        self.assertTrue(self.backend.stop())
        self.idle()
        self.assertIsNotNone(children[0].poll())
        self.assertEqual(self.backend.snapshot()["state"], "stopped")


class RedactionTests(unittest.TestCase):
    def test_common_credential_forms_and_known_values(self):
        for text in ['{"api_key": "hidden-value"}', "password='hidden-value with spaces'",
                     "access_token=hidden-value", "Authorization: Bearer hidden-value",
                     "Bearer hidden-value", "Basic hidden-value", "--password hidden-value",
                     "https://user:hidden-value@localhost/", "Cookie: session=hidden-value",
                     "just hidden-value in a message"]:
            with self.subTest(text=text):
                secrets = ("hidden-value",) if text.startswith("just") else ()
                self.assertNotIn("hidden-value", runtime.redact(text, secrets))
        self.assertEqual(runtime.redact("ordinary local message"), "ordinary local message")

    def test_private_key_and_control_characters(self):
        text = "-----BEGIN PRIVATE KEY-----\nhidden-value\n-----END PRIVATE KEY-----"
        self.assertNotIn("hidden-value", runtime.redact(text))
        self.assertEqual(runtime.redact("\x1b[31mhello\x00\x1b[0m"), "hello")


if __name__ == "__main__":
    unittest.main()
