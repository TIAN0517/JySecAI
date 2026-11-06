#!/usr/bin/env bash
# =============================================================================
# 外部 MCP (stdio) initialize: EOF 診斷
# -----------------------------------------------------------------------------
# 為什麼要「重現」而不是只看日誌：
#   `initialize: EOF` 代表子行程有被啟動，但在我們送出 initialize 之前就把
#   stdin/stdout 關掉並結束了。Go 端只拿到 EOF，看不到原因。
#   本腳本用「跟 internal/mcp/client_sdk.go 完全相同的方式」再跑一次，
#   就能直接看到那支 Python 印到 stderr 的真實錯誤。
#
# 環境變數白名單複製自 client_sdk.go:458-467 的 envMapToSlice，
# 目的是還原 inherit_parent_env 為 false 時子行程實際看到的環境。
#
# 只讀：不下載、不安裝、不修改設定、不對任何外部目標發請求。
# 用法：
#   sudo bash diag-external-mcp.sh
#   bash diag-external-mcp.sh /path/to/other/config.yaml
# =============================================================================
set -uo pipefail

CFG=${1:-/var/lib/jysecai/core/config.yaml}
WORKDIR=$(systemctl show jysec-core -p WorkingDirectory --value 2>/dev/null)
[ -d "$WORKDIR" ] || WORKDIR=/opt/jysecai/core/current
[ -d "$WORKDIR" ] || WORKDIR=$(pwd)

echo "設定檔：$CFG"
echo "工作目錄：$WORKDIR"
if [ ! -r "$CFG" ]; then
  echo
  echo "⚠ 讀不到設定檔。生機請用：sudo bash diag-external-mcp.sh"
  exit 1
fi

echo
echo "############################################################"
echo "# 1. 設定檔中的 external_mcp 相關行（敏感值已遮蔽）"
echo "############################################################"
python3 - "$CFG" <<'PY'
import re, sys
try:
    raw = open(sys.argv[1], encoding='utf-8', errors='replace').read()
except Exception as e:
    print("讀不到設定檔：", e); raise SystemExit(1)
secret = re.compile(r'(?i)(token|secret|password|api[_-]?key|authorization)')
keep = re.compile(r'(?i)external_?mcp|^\s{0,8}(servers|command|args|type|env|'
                  r'working_directory|inherit_parent_env|timeout|enabled|'
                  r'external_mcp_enable|description)\s*:|^\s{0,10}-\s+\S+')
n = 0
for i, l in enumerate(raw.splitlines(), 1):
    if keep.search(l):
        print(f"{i:5d}: {secret.sub(lambda m: m.group(0).split(':')[0] + ': <REDACTED>', l)}")
        n += 1
        if n >= 160:
            print("      ...（截斷）"); break
if not n:
    print("(設定檔中找不到 external_mcp 相關內容)")
PY

echo
echo "############################################################"
echo "# 2. 解析出每個伺服器的 command / args / cwd / env"
echo "############################################################"
python3 - "$CFG" > /tmp/mcp_specs.tsv <<'PY'
import re, sys
try:
    import yaml
except ImportError:
    print("# 需要 PyYAML：apt install -y python3-yaml", file=sys.stderr)
    raise SystemExit(2)
try:
    cfg = yaml.safe_load(open(sys.argv[1], encoding='utf-8', errors='replace')) or {}
except Exception as e:
    print(f"# YAML 解析失敗：{e}", file=sys.stderr); raise SystemExit(2)

def find_mcp(node, path=""):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else str(k)
            if re.match(r'(?i)external_?mcp', str(k)) and isinstance(v, dict):
                out.append((p, v))
            out.extend(find_mcp(v, p))
    return out

found = find_mcp(cfg)
if not found:
    print("# 找不到 external_mcp 區塊", file=sys.stderr); raise SystemExit(3)

SEP = "\x1f"   # args 內部各參數之間
FLD = "\x1e"   # 欄位之間（必須與 SEP 不同，否則多參數的 args 會把欄位打散）

def cell(v):
    s = "" if v is None else str(v)
    return s if s else "@@EMPTY@@"

for path, node in found:
    servers = node.get("servers") if isinstance(node.get("servers"), dict) else None
    if servers is None:
        servers = {k: v for k, v in node.items()
                   if isinstance(v, dict) and (v.get("command") or v.get("url"))}
    for name, s in servers.items():
        t = (s.get("type") or ("sse" if s.get("url") else "stdio")).lower()
        args = s.get("args") or []
        if isinstance(args, str):
            args = args.split()
        env = s.get("env") or {}
        envk = ",".join(sorted(env.keys())) if isinstance(env, dict) else str(env)
        print(FLD.join([
            cell(name), cell(t), cell(s.get("command")),
            cell(SEP.join(str(a) for a in args)),
            cell(s.get("working_directory") or s.get("working_dir")),
            cell(s.get("inherit_parent_env")),
            cell(envk),
        ]))
