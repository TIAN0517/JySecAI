<?php
$rootPath = dirname(dirname(__FILE__));
require_once($rootPath . '/model/config.php');
//--------------------------------[名片自動上架下]--------------------------------
SQL::begin();
$topSettingList = SQL::selectAll("SELECT * FROM `card_top_setting` JOIN `card` ON `card`.`card_id` = `card_top_setting`.`card_id`
								 WHERE `card_top_setting`.`cts_timing` = ? AND `card_top_setting`.`cts_status` = 1 AND `card`.`card_delete_time` IS NULL
								 AND `card`.`card_show` = 1 AND `card`.`card_status` = 0 AND `card`.`card_expiry_time` > NOW()", [date('H')]);
$sqlStatus = true;
foreach ($topSettingList as $setting) {
	$logList = SQL::selectOne("SELECT count(*) AS `listCount` FROM `card_top_log` WHERE `card_id` = ?
								AND TO_DAYS(`ctl_create_time`) = TO_DAYS(NOW())", [$setting['card_id']]);
	if((int)$logList['listCount'] >= (int)$setting['card_refresh'] ) continue;

	$info = [
		'ctl_type' => 'auto',
		'card_id' => $setting['card_id'],
		'ctl_create_time' => date("Y-m-d H:i:s")
	];
	$sqlStatus = SQL::insert('card_top_log', $info);
	if(!$sqlStatus) {
		SQL::rollback();
		model::setLog('error', '名片(' . $setting['card_id'] . ') 自動置頂記錄錯誤', $info);
		model::sendLineToAdmin("名片(" . $setting['card_id'] . ") 自動置頂記錄錯誤\r\n" . siteRootUrl);
		exit;
	}

	$sqlStatus = SQL::update('card', ['card_sticky_time' => date("Y-m-d H:i:s")], ['card_id' => $setting['card_id']] );
	if(!$sqlStatus) {
		SQL::rollback();
		model::setLog('error', '名片(' . $setting['card_id'] . ') 更改自動置頂時間錯誤', $setting);
		model::sendLineToAdmin("名片(" . $setting['card_id'] . ") 更改自動置頂時間錯誤\r\n" . siteRootUrl);
		exit;
	}

	$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_id` = ? AND `inv_ban` = 0 AND `inv_expiry_time` > NOW()
										AND `inv_line_token` != ''", [$setting['inv_id']]);
	if($investor) {
		$message = "金主會員您好：" . "\r\n";
		$message .= "您的名片已自動置頂" . "\r\n";
		$message .= "https://tyl777.com/card/" . $setting['card_id'] . "\r\n\r\n";
		$message .= "速借款官網" . "\r\n";
		$message .= "https://tyl777.com" . "\r\n";
		$message .= "客服聯繫管道" . "\r\n";
		$message .= "Line@:@685lrxpo" . "\r\n";
		model::sendLine($investor['inv_line_token'], $message);
	}
}
SQL::commit();
// model::sendLineToAdmin("名片自動置頂完成");

?>