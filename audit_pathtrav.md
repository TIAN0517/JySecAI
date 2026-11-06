# Path Traversal & Unsafe File Handling Audit — JySecAI

**Scope:** `C:\Users\Administrator\desktop\jysecai` (Go), own code, defensive audit.
**Method:** static trace of every `os.Create/OpenFile/WriteFile/ReadFile/MkdirAll/Remove/RemoveAll`, `os.CreateTemp`, `io.Copy`, `c.File`, `http.ServeFile`, `c.FileAttachment`, plus `archive/zip` extraction. Every finding below was traced from HTTP route → handler → sink, and the path math was **empirically executed** where it decided severity.

**Excluded per instructions:** `internal/agent/agent.go` `resolveWithinPromptBase` (already fixed); the `.backup` writers in `internal/handler/config.go:1918` and `internal/handler/external_mcp.go:515` (already 0600).

---

## Counts

| Severity | Count |
|---|---|
| **S0** — arbitrary read/write by any authenticated user | **1** |
| **S1** — arbitrary read/write needing a specific role | **3** |
| **S2** — traversal confined to a workspace/base dir | **2** |
| **S3** — permission weakness / latent / info-disclosure | **9** |
| **Total** | **15** |

**Headline:** one genuine unauthenticated-tier arbitrary file read (`Viewer` role) via the skill-package API. The root cause is a *base-path* bug, not a denylist bug: `SafeRelPath` is correct, but it is handed a `root` that was built from an unsanitized route parameter.

---

### [S0] Arbitrary file read as any authenticated user (incl. `Viewer`) — skill `:name` is the traversal base

