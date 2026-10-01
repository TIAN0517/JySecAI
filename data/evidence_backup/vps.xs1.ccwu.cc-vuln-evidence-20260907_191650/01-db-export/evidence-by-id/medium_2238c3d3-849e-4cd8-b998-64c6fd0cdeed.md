# 4000-4008 /events 端点矩阵：4000/4002/4003/4004/4005/4007/4008 均 401 "No authorization token was found"；4006 例外 403 "Access denined" 暴露 Express 拼写错误；4004 例外 set-cookie connect.sid 即使 401 也下发 express-sessio

- ID: `2238c3d3-849e-4cd8-b998-64c6fd0cdeed`
- Severity: **medium**
- Status: confirmed
- Type: finding
- Target: `-`
- Conversation: `12ac3036-82f7-4cd7-a0e6-b66dc9d6ad7c`
- Created: 2026-08-29 15:20:05.254213492+08:00

## Description

由项目事实 finding/4000-4008-events-port-matrix 生成

## Evidence

--- retest 2026-08-31 ---
2026-08-31 GET /events：
4000/4002/4003/4005/4007/4008 → 401
4001 → 200
4006 → 403 "Access denined"（拼写错误仍在）
4004 → 401 且 Set-Cookie connect.sid


