# Web 安全扫描

「Web 安全扫描」把任务、进度、发现和报告留在 JySecAI 里。扫描本身交给操作者单独部署的 [Xalgorix](https://github.com/xalgorix/xalgorix)，JySecAI 不启动它的容器。

在 `config.yaml` 填写：

```yaml
xalgorix:
  enabled: true
  base_url: "http://127.0.0.1:9137"
  api_token: "" # XALGORIX_API_TOKEN，只授权 /api
```

`api_token` 不会出现在设置接口或目录响应里。地址只接受配置里的那一台主机；连到链路本地或云元数据地址会被拒绝。

页面上的任务会先停在「待审批」。具有审批权限的人批准后，JySecAI 才把目标和任务说明发给 Xalgorix。目标必须落在这次填写的授权范围内。审查只请求侦察阶段，利用验证只请求 Xalgorix 的验证阶段。

报告从本站的任务详情下载，不会把 Xalgorix 的管理地址交给浏览器。面板不要直接暴露到公网，也只扫描自己拥有或已获授权的目标。
