更新时间: 2026-09-01T03:19:06Z

下次失效（只对 A / HS256）:
  1. 读 JWT_PASSWORD 文件或 /config
  2. 新 iat/exp + 同一 claims 重签
  3. 原子写入 /root/erpc/data/tokens.json
  4. append 一行到 tokens.jsonl

正式站 B 不要走这条。
