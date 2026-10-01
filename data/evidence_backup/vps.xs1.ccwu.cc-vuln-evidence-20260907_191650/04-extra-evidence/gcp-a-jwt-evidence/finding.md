# EPCR GCP (A) JWT 证据

- 漏洞ID: 5699c19d-4db7-4887-8d70-ca7f062e0305
- 目标: http://35.234.50.28 (GCP)，不是 epcr.tpf.gov.tw
- 算法: HS256 跨服务共享密钥（来源 :3100 socket.io / 各服务 /config）
- 影子账号: admin2（DB id=37 不存在）
- 本包不存放签好的 eyJ。完整 JWT 用本机 jwt 按 claims-template 重签。
- 正式站 B 是 RS256，这把密钥不能拿去签 tpf.gov.tw。