- **File:** `internal/skillpackage/layout.go:11` (the defect) → `internal/skillpackage/io.go:88-108` (the sink) → `internal/handler/skills.go:181` and `internal/handler/skills.go:269` (the routes)
- **Path construction:**
  ```go
  // layout.go:11 — skillID is the raw gin route param, never sanitized
  func SkillDir(skillsRoot, skillID string) string { return filepath.Join(skillsRoot, skillID) }

  // io.go:88 — SafeRelPath is CORRECT, but its root is already hostile
  func ReadPackageFile(skillsRoot, skillID, relPath string, maxBytes int64) ([]byte, error) {
      root := SkillDir(skillsRoot, skillID)   // <-- attacker controls the base
      abs, err := SafeRelPath(root, relPath)   // correctly confines rel INSIDE the (hostile) root
      ...
      return os.ReadFile(abs)
  }
  ```
  `SafeRelPath` (`io.go:19-37`) is genuinely sound: `filepath.ToSlash` normalizes `\`→`/` so `..\` is caught, `strings.Contains(rel, "..")` blocks the segment, the leading `/` is trimmed before joining (so `filepath.Join(base,"/etc/passwd")` is *not* an escape), and a final `filepath.Rel` re-asserts containment. **The bug is that the base is attacker-controlled.** Note also that `ReadPackageFile` — unlike `WritePackageFile` (`io.go:113`), `ListPackageFiles` (`io.go:42`) and `LoadSkill` — has **no `ResolveSKILLPath` guard**, so the escaped base is not even required to be a real skill directory.
- **Escape sequence:** `%5C` decodes to `\`, which `filepath.Clean` treats as a separator on Windows. `%2F` does **not** work (gin won't route a decoded `/` into a single param segment), so the Windows backslash form is the payload.
- **Verified empirically** (not inferred):
  - gin 1.9.1 (the pinned version), no `RemoveExtraSlash`/`CleanPath`/`RedirectFixedPath` middleware anywhere in the stack:
    ```
    GET /api/skills/..%5C..%5C..%5C..%5C..%5C/file  => 200 {"name":"..\\..\\..\\..\\..\\"}
    GET /api/skills/..%5c..%5c..%5c..%5c..%5c/file  => 200 {"name":"..\\..\\..\\..\\..\\"}
    GET /api/skills/..%2F..%2F..%2F..%2F..%2F/file  => 404   (slash form blocked by routing)
    ```
  - the resulting join and a full `SafeRelPath` round-trip against the escaped base:
    ```
    SkillDir("C:\...\jysecai\skills", "..\..\..\..\..\") => "C:\"
    rel=Users/Administrator/.ssh/id_rsa => "C:\Users\Administrator\.ssh\id_rsa"  err=<nil>
    rel=Windows/win.ini               => "C:\Windows\win.ini"                    err=<nil>
    ```
- **Reachability:** `GET /api/skills/:name/file?path=` (app.go:1427) and `GET /api/skills/:name?resource_path=` (app.go:1434, via `ReadScriptText` → `ReadPackageFile` at service.go:150). Permission `skills:read`. In `internal/database/rbac.go:395-400` every key matching `strings.HasSuffix(key, ":read")` is granted to **Operator, Auditor and Viewer**, and `resourceAllowed` returns true for GET. **No admin role, no scope=`all`, no approval gate.**
- **Concrete payload** (deploy root `C:\Users\Administrator\desktop\jysecai`, skills root `...\jysecai\skills`):
  ```
  GET /api/skills/..%5C..%5C..%5C..%5C..%5C?resource_path=Windows/win.ini
  GET /api/skills/..%5C..%5C..%5C..%5C..%5C%5CUsers%5CAdministrator%5C.ssh%5Cid_rsa/file?path=x
  GET /api/skills/%2e%2e%5c%2e%2e%5c%2e%2e%5c%2e%2e%5c%2e%2e%5c%2e%2e%5c%2e%2e/file?path=config.yaml
  ```
  On Linux the same class works with `%2F` only if the route is reached before decoding; on Windows the backslash form is definitive. Response body is `{"path":..., "content":"<raw bytes>"}`, capped at 10 MiB (`defaultMaxRead`). High-value targets in this repo: `config.yaml` (105 lines match `api_key|encryption_key|implant_token|password|secret|token`), `.env`, the SQLite DB, SSH keys.
- **Suggested fix:** validate `:name` with the existing `isValidSkillName` (`skills.go:700-710`, restricts to `[a-z0-9-]{1,100}`) at every handler — `GetSkill`, `GetSkillPackageFile`, `PutSkillPackageFile`, `ListSkillPackageFiles`, `UpdateSkill`, `DeleteSkill` — **and** add a `ResolveSKILLPath(root)` guard inside `ReadPackageFile` so the read path matches the write/list paths. Defence in depth: assert `filepath.Rel(skillsRoot, root)` contains no `..`.

---

### [S1] Recursive arbitrary-directory delete via `DELETE /api/skills/:name`

- **File:** `internal/handler/skills.go:462-463`
- **Path construction:** `skillName := c.Param("name")` (`:448`, only checked for `!= ""`) → `skillDir := filepath.Join(h.skillsRootAbs(), skillName)` (`:462`) → `os.RemoveAll(skillDir)` (`:463`). **No `ResolveSKILLPath` guard, no `isValidSkillName`, no `SafeRelPath`** — the least-guarded sink in the file.
- **Escape sequence:** identical `%5C` decoding as the S0. `DELETE /api/skills/..%5C..%5Cdata` → `C:\Users\Administrator\desktop\jysecai\data`.
- **Reachability:** `DELETE /api/skills/:name` (app.go:1432) → `skills:delete`, which rbac.go:389-394 explicitly *excludes* from the operator/auditor/viewer grant, and `/skills` is a process-global-mutation path so `Scope == all` is additionally required → **admin only**.
- **Concrete payload:**
  ```
  DELETE /api/skills/..%5C..%5C
  DELETE /api/skills/..%5C..%5C..%5CUsers%5CPublic
  ```
  `os.RemoveAll` returns `nil` for a non-existent path, so the endpoint answers **HTTP 200 even when nothing was deleted** — silent and easy to miss in testing.
- **Calibration:** admin already holds `terminal:execute` (arbitrary command execution on this host, rbac.go:375), so this is not a privilege *gain* in the default role model. It matters for (a) custom roles, (b) blast-radius/safety review, (c) defence in depth.
- **Suggested fix:** `isValidSkillName(skillName)` before the join; resolve via `ResolveSKILLPath` so only a real skill dir can be removed.

---

### [S1] Arbitrary file write + directory creation via knowledge-base item create/update

- **File:** `internal/knowledge/manager.go:603-611` (`CreateItem`), `internal/knowledge/manager.go:644-671` (`UpdateItem`), `internal/knowledge/manager.go:703` (`DeleteItem`)
- **Path construction:**
  ```go
  // manager.go:603 — `category` and `title` are raw JSON body fields
  filePath := filepath.Join(m.basePath, category, title+".md")
  os.MkdirAll(filepath.Dir(filePath), 0755)
  os.WriteFile(filePath, []byte(content), 0644)
  ```
  `internal/handler/knowledge.go:242-252` binds `{"category","title","content"}` and passes them straight through — **no `..` rejection, no separator rejection, no drive-letter rejection, no ADS rejection anywhere in the chain.** `filepath.Join` *does* escape on `..`.
- **Escape sequence:** `{"category":"..\\..\\..\\..\\tmp\\pwn","title":"x"}` → `<knowledge_root>/../../../tmp/pwn/x.md`.
- **Reachability:** `POST /api/knowledge/items` (app.go:1160), `PUT /api/knowledge/items/:id` (app.go:1170) → `knowledge:write` (rbac.go:391, admin-only) **and** `Scope == all`. Same admin-already-has-RCE calibration as above.
- **Concrete payload:**
  ```
  POST /api/knowledge/items
  {"category":"..\\..\\..\\..\\..\\Users\\Administrator\\.ssh","title":"authorized_keys","content":"ssh-ed25519 AAAA... attacker\n"}
  ```
  Compounding factor: `UpdateItem` renames and deletes using `item.FilePath` **read back from the database** (`manager.go:654` `os.Rename`, `:663`/`:718` `os.Remove`), so one poisoned row converts `DeleteItem` into an arbitrary unlink as a second-order effect.
- **Suggested fix:** reject `category`/`title` containing `/`, `\`, `..`, `:` or a drive letter (allowlist `[^\p{L}\p{N}\-_ ]` is simplest), and assert `ensurePathInDir(m.basePath, filePath)` — the helper already exists at `internal/poc/poc.go:97-106`.

---

### [S1] Skill `SKILL.md` overwrite through unsanitized `:name`

- **File:** `internal/handler/skills.go:405-406` (read) → `internal/handler/skills.go:429-431` (write), in `UpdateSkill`
- **Path construction:** `mdPath := filepath.Join(h.skillsRootAbs(), skillName, "SKILL.md")` (`:405`) → `os.ReadFile` (`:406`) → must parse via `ParseSkillMD` (`:411`) → `skillDir := filepath.Join(h.skillsRootAbs(), skillName)` (`:429`) → `os.WriteFile(filepath.Join(skillDir, "SKILL.md"), skillMD, 0644)` (`:431`). Contrast `CreateSkill` at `:337`, which correctly calls `isValidSkillName`.
- **Escape sequence:** `PUT /api/skills/..%5C<other-skill>` with a body overwrites a sibling skill directory's `SKILL.md` with attacker content. Impact is **agent-instruction / tool-allowlist injection** — the file is read by the LLM agent as policy.
- **Constraining factors:** the target must already contain a `SKILL.md` that parses, and `os.WriteFile` creates no parent directories, so escaping `skills/` entirely requires a foreign directory that happens to hold a valid `SKILL.md`.
- **Reachability:** `PUT /api/skills/:name` (app.go:1431) → `skills:write` → admin only, plus `Scope == all`.
- **Suggested fix:** `isValidSkillName(skillName)` before the first join.

---

### [S2] Skill package write escapes the skills root

- **File:** `internal/skillpackage/io.go:111-124` via `internal/handler/skills.go:294`
- **Path construction:** `root := SkillDir(skillsRoot, skillID)` (unsanitized base) → `ResolveSKILLPath(root)` guard (`:113`) → `SafeRelPath(root, relPath)` (correct) → `os.MkdirAll(filepath.Dir(abs), 0755)` + `os.WriteFile(abs, content, 0644)`.
- **Why S2 not S0:** the `ResolveSKILLPath` guard means the escaped target must be a directory that really contains a `SKILL.md`, so this is confined in practice to sibling skill directories — but `MkdirAll` **can** create new directories, so it is a genuine write primitive one level out.
- **Reachability:** `PUT /api/skills/:name/file` (app.go:1428) → `skills:write`, admin only.
- **Concrete payload:** `PUT /api/skills/..%5C..%5C..%5Ctmp/file {"path":"pwned.txt","content":"..."}` — lands outside the guard only if the resolved base has a `SKILL.md`; otherwise the guard rejects it.
- **Suggested fix:** same as the S0 — validate `skillID` with `isValidSkillName` at the handler, and assert containment of `root` against `skillsRoot` inside `SkillDir` itself so *every* current and future caller is protected.

---

### [S2] Directory listing + existence oracle outside the skills root

- **File:** `internal/skillpackage/io.go:40-45` via `internal/handler/skills.go:253` and `internal/handler/skills.go:212`
- **Path construction:** `ListPackageFiles` / `LoadSkill` pass the unsanitized `skillID` into `SkillDir`, but both call `ResolveSKILLPath` first, so traversal is bounded to directories containing a `SKILL.md`. `filepath.WalkDir` then returns **absolute paths and file sizes** for the whole subtree.
- **Reachability:** `GET /api/skills/:name/files` (app.go:1426), `GET /api/skills/:name` (app.go:1434) → `skills:read` → **granted to Viewer/Auditor/Operator**. Wide reach, low impact — chiefly an existence oracle ("does `<dir>/SKILL.md` exist?") plus filesystem layout disclosure. Also `internal/skillpackage/io.go:141` (`listScripts`) has the same shape.
- **Concrete payload:** `GET /api/skills/..%5C..%5C..%5C/files` — lists only if a `SKILL.md` sits there; the differential response is a directory-existence probe.
- **Suggested fix:** `isValidSkillName` on `:name`; this removes the whole class at once.

---

### [S3] The main `config.yaml` is rewritten at 0644 — the missed secret writer

- **File:** `internal/handler/config.go:2038` (`writeYAMLDocument`), reached from `internal/handler/config.go:1948` and `internal/handler/external_mcp.go:529`
- **Path construction:** `os.WriteFile(path, buf.Bytes(), 0644)`. `path` is `h.configPath` — the **live main config**, which in this deployment holds 105 lines matching `api_key|encryption_key|implant_token|password|secret|token`.
- **Why this is the "missed writer":** first-boot `EnsureLocalConfig` creates the file correctly at **0600** (`internal/config/config.go:1745` `MkdirAll 0700`, `:1749` `WriteFile 0600`), and the `.backup` files were already moved to 0600 (`internal/handler/config.go:1918`, `internal/handler/external_mcp.go:515`). But **every subsequent in-place update goes back through `writeYAMLDocument` at 0644**, so the hard-coded 0600 protection is not the effective state of the file — it is only the creation-time state. `internal/config/config.go:1826` (`persistMCPAuth`, called from `:1843`) likewise writes an MCP `auth_header_value` bearer token at 0644.
- **Practical severity nuance (important, and it cuts both ways):** Go's `os.WriteFile`/`OpenFile` applies `perm` **only when the file is created**. For an existing `config.yaml` the mode is preserved, so in the steady state the 0600 from first boot survives. The exposure is therefore conditional: any code path that creates `config.yaml` fresh through these writers (e.g. `external_mcp.go:529` before `EnsureLocalConfig` has run, or a fresh `data/` directory) lands it at 0644.
- **Real-world corroboration:** the ACL on the deployed `config.yaml` on this host is already wider than 0600 — `WIN-75K4OEGESJ5\CodexSandboxUsers` and three additional SIDs hold **Modify**. On Windows the `0644` constant also does not map cleanly, so the effective protection depends on inherited directory ACLs rather than on the code.
- **Suggested fix:** change `writeYAMLDocument` to `0600` (and `persistMCPAuth` likewise), or `os.Chmod` after write; set the parent directory to `0700`. Tool-guard/tool YAML files at `:1980` can stay `0644` — they hold no secrets.

---

### [S3] C2 evidence, artifact and victim-data directories are world-readable

The brief explicitly asked for the `internal/c2` permission posture. Victim data — screenshots, exfiltrated documents, implant uploads, download results — is written `0644` into `0755` directories:

| Location | Call | Mode |
|---|---|---|
| `internal/c2/manager.go:807` | `osMkdirAll(dir, 0o755)` (`<storage>/results`) | 0755 |
| `internal/c2/manager.go:821` | `osWriteFileAtomic(path, data, 0o644)` | **0644** |
| `internal/c2/listener_http.go:359` | `os.MkdirAll(dir, 0o755)` (`<storage>/uploads`) | 0755 |
| `internal/c2/listener_http.go:367` | `osWriteFileAtomic(dst, plaintext, 0o644)` | **0644** |
| `internal/c2/tcp_beacon_server.go:216` | `os.MkdirAll(dir, 0o755)` | 0755 |
| `internal/c2/tcp_beacon_server.go:222` | `osWriteFileAtomic(dst, plainFile, 0o644)` | **0644** |
| `internal/handler/c2.go:1249` | `os.MkdirAll(path, 0o755)` | 0755 |
| `internal/c2/payload_builder.go:175,214` | `os.MkdirAll(..., 0755)` | 0755 |
| `internal/c2/payload_builder.go:198` | `os.WriteFile(..., 0644)` | 0644 |

Any unprivileged local user on a shared host can read post-exploitation data. **Suggested fix:** `0700` directories, `0600` files.

---

### [S3] POC drafts written group-readable while containing evidence PII

- **File:** `internal/poc/poc.go:60` (`MkdirAll 0o750`), `internal/poc/poc.go:71` (`atomicWriteFile(..., 0o640)`)
- The path is **safe** (see verified-safe list), but the mode is `0640` = **group-readable**. The markdown embeds `v.Evidence` verbatim (`poc.go:232-236`) plus up to 10 `ProjectFact` bodies (`:237-248`) — and this repo's own `evidence/` tree holds substantial student PII and phishing lists.
- **Reachability:** `POST /api/vulnerabilities/:id/generate-poc` (app.go:1277) and `/batch-generate-poc` (app.go:1287) → `vulnerability:write`, which falls to the `default:` branch (rbac.go:406-410) and is therefore granted to **Operator/Auditor/Viewer**; the resource check is per-vulnerability ownership. So any authenticated user can produce a group-readable PII dump for vulns they own.
- **Suggested fix:** `0700`/`0600`. `0o750` for the directory is already the right call — the file mode is the inconsistency.

---

### [S3] Artifact / workspace / checkpoint directories are 0755 around correctly-0600 files

The **files** are consistently `0600` (`checkpoint_store.go:65`, `spill.go:63`, `spill.go:259`, `eino_checkpoint.go:64`, `eino_summarize.go:680`, `latest_user_message.go:160`) — good. The **parent directories** are `0755`, so any local user can enumerate filenames and stat sizes (conversation IDs, execution IDs, tool-call IDs), and can reach the files if the leaf mode is ever loosened:

`internal/project/workspace.go:48` · `internal/workflow/checkpoint_store.go:23` · `internal/tooloutput/spill.go:56,251` · `internal/multiagent/eino_summarize.go:158,677` · `internal/multiagent/eino_agentic_summarize.go:103` · `internal/multiagent/latest_user_message.go:155` · `internal/multiagent/eino_checkpoint.go:24` · `internal/multiagent/eino_middleware.go:127,164,266,357` · `internal/database/database.go:156` (SQLite dir!) · `internal/handler/agent.go:540,576` · `internal/handler/chat_uploads.go:329,1429,1456`

`internal/database/database.go:156` creating the SQLite directory at `0755` is the most sensitive of these — it holds the full RBAC and conversation database.

### [S3] Other world-readable writers

- `internal/handler/agent.go:618` — chat attachments at `0644`; user-uploaded files routinely carry credentials and PII. Should be `0600`.
- `internal/app/vulnerability_tools.go:781` — triage report at `0644`; contains vulnerability titles and evidence.
- `internal/knowledge/manager.go:41,606,611,649,671` — knowledge corpus (credential/exploit notes) at `0644`/`0755`.
- `internal/handler/role.go:359`, `internal/handler/skills.go:368,431,653` — role/skill YAML at `0644`; low sensitivity (no secrets) but note `role.go:344,360` `continue`s silently on write failure, desyncing disk from memory.
- `internal/handler/markdown_agents.go:233,299` — agent markdown at `0644`; no secrets.

---

### [S3] Absolute server paths leaked to clients via `err.Error()`

`internal/handler/skills.go:181-185, 269-274, 294-299` and `internal/handler/knowledge.go:256, 289, 310, 411, 432, 465` return raw Go errors in the JSON body, embedding full absolute paths — e.g. `open C:\Users\Administrator\desktop\jysecai\config.yaml: The system cannot find the file specified.` This both discloses deployment layout and turns the S0 above into a reliable filesystem **enumeration** oracle (differentiate "not found" from "permission denied" from "is a directory").

**Suggested fix:** return the `PackageError` code (the `workflow/package` pattern at `inspector.go:22-39` already does this correctly) rather than `err.Error()`.

---

### [S3] Latent: `os.Remove` with zero path validation on a HITL-exempt, model-callable path

- **File:** `internal/multiagent/plantask_local_backend.go:70`
  ```go
  func (l *localPlantaskBackend) Delete(ctx, req *plantask.DeleteRequest) error {
      p := strings.TrimSpace(req.FilePath)   // raw: no Clean, no Rel check, no base-dir check
      if p == "" { return nil }
      return os.Remove(p)                    // <-- no validation whatsoever
  }
  ```
  This is the only unvalidated path sink in the file — every sibling method re-derives or cleans its path (`LsInfo` at `:45,53-57` does call `filepath.Clean`/`IsAbs`).
- **Why S3 and not S0 today:** the upstream builder is `filepath.Join(t.BaseDir, taskID + ".json")`, and `isValidTaskID` is the anchored regex `^\d+$`, so `taskID` cannot contain `/`, `\`, or `..`. The traversal is not live.
- **Why it still matters:** `TaskUpdate` is a **model-callable LLM tool** and is explicitly **HITL-exempt** (`HitlExemptMetaTools`), requiring only `agent:execute` — which lands in the `default:` branch (rbac.go:406-410) and is therefore granted to **Operator, Auditor and Viewer**. The only thing standing between a low-privilege user and an arbitrary unlink is a regex in a third-party module. Any upstream relaxation of `validTaskIDRegex`, any second `DeleteRequest` construction site, or any new caller converts this to S0.
- **Suggested fix:** add the `ensurePathInDir`-style `filepath.Rel` assertion that `internal/poc/poc.go:97-106` already demonstrates in this codebase.

---

## Verified SAFE (and why)

These were examined and are **not** findings. Recorded so the next reviewer does not re-tread them.

| Component | Why it is safe |
|---|---|
| `internal/skillpackage/io.go:19-37` `SafeRelPath` | Correct denylist+prefix design. `ToSlash` normalizes `\`→`/` so `..\` is caught; `Contains(rel,"..")` blocks the segment; leading `/` is trimmed before the join so `Join(base,"/etc/passwd")` does **not** escape; a final `filepath.Rel` re-asserts containment and catches volume mismatch. Verified that `C:\foo` and `\\?\C:\foo` cannot escape `filepath.Join`. **Only defect is callers passing a hostile `root`** (the S0). |
| `internal/handler/chat_uploads.go` — `resolveUnderChatUploads` (:233), `resolveReductionVirtualPath` (:671), `resolveWorkspaceVirtualPath` (:692), `resolveConversationArtifactVirtualPath` (:713) | All four follow the same correct pattern: `filepath.Clean` → reject `.`/`..` prefix → `filepath.Join` → `filepath.Abs` → re-assert `HasPrefix(full, rootAbs+Separator)`. `Mkdir` (:1212) and `Rename` (:1291) additionally reject any `/` or `\` in the name. `Upload` sanitizes via `filepath.Base(fh.Filename)` and appends a timestamp + 6 hex chars. |
| `internal/handler/agent.go:451-481` `validateChatAttachmentServerPath` | `Clean` → `Abs` → prefix assert → `!IsDir()`. Correct, and its root matches `chat_uploads.go:absRoot()` exactly. Two hardening gaps, **not findings** (both require a pre-existing filesystem foothold): no `filepath.EvalSymlinks` on the candidate, and an NTFS ADS (`…\chat_uploads\x.txt:stream`) passes the prefix check and `os.Stat`. |
| `internal/poc/poc.go` — output paths | `outputDir` is server-chosen (`app.go:409`). `filenameSlug` applies the allowlist regex `[^\p{L}\p{N}\-_]+` to the ID and title — a *stronger* guarantee than a denylist. Verified: `filenameSlug("../../etc/passwd")` → `"etc-passwd"`; `filenameSlug("..")` → `"fallback"`. `ensurePathInDir` (`:97-106`) adds `filepath.Rel` containment. `atomicWriteFile` uses `os.CreateTemp(dir, ".poc-draft-*")` — unpredictable name — then `Chmod(0o640)`. Only the mode is a finding (S3). |
| `internal/project/workspace.go:10-23` `sanitizeWorkspacePathSegment` | Replaces `/`, `\`, `Separator` with `-` and `..` with `__`. Verified against 17 payloads incl. `C:\Windows\win.ini`, `\\?\C:\Windows`, `....//....//etc` — containment held in every case. Verified `filepath.Join("C:\data","C:/x")` does **not** reset the volume, so a surviving `C:` is inert. |
| `internal/tooloutput/spill.go:191-204` `sanitizeSegment` | Byte-identical logic; applied to every segment of `SessionRoot` (`:31-44`) and both `id` derivations (`:54,249`). `ExecutionID` is a server UUID, never user input. Files `0600` (`WriteTruncFile` `:63`, `Tee` `:259`). |
| `internal/workflow/checkpoint_store.go` | `dir` is the constant `data/workflow-checkpoints` (`engine.go:29`), overridable only by `SetCheckpointDir`, whose only callers are `_test.go`. The id is a server `uuid.NewString()` (`runner.go:53`); the resume path DB-validates it first (`workflow_run.go:139-144`). Guard at `:34` blocks `..` and both separators. `0600` + atomic rename. |
| `internal/vulnquality/report.go` | Not reachable by any web user — standalone CLI via `os.Args`; zero HTTP references. `ValidateCopyPath` (`:156-183`) is the strongest validator found: `Abs` → inside-tmp → `EvalSymlinks` → inside-tmp again (catches symlink escape) → `Stat` + `IsRegular()` (rejects devices/FIFOs). `ValidateOutputPath` (`:293-309`) uses `os.SameFile` to block DB overwrite via hardlink. Read-only via `file:…?mode=ro` DSN (`:142`). |
| `internal/c2` containment — `uploadPathForTask` (`manager.go:822-833`), `ensurePathInDir` (`manager.go:851+`) | `uploadTaskIDPattern = ^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$` plus `ensurePathInDir` (`filepath.Rel` + `IsAbs` + `Lstat` symlink rejection on both container and destination). Covered by `manager_blob_test.go`. `osWriteFileAtomic` (`io.go:17-41`) writes a temp sibling and `os.Rename`s, so it never follows a pre-planted destination symlink. |
| `internal/c2` download/serving — `listener_http.go:385-403`, `tcp_beacon_server.go:238-250`, `handler/c2.go:900,1231` | `taskID` rejects `/`, `\`, `..`; then `Abs` + prefix re-verify. Uploads require AES-GCM decrypt **and** a constant-time `X-Implant-Token` compare **and** a 256 MiB `MaxBytesReader`. `PayloadDownload` validates the `beacon_` prefix and runs an ownership ACL; `DownloadResultFile` serves only the DB-stored `ResultBlobPath` — no request-supplied path component. |
| `internal/workflow/package/inspector.go` — the only zip parser | `safeArchivePath` (`:152-154`) rejects `\`, leading `/`, `path.Clean` mismatch, `../` and bare `..`. `InspectArchive` also rejects symlink entries (`:71`), duplicate names (`:74`), and enforces both a 10 MiB compressed and 20 MiB **cumulative** extracted cap with `io.LimitReader` (`:77-88`). It is **memory-only — nothing is ever extracted to disk**, so classic zip-slip does not apply. `safePackageWorkflowID` (`:161`) rejects any ID containing `/\`. |
| `internal/handler/webshell.go` | **No local file sinks.** Every path in `buildFileCommand` (`:229-341`) is interpolated into a shell string shipped over HTTP to the **target webshell** and executed there — unconfinement is the intended feature and runs on the victim, not this server. The only local op is `os.ReadFile(os.Getenv("JYSSECAI_WEBSHELL_CA_FILE"))` (`:476`), process env only. |
| `internal/handler/markdown_agents.go:36-46` `safeJoin` | Regex `^[a-zA-Z0-9][a-zA-Z0-9_.-]*\.md$` plus `Clean(filename) != filename` plus `Contains(clean,"..")`. No `/`, `\` or `:` can survive. Mutations need `agents:write` + `Scope==all`. |
| `internal/handler/role.go:372-403` `sanitizeFileName` | Replaces `/ \ : * ? " < > |` and space. It does not strip `..`, but all separators are neutralized, so `..` becomes a literal filename; colon is replaced so no ADS. `roles:write`/`roles:delete` are admin-only. |
| `internal/handler/tool_guard.go:131-180` `saveToolGuardConfig` | Path is `filepath.EvalSymlinks(h.configPath)` — fully server-chosen. `os.CreateTemp(dir, ".tool-guard-*.yaml")` with no user input in dir or pattern. **`tmp.Chmod(info.Mode().Perm())` preserves the original mode** rather than downgrading, then atomic rename. Correct. |
| `internal/handler/terminal.go:122-136, 243-257` | `req.Cwd` → `Abs` → `Rel(curAbs, absCwd)`, rejecting `err != nil`, `rel == ".."`, `HasPrefix(rel,"..")`. Confines `cmd.Dir` to the process CWD subtree. `terminal:execute` is admin-only. |
| `internal/handler/audit_export_csv.go` | No filesystem path at all — streams via `csv.NewWriter(c.Writer)`. `Content-Disposition` name is server-generated (`audit-logs-<date>.csv`). `escapeCSVCell` (`:20-30`) neutralizes `= + - @ \t \r` on attacker-influenced columns (CSV-injection defence). |
| `internal/handler/openapi.go` | 6380-line static spec map. Zero matches for any file sink. |
| `internal/handler/vulnerability.go` | Zero `os.`/`filepath.` calls. `ExportVulnerabilities` returns JSON; `sanitizeExportName` builds a *client-side* filename only. |
| `internal/app/vulnerability_tools.go:776-781` | Path is 100% server-generated: `filepath.Join(root,"reports", fmt.Sprintf("vulnerability-triage-report-%s.md", time.Now()…))`. |
| `internal/agents/markdown.go` | No user input reaches any path. `collectMarkdownBasenames` (`:288-325`) derives every name from `os.ReadDir`, filters `.md`, skips dotfiles. `SlugID` (`:178`) and `sanitizeEinoAgentID` (`:202`) emit only `[a-z0-9-]`. |
| `internal/multiagent/eino_skills.go:80-83` | Uses the third-party `skill.NewBackendFromFilesystem`; its `Get(name)` globs `*/SKILL.md` and does an **exact string match** on front matter — the LLM-controlled name never reaches `filepath.Join`. |
| `internal/multiagent/eino_middleware.go:32-45` `sanitizeEinoPathSegment` + `reductionCacheRootDir` (`:107-120`) | Replaces `os.Separator`, `/`, `\`, then `..`→`__`, caps length, empty→`default`. The `plantask` `rel` (`:261-265, :352-356`) is `cfg…PlantaskRelDir` — admin config, not user input. |
| `internal/multiagent/eino_checkpoint.go:35-40` | `path()` rejects any id containing `/` or `\`; `id+".ckpt"` can never be the `..` element. The id is server-generated. `Set` uses `0o600`. |
| Config base-directory redirection | Every sink base (`workspace_root_dir`, `reduction_root_dir`, `checkpoint_dir`, `plantask_rel_dir`, `skills_dir`, `poc_drafts`) is correctly **absent** from `AgentConfigUpdate` (`config.go:888-897`) and `MultiAgentAPIUpdate` (`config.go:668-684`), so `PUT /api/config` (which requires `config:write`, excluded from Operator at rbac.go:375) cannot be used to redirect any of these sinks. This control holds. |
| Temp-file creation audit | `os.CreateTemp` appears in `internal/poc/poc.go` (`.poc-draft-*`), `internal/handler/tool_guard.go` (`.tool-guard-*.yaml`), and the tool-output/atomic-write helpers. All use fixed server-side patterns with no user input in the directory or pattern, and all `Chmod` to `0600`. **No predictable-temp-file or world-readable-temp-file findings.** |
| Symlink audit | Beyond the already-fixed `internal/agent/agent.go`, no production code calls `os.Symlink`. The one place a planted symlink could matter — `internal/handler/agent.go:451-481` writing under `chat_uploads` — has correct containment; it does not `EvalSymlinks`, which is a hardening note, not a finding, since it needs a pre-existing filesystem foothold. |

---

## Windows-specific notes

- **`%5C` is the traversal character, `%2F` is not.** Verified: gin 1.9.1 routes `%5C` into `:name` as a literal `\` (HTTP 200) but 404s on `%2F`. Any future "fix" that only filters `/` is a no-op on this platform.
- **`filepath.Join(base, "C:\foo")` does NOT escape** — it yields `C:\base\C:\foo`, an invalid nested path. Verified. The `..`-based escape is the only lever here.
- **`filepath.Join(base, "/etc/passwd")` does NOT escape** (leading `/` is cleaned to `base/etc/passwd`). Verified.
- **NTFS ADS** (`file.txt:stream`) survives a `HasPrefix(path, root+sep)` check because it addresses a *stream on a file inside the root*, not a different root. It is not an escape vector for these handlers. Two places accept ADS names without a colon check — `internal/handler/agent.go:451-481` (needs a foothold) and the role/skill filename sanitizers, both of which strip `:` or are constrained by the `SafeRelPath` `..` check.
- **`\\?\` prefixes** were tested against `sanitizeWorkspacePathSegment`, `SafeRelPath`, and the `..` prefix check. All neutralized.
- **Go's `os.WriteFile` perm only applies at creation.** This materially changes the severity of every `0644` in this report — see the config.yaml finding for the worked example.

---

## Suggested remediation order

1. **`internal/skillpackage/layout.go:11`** — make `SkillDir` itself refuse to return a path outside `skillsRoot` (`filepath.Rel` + `..` check). One change closes the S0, the S2s, and every future caller of this function, instead of patching six handlers individually.
2. **`internal/handler/skills.go`** — apply the existing `isValidSkillName` (`:700-710`) to `:name` in all six handlers. This is a five-line change per handler and the pattern is already in the file.
3. **`internal/knowledge/manager.go:603,644`** — validate `category`/`title`; reuse `ensurePathInDir` from `internal/poc/poc.go:97-106`.
4. **`internal/handler/config.go:2038`** — 0600; and `internal/config/config.go:1826` likewise.
5. **Permissions sweep** — `0700`/`0600` for `internal/c2` storage, `internal/database/database.go:156` (SQLite dir), `internal/poc/poc.go:71`, `internal/handler/agent.go:618`.
6. **Stop returning `err.Error()`** in `skills.go` / `knowledge.go` JSON responses; use the `PackageError` code pattern.
7. **`internal/multiagent/plantask_local_backend.go:70`** — add the containment assertion before the `^\d+$` upstream guard is ever needed.
