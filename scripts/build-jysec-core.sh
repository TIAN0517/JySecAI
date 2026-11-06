#!/usr/bin/env bash
# 建置 jysec-core 並在同一次執行內封存 sha256 sidecar。
#
# 為什麼把 sidecar 綁在這裡
#   2026-10-02 的失效根因不是「忘了驗」，而是「驗的東西跟跑的東西不是同一份」。
#   如果 sidecar 是一個要另外記得執行的步驟，它早晚會再次與建置結果脫節。
#   把它放進同一個指令、且在 build 成功後才寫入，就，杜絕了手動流程出錯的空間。
#
# 用法（在 WSL 內執行，需要 WSL 的 go 與 gcc）
#   bash build-jysec-core.sh                    # 輸出到 build/releases/jysec-core
#   bash build-jysec-core.sh --out /tmp/foo     # 自訂輸出路徑
#   bash build-jysec-core.sh --no-cgo           # 靜態建置（CGO=0，體積較小但功能面可能差異）

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT=""
CGO=1
PKG="./cmd/server"

while [ $# -gt 0 ]; do
  case "$1" in
    --out)    OUT="$2"; shift 2 ;;
    --no-cgo) CGO=0; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "[abort] 未知參數：$1" >&2; exit 2 ;;
  esac
done

[ -n "$OUT" ] || OUT="$ROOT/build/releases/jysec-core"
OUTDIR="$(dirname "$OUT")"
mkdir -p "$OUTDIR"

command -v go >/dev/null 2>&1 || { echo "[abort] 找不到 go，請在 WSL 內執行本腳本" >&2; exit 2; }
if [ "$CGO" -eq 1 ]; then
  command -v gcc >/dev/null 2>&1 || { echo "[abort] CGO=1 需要 gcc；請改用 --no-cgo" >&2; exit 2; }
fi

cd "$ROOT" || { echo "[abort] 找不到專案根目錄：$ROOT" >&2; exit 2; }

printf '== 環境 ==\n'
printf '  go        : %s\n' "$(go version)"
printf '  root      : %s\n' "$ROOT"
printf '  out       : %s\n' "$OUT"
printf '  CGO       : %s\n' "$CGO"
printf '  開始建置（大型專案，可能數分鐘）...\n\n'

TMP="${OUT}.building.$$"
START=$(date +%s)

CGO_ENABLED="$CGO" GOOS=linux GOARCH=amd64 \
  go build -buildvcs=false -trimpath -o "$TMP" "$PKG"
rc=$?

ELAPSED=$(( $(date +%s) - START ))

if [ $rc -ne 0 ] || [ ! -f "$TMP" ]; then
  rm -f "$TMP"
  echo "[abort] 建置失敗（exit $rc），已用掉 ${ELAPSED}s，未產生任何 sidecar" >&2
  exit "$rc"
fi

# 只有建置成功才原子換上，並在同一刻寫出 sidecar
mv -f "$TMP" "$OUT"
HASH="$(sha256sum "$OUT" | awk '{print $1}')"
SIZE="$(wc -c < "$OUT" | tr -d ' ')"
printf '%s  %s\n' "$HASH" "$(basename "$OUT")" > "${OUT}.sha256"

printf '\n== 建置完成（%ss）==\n' "$ELAPSED"
printf '  binary  : %s\n' "$OUT"
printf '  bytes   : %s\n' "$SIZE"
printf '  sha256  : %s\n' "$HASH"
printf '  sidecar : %s\n' "${OUT}.sha256"
cat "${OUT}.sha256"
printf '\n下一步（部署請用 deploy-jysec-core.sh，它會驗 source == sidecar，落地後再驗一次）\n'
