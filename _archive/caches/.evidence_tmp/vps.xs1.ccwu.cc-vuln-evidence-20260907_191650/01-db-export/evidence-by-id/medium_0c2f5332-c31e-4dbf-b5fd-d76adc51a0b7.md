# 新北災訊E點通 生产环境暴露 Swagger API 文档（含后台管理接口清单）

- ID: `0c2f5332-c31e-4dbf-b5fd-d76adc51a0b7`
- Severity: **medium**
- Status: open
- Type: 敏感信息泄露
- Target: `https://e1.ntpc.gov.tw/swagger-ui.html + /v2/api-docs?group=v3.0`
- Conversation: `80d7d5eb-ea76-4288-bfcf-c45dee0eace1`
- Created: 2026-09-04 16:45:21.472566082+08:00

## Description

生产环境暴露 Springfox Swagger UI (v2.9.2) 及完整 API 文档。/swagger-resources 返回 [{"name":"v3.0","url":"/v2/api-docs?group=v3.0"}]，获取的 api-docs 暴露全部接口，包括 /v3/api/backstage/account/list（后台账号列表）、/v3/api/backstage/user/edit（用户编辑）、/v3/api/backstage/analysis/*（运营分析）、/v3/api/getFile/{path1}/{path2}/{name}（文件下载）等敏感管理接口路径与参数结构，为攻击者提供完整攻击面地图。

## Preconditions

无，互联网直接访问

## Reproduction

1. curl https://e1.ntpc.gov.tw/swagger-resources 2. curl 'https://e1.ntpc.gov.tw/v2/api-docs?group=v3.0' 3. 浏览器打开 https://e1.ntpc.gov.tw/swagger-ui.html

## Evidence

GET https://e1.ntpc.gov.tw/swagger-resources → 200 [{"name":"v3.0","url":"/v2/api-docs?group=v3.0","swaggerVersion":"2.0"}]
GET https://e1.ntpc.gov.tw/swagger-ui.html → 200 Springfox Swagger UI v2.9.2
GET https://e1.ntpc.gov.tw/v2/api-docs?group=v3.0 → 200 完整 OpenAPI 文档（info.title=NewTaipeiDisasterInfo），含 100+ 接口含 backstage 管理接口。

## Impact

攻击者可枚举全部内部 API（含后台账号管理、用户密码修改、公告审核、文件下载），极大降低后续攻击（鉴权绕过、IDOR、注入）成本。属于敏感信息泄露。

## Recommendation

生产环境禁用 Swagger（springfox.documentation.enabled=false 或 profile 限制），或对 /swagger-ui.html、/v2/api-docs、/swagger-resources 加 IP 白名单/认证。
