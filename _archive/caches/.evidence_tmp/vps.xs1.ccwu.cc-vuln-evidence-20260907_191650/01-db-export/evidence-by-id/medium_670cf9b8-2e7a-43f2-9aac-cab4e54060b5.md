# CSP 泄露内部拓扑/弱 CSP + bower.json 前端依赖暴露

- ID: `670cf9b8-2e7a-43f2-9aac-cab4e54060b5`
- Severity: **medium**
- Status: open
- Type: 敏感信息泄露/配置缺陷
- Target: `https://epcr.tpf.gov.tw:4000/ (CSP 头) + /bower.json + /config`
- Conversation: `80f986d3-5b1e-486e-aa5f-e4ec64a430b4`
- Created: 2026-09-01 06:21:55.190463123+08:00

## Description

4000 根页面 CSP 头暴露全部内部服务端口与外部/本地 IP：self 列表含 4000-4007、9000、35.234.50.28(GCP)、localhost:8100、localhost:18081；且 script-src 包含 'unsafe-inline' 与通配符 *，CSP 形同虚设。/bower.json 无鉴权泄露前端依赖清单（angular 1.6.4、angular-jwt 0.1.9、socket.io-client 1.7.4 等多个存在 CVE 的旧版）。

## Reproduction

1) GET https://epcr.tpf.gov.tw:4000/ 查看响应头 Content-Security-Policy，确认含内部端口与 'unsafe-inline'
2) GET https://epcr.tpf.gov.tw:4000/bower.json 应返回 200 依赖清单

## Evidence

curl -skI https://epcr.tpf.gov.tw:4000/ | grep -i content-security-policy
输出含: 4000 4001 4002 4003 4004 4005 4006 4007 9000 35.234.50.28 localhost:8100 localhost:18081
curl -sk https://epcr.tpf.gov.tw:4000/bower.json -> 200 1312B angular 1.6.4 / angular-jwt 0.1.9 / socket.io-client 1.7.4 / angular 1.6.4

## Impact

攻击者获知全部内部端口映射、GCP 源站 IP 与本地容器端口，可针对性横向探测；弱 CSP(unsafe-inline+通配符) 使反射型 XSS 更易利用；旧版前端库存在已知 CVE 可被利用。

## Recommendation

1) CSP 中剔除 'unsafe-inline' 与通配符 *；2) /bower.json、/config 加鉴权或仅在构建时输出；3) 升级 angular-jwt 至修复 alg:none/签名绕过版本、socket.io-client 至新版。