PY

if [ ! -s /tmp/mcp_specs.tsv ]; then
  echo "  （解析失敗或沒有任何伺服器，請確認有裝 python3-yaml）"
  exit 1
fi

while IFS=$'\x1e' read -r name typ cmd argstr cwd inherit envkeys; do
  [ "$name" = "@@EMPTY@@" ] && continue
  echo "  ── $name"
  echo "     type=$typ   cwd=${cwd/#@@EMPTY@@/(未設定)}   inherit_parent_env=${inherit/#@@EMPTY@@/(未設定)}   env=${envkeys/#@@EMPTY@@/(無)}"
  echo "     command: $cmd"
  echo "     args   : ${argstr/#@@EMPTY@@/(空)}"
done < /tmp/mcp_specs.tsv

echo
echo "############################################################"
echo "# 3. 【頭號假設】args 相對路徑 / args 為空 / working_directory 未設"
echo "#"
echo "#  機制："
echo "#    client_sdk.go:405   cmd.Dir = strings.TrimSpace(cfg.WorkingDirectory)"
echo "#    working_directory 沒設 -> cmd.Dir=\"\" -> 子行程繼承父行程 cwd"
echo "#    父行程 = jysec-core，其 systemd WorkingDirectory 就是上面那個工作目錄"
echo "#    args 若寫成相對路徑 -> 從該工作目錄去找 -> 找不到 -> Python 立刻結束"
echo "#    -> 父行程讀 stdin 得到 EOF，就是 initialize: EOF"
echo "#"
echo "#  args 為空更糟：子行程是裸 python，會把 initialize 的 JSON"
echo "#  當成 Python 程式碼執行 -> SyntaxError -> 立刻結束 -> 同樣是 EOF。"
echo "############################################################"

while IFS=$'\x1e' read -r name typ cmd argstr cwd inherit envkeys; do
  [ "$name" = "@@EMPTY@@" ] && continue
  [ "$typ" = "stdio" ] || continue
  echo
  echo "  ── $name"
  echo "     working_directory = ${cwd/#@@EMPTY@@/(未設定)}"
  if [ "$argstr" = "@@EMPTY@@" ]; then
    echo "     args = （空！）-> 裸 python，會把 initialize 的 JSON 當 Python 跑"
    continue
  fi
  # 逐個參數檢查：跳過 flag（以 - 開頭），只看非絕對路徑
  bad=""
  while IFS= read -r a; do
    [ -z "$a" ] && continue
    case "$a" in
      -*) continue ;;          # flag，不是路徑
      /*) continue ;;          # 絕對路徑，沒問題
    esac
    case "$a" in
      *.py|*/*|*.js) bad="$a"; break ;;
    esac
  done <<< "$(printf '%s' "$argstr" | tr '\x1f' '\n')"

  if [ -z "$bad" ]; then
    echo "     args 內沒有非絕對路徑的參數，相對路徑假設不成立"
  else
    base="${cwd/#@@EMPTY@@/$WORKDIR}"
    echo "     非絕對路徑參數 = $bad"
    if [ -e "$base/$bad" ]; then
      echo "        從 $base 解析：找得到"
    else
      echo "        從 $base 解析：❌ 找不到 ← 這就是 EOF 的原因"
    fi
  fi
done < /tmp/mcp_specs.tsv

echo
echo "############################################################"
echo "# 4. 重現平台行為：相同的 env 白名單啟動，抓 stderr"
echo "#    （白名單複製自 client_sdk.go:458-467）"
echo "############################################################"

build_env() {
  local inherit="$1"
  (
    unset $(env | cut -d= -f1) 2>/dev/null || true
    for k in PATH PATHEXT SYSTEMROOT WINDIR COMSPEC HOME USERPROFILE APPDATA \
             LOCALAPPDATA PROGRAMDATA TMP TEMP LANG LC_ALL \
             XDG_CACHE_HOME XDG_CONFIG_HOME XDG_DATA_HOME \
             NUMBER_OF_PROCESSORS PROCESSOR_ARCHITECTURE; do
      [ -n "${!k:-}" ] && export "$k"
    done
    if [ "$inherit" = "True" ] || [ "$inherit" = "true" ]; then
      echo "  （inherit_parent_env=true，子行程會繼承完整環境）"
    else
      echo "  （inherit_parent_env=${inherit}，子行程只有白名單變數）"
    fi
    exec "$@"
  )
}

