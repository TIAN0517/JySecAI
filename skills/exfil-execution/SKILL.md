---
name: exfil-execution
description: >-
  数据外传:DNS/HTTPS/云外传通道选择,数据最小化与加密暂存,外传量控制与告警阈值规避概念,外传证据回收与双端校验。Use when planning exfiltration channels, encrypting staged data, pacing transfer volume, or recovering exfil evidence.
metadata:
  tags: [渗透测试, penetration-testing, 红队]
---

## 数据外传 / Exfiltration

> 声明:本 Skill 所有手法仅限授权范围内使用(外传通道与数据范围须在 SOW 明确允许,未授权第三方云一律禁用)。外传是攻击链最后一步,也是合规责任最重的一步:通道合法性、数据最小化、双端校验缺一不可。

```
=== 通道选择 ===
DNS外传: dnscat2(双端)/iodine — 适用场景:目标仅放行53出站;数据走TXT/NULL记录
  opsec: DNS熵值与请求量是检测点 → 分片<255字符+低频+域名贴目标业务(如 *.cdn-updates.target.local)
  验证(证据): server端会话收齐数据 + 传输前后 sha256sum 比对一致(输出存证)
HTTPS外传(首选): 贴合法HTTPS出站,优先复用已有C2/beacon加密通道传文件(有合法流量掩护,不新增出口)
  自建中转: 授权VPS上webdav/上传接口,TLS必须(禁明文http);证书与redirector同一套伪装体系(见`c2-infra`)
  验证: 中转端文件 sha256 与源端一致 + 解密抽检可读(证据=比对输出)
云通道(概念): 仅限SOW允许的对象存储/协作API中转 — 用前核对数据落地司法辖区与留存策略;禁用任何未授权第三方云(合规与溯源双重风险)
=== 数据最小化与加密暂存 ===
最小化: 只传SOW要的数据(逐项对清单),不"顺手全打包" — 量大=告警大+责任大;超大目录先抽样确认价值再全量
暂存加密(目标侧先加密再落盘): 7z a -p'<强口令>' -mhe=on out.7z data/ 或 openssl enc -aes-256-cbc -pbkdf2 -salt -in bundle.tar.gz -out bundle.enc
  口令传递: 密钥经既有加密C2通道传递,不在目标盘明文留存
  验证: 目标侧解密试读(bundle.tar.gz tzf列表/7z t完整性),证据=解密输出首屏;中转端复验哈希
  回滚/清理: 明文中间件(bundle.tar.gz/原始收集目录)shred -u(Windows sdelete),每个文件一行台账;密文按SOW决定留否
=== 外传量控制与告警阈值规避(概念) ===
限速贴合基线: 通道层限速(dnscat2窗口/分片sleep/应用层分批)≤目标出站基线突增10%;避开夜间全量备份与日终报表窗口(基线比对最敏感时段)
分批切片: 大包切卷 7z -v100m 或 split -b 100m → 按天分批 → 单次量贴业务高峰形态;优先复用C2心跳通道(已有流量掩护)
  验证: 传输期间与防守方约定口径核对无告警(SOW内);流量图与历史基线形状一致(证据=流量截图/脚本统计)
  回滚/清理: 中断的半包(分卷)标记台账,续传或销毁,不留孤儿分卷
=== 外传证据回收 ===
双端记账: 每个外传包登记五元组(源路径+sha256+大小+通道+时间) → 台账+黑板 finding/exfil Fact(见`pentest-output-standards`/`pentest-blackboard`)
回收校验: 中转端 sha256sum -c 全量校验 → 解密抽检 → 报告附包清单与哈希;校验通过后按需清除目标侧密文(征得用户/按SOW)并销毁密钥(交付解密后即毁)
  验证: 客户侧拿到包能解密(终验)=证据链闭环
> 外传纪律: 每个字节都有授权、有清单、有哈希、有终点。传完的那一刻,证据链才开始生效。
```
