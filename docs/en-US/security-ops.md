# Web security scans

The Web security scan page keeps tasks, progress, findings, and reports inside JySecAI. The scan itself runs on an operator-deployed [Xalgorix](https://github.com/xalgorix/xalgorix) service. JySecAI does not start that container.

Add this to `config.yaml`:

```yaml
xalgorix:
  enabled: true
  base_url: "http://127.0.0.1:9137"
  api_token: "" # XALGORIX_API_TOKEN, API routes only
```

`api_token` is not returned by the settings API or the engine catalog. Requests stay on the configured host. Link-local and cloud metadata addresses are rejected.

A task stays awaiting approval until someone with approval permission accepts it. Only then does JySecAI send the targets and the objective to Xalgorix. Every target must match the authorization patterns entered for that task. Review mode asks for the reconnaissance phase only. Exploit validation asks for Xalgorix's verification phase only.

Reports download through JySecAI. The browser never receives the Xalgorix admin address. Do not expose that admin panel to the public internet, and scan only targets you own or are explicitly authorized to test.