while IFS=$'\x1e' read -r name typ cmd argstr cwd inherit envkeys; do
  [ "$name" = "@@EMPTY@@" ] && continue
  echo
  echo "──────── $name（$typ）────────"
  if [ "$typ" != "stdio" ]; then
    echo "  非 stdio，略過（http/sse 走網路，不會是 EOF）"
    continue
  fi
  [ "$cwd" = "@@EMPTY@@" ] && cwd=""
  [ "$argstr" = "@@EMPTY@@" ] && argstr=""
  [ "$envkeys" = "@@EMPTY@@" ] && envkeys=""
  [ "$inherit" = "@@EMPTY@@" ] && inherit="False"

  echo "  command : $cmd"
  echo "  args    : ${argstr:-（空！）}"
  echo "  cwd     : ${cwd:-$WORKDIR}"
  echo "  env keys: ${envkeys:-（無）}"

  echo "  -- command 是否可用"
  if [ -x "$cmd" ]; then
    echo "     存在且可執行"
  else
    echo "     作為路徑找不到：$cmd"
    if rp=$(command -v "$cmd" 2>/dev/null); then
      echo "     但 PATH 可以解析到：$rp"
    else
      echo "     PATH 也解析不到（平台端會在這裡直接失敗，錯誤訊息會是『找不到 MCP 命令』而不是 EOF）"
      continue
    fi
  fi

  vd=$(cd "$(dirname "$cmd")/.." 2>/dev/null && pwd)
  if [ -f "$vd/pyvenv.cfg" ]; then
    echo "  -- pyvenv.cfg（$vd）"
    head -3 "$vd/pyvenv.cfg" | sed 's/^/        /'
  fi

  echo "  -- 原樣啟動，3 秒後收尾"
  ARGS=()
  if [ -n "$argstr" ]; then
    mapfile -d $'\x1f' -t ARGS < <(printf '%s\x1f' "$argstr")
  fi
  out=$( cd "${cwd:-$WORKDIR}" 2>/dev/null && \
         timeout 3 build_env "$inherit" "$cmd" "${ARGS[@]}" 2>&1 </dev/null )
  rc=$?
  if [ -z "$out" ]; then
    echo "     （完全沒有輸出，exit=$rc）"
  else
    printf '%s\n' "$out" | head -25 | sed 's/^/     | /'
  fi
  echo "     exit code: $rc"
  # case 的 pattern 含空格時必須加引號：
  # 未引號的 *No module named* 會被 bash 拆成多個 pattern，整段語法錯誤。
  case "$out" in
    *ModuleNotFoundError*|*"No module named"*)
      echo "     根因：Python 找不到模組 -> 多半是 working_directory 或 PYTHONPATH 沒設" ;;
    *SyntaxError*)
      echo "     根因：Python 語法錯誤 -> args 為空或指向的檔案本身有問題" ;;
    *"No such file"*)
      echo "     根因：檔案不存在 -> args 路徑不對" ;;
    *PermissionError*|*OSError*)
      echo "     根因：檔案權限或路徑問題" ;;
  esac
  if [ "$rc" -eq 124 ]; then
    echo "     3 秒仍在跑 -> 這個啟動方式是正常的（不會 EOF）"
  fi
done < /tmp/mcp_specs.tsv

echo
echo "############################################################"
echo "# 5. 摘要"
echo "############################################################"
python3 - /tmp/mcp_specs.tsv <<'PY'
import sys
rows = [l.rstrip("\n").split("\x1e") for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
rows = [r for r in rows if len(r) >= 7]
stdio = [r for r in rows if r[1] == "stdio"]
rel = noargs = nocwd = 0
for r in stdio:
    name, typ, cmd, args, cwd, inherit, envk = r
    if args == "@@EMPTY@@":
        noargs += 1
    else:
        for a in args.split("\x1f"):
            if a.endswith(".py") and not a.startswith("/"):
                rel += 1
                break
    if cwd == "@@EMPTY@@":
        nocwd += 1
print(f"  伺服器總數 {len(rows)}（其中 stdio {len(stdio)}）")
print(f"  args 為相對路徑的：{rel}")
print(f"  args 為空的：{noargs}")
print(f"  未設 working_directory 的：{nocwd}")
if rel or noargs:
    print("  -> 上述任一成立就足以解釋 initialize: EOF")
else:
    print("  -> 相對路徑假設不成立，請看第 4 節抓到的 stderr")
PY
echo
echo "（本腳本唯讀，未修改任何設定，也未對任何外部目標發請求）"
