<?php
$rootPath = dirname(dirname(__FILE__));
require_once($rootPath . '/model/config.php');
//--------------------------------[名片自動上架下]--------------------------------
SQL::begin();
$cardList = SQL::selectAll("SELECT * FROM `card` WHERE `card_delete_time` IS NULL
							AND ( (`card_listing` >= CURRENT_TIMESTAMP - INTERVAL 30 MINUTE
									AND `card_listing` <= CURRENT_TIMESTAMP + INTERVAL 30 MINUTE
									AND `card_show` = 0)
							OR (`card_delisting` >= CURRENT_TIMESTAMP - INTERVAL 30 MINUTE
									AND `card_delisting` <= CURRENT_TIMESTAMP + INTERVAL 30 MINUTE
									AND `card_show` = 1) )");
$sqlStatus = true;
foreach ($cardList as $card) {
	if($card['card_show'] == 1 && strtotime($card['card_delisting']) > (time() - 1800) ) {
		$sqlStatus = SQL::update('card', ['card_show' => 0], ['card_id' => $card['card_id']] );
		model::sendLineToAdmin("名片(" . $card['card_id'] . ") 自動下架");
	} else if($card['card_show'] == 0 && strtotime($card['card_listing']) > (time() - 1800) ) {
		$sqlStatus = SQL::update('card', ['card_show' => 1], ['card_id' => $card['card_id']] );
		model::sendLineToAdmin("名片(" . $card['card_id'] . ") 自動上架");
	}

	if(!$sqlStatus) {
		SQL::rollback();
		model::setLog('error', '名片(' . $card['card_id'] . ') 自動上下架發生錯誤', $card);
		model::sendLineToAdmin("名片(" . $card['card_id'] . ") 自動上下架發生錯誤\r\n");
		exit;
	}
}
SQL::commit();
// model::sendLineToAdmin("名片自動上下架完成");

?>