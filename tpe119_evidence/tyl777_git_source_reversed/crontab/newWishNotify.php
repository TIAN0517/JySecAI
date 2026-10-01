<?php
$rootPath = dirname(dirname(__FILE__));
require_once($rootPath . '/model/config.php');

$wishID = $argv[1];
$wish = SQL::selectOne("SELECT * FROM `wish` WHERE `wish_id` = ? AND `wish_delete_time` IS NULL", [$wishID] );
if($wish) {
	$moneyText = ((int)$wish['wish_money']/10000) . '萬';
	$messageInfo = [
		'event' => 'newWish',
		'id' => $wishID,
		'title' => $wish['wish_title'],
		'area' => $wish['wish_area'],
		'money' => $moneyText,
		'collateral' => $wish['wish_collateral'],
		'create_time' => $wish['wish_contact_time']
	];
	$messageInfo = json_encode($messageInfo);
	// model::sendLineToAdmin("速借款 - 有新的借錢需求發布：" . $wishID);
	$modelClass = new model;
	set_error_handler([$modelClass, 'warningHandler'], E_WARNING);
	require_once(rootPath . '/model/libaries/webSocketClient.php');
	$WebSocketClient = new WebsocketClient($siteRootUrl, '34.80.100.149', 9453, $messageInfo);

	$area = '';
	foreach (cityArea as $key => $cityList) {
		if(in_array($wish['wish_area'], $cityList)) $area = $key;
	}

	$message = "金主會員您好：" . "\r\n";
	$message .= "下方連結是[" . $area . "]地區的借客發布最新的借錢需求資訊" . "\r\n";
	$message .= "https://tyl777.com/wish/info/" . $wishID . "\r\n";
	$message .= "可盡速與借客聯繫" . "\r\n\r\n";
	$message .= "速借款官網" . "\r\n";
	$message .= "https://tyl777.com" . "\r\n";
	$message .= "客服聯繫管道" . "\r\n";
	$message .= "Line@:@685lrxpo" . "\r\n";

	$investorList = SQL::selectAll("SELECT * FROM `investor` WHERE `inv_ban` = 0 AND `inv_expiry_time` > NOW()
								AND `inv_line_token` != ''");
	// model::sendLineToAdmin("速借款 - 開始通知新的發布需求");
	foreach ($investorList as $investor) {
		model::sendLine($investor['inv_line_token'], $message);
	}
}
?>