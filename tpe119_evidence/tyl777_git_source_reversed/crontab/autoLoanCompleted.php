<?php
$rootPath = dirname(dirname(__FILE__));
require_once($rootPath . '/model/config.php');
//--------------------------------[14天自動完成借款]--------------------------------
SQL::begin();
$daysAgo = date("Y-m-d", strtotime('-4 day'));
$wishList = SQL::selectAll("SELECT * FROM `wish` WHERE `wish_delete_time` IS NULL AND `wish_status` = 0
							AND `wish_create_time` < ?", [$daysAgo]);
$sqlStatus = true;
foreach ($wishList as $wish) {
	$sqlStatus = SQL::update('wish', ['wish_status' => 1], ['wish_id' => $wish['wish_id']] );
	if(!$sqlStatus) {
		SQL::rollback();
		model::setLog('error', '借錢需求 (' . $wish['wish_id'] . ') 自動下架發生錯誤', $wish);
		model::sendLineToAdmin("借錢需求 (" . $wish['wish_id'] . ") 自動下架發生錯誤\r\n");
		exit;
	}
}
SQL::commit();
// model::sendLineToAdmin("名片自動上下架完成");

?>