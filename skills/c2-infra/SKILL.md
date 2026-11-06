---
name: c2-infra
description: >-
  C2基础设施:心跳曲线设计(sleep/jitter),流量特征管理(UA/URI轮换,malleable profile概念),重定向链与备援通道,基础设施自治体清理与烧毁准则。Use when designing C2 heartbeat, managing traffic signatures, building redirector chains, or planning infra teardown.
metadata:
  tags: [渗透测试, penetration-testing, 红队]
---

## C2 基础设施 / 流量隐蔽

> 声明:本 Skill 所有手法仅限授权范围内使用(redirector/listener 部署须在 SOW 允许的网络与资产上进行)。C2 是行动生命线:先定 kill date 与烧毁预案,再上第一台 beacon;每处持久化实时记入 `pentest-output-standards` 改动台账。

```
=== 心跳曲线设计(sleep/jitter) ===
低调型: sleep 300-900s + jitter 30-50%(如 beacon sleep 600 0.4) — 心跳间隔离散化,不落固定整点
  交互式任务: 下发任务时临时提频,拿完立刻回低调档(手动或自动化切换profile)
  贴作息: 目标工作时间激活,深夜/周末准停(计划任务切配置) — "下班心跳"比全天心跳更不显眼
  验证(证据): 对端抓包/流量图确认心跳间隔呈随机分布而非固定值;自查无整点定时器指纹;防守方视角=流量基线平滑
  回滚/清理: 每个listener/beacon的sleep配置与kill date写台账;kill date 到期自毁是最后防线
=== 流量特征管理 ===
UA管理: 从目标真实流量抓UA池(浏览器/业务客户端),每N次心跳轮换;禁用工具默认UA(Cobalt Strike默认/经典恶意UA=秒标记)
URI伪装: 心跳路径贴目标业务形态(/api/v2/report,/static/js/vendor.min.js),GET/POST模板与真实业务请求对齐
malleable概念(配置化流量): C2 profile 定制请求/响应模板、证书、数据编码(base64/xor+padding)、jitter — 上线前用公开检测规则(sigma/snort/suricata规则集)自测,命中即改
  证书: 对redirector域名签发有效证书(Let's Encrypt),SAN/OU贴目标业务;有条件对齐JA3与真实浏览器
  验证: curl -v 心跳URL返回伪装页(404/登录页);wireshark确认全程TLS且无明文C2关键字;用IDS规则自扫一遍为阴性
  回滚/清理: profile与域名映射表进台账;换profile=旧URI/UA立即停用
=== 重定向链与备援通道 ===
分层架构(必做,不裸奔teamserver): beacon → redirector → teamserver
  redirector实现: 云函数(按约定头过滤)/Apache mod_rewrite(非约定UA/URI/参数302到真实网站)/iptables DNAT/socat
  mod_rewrite规则示例: RewriteCond %{HTTP_USER_AGENT} !^Mozilla.*约定标记 [NC] → RewriteRule ^.*$ http://真实站点/ [R=302,L]
  验证: 非法请求到redirector必须返回与真实站点一致的页面(证据=curl对比输出/截图);只有带约定特征的请求进teamserver
备援通道(主通道挂了能切): 主HTTPS + 备DNS TXT隧道/合法云服务中转(概念:用合法云API当中继,如工单/网盘接口) — 备通道平时不活跃,切换动作写台账
域前置/CDN前置(概念): SNI指向高信誉域+Host头到C2 — 主流CDN多已封禁,用前必须实测可用,不可依赖
  回滚/清理: redirector配置(Cron/云函数/DNS记录)逐条台账;烧毁时逆序拆除
=== 基础设施自治体清理与烧毁准则 ===
🚨烧毁准则(命中任一立即执行,不犹豫): 1.未授权方(蓝队/扫描器)主动触碰teamserver端口 2.redirector域名/IP出现在威胁情报平台 3.beacon主机被隔离或取证动作迹象 4.用户侧感知异常(登录提醒/EDR弹窗)
烧毁步骤(顺序执行): 停listener(断新连接) → 逐beacon退出并删持久化(按台账逆序:Run键/计划任务/服务/WMI订阅) → 销毁teamserver VPS(不留快照) → 弃用redirector域名与证书 → 记录烧毁时间/原因/波及范围进台账与黑板
  验证(证据): beacon全下线确认(teamserver连接数=0)+目标侧持久化复查(netexec枚举计划任务/服务)=清理闭环
  清理清单: teamserver进程/证书/日志、云函数与Cron、DNS记录、beacon侧持久化(逐台账行核对)
> 心跳设计决定"活多久",烧毁预案决定"出事多大"。宁可不打通,不留一条被溯源的通道。
```
