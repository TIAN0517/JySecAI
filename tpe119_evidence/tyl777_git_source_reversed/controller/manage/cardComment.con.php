<?php 
class page {
	public static function pageScript() { }

	public static function pageStyle() { }

	public static function pageContent() {
		$amount = 30;
		$card_id = (GET::text('id') == '')? '%':GET::text('id');
		$cc_message = GET::text('message');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `card_comment`
				JOIN `card` ON `card_comment`.`card_id` = `card`.`card_id`
				WHERE  (`card_comment`.`card_id` LIKE '{$card_id}')
				AND (`card_comment`.`cc_message` LIKE '%{$cc_message}%')
				ORDER BY `cc_id` DESC";
		$total = SQL::selectTotal($sql);
		$getUrl =  str_replace('&page=' . $page , '', $_SERVER['QUERY_STRING']);
		$url = '?' . $getUrl . '&page=';
		$pageLink = manage::pagingLink($url, $page, $total, $amount);
		$query = SQL::selectPage($sql, $amount, $page);

		$tableInfo = [];
		$tableHead = [
			['width' => '70', 'text' => '顯示'],
			['width' => '100', 'text' => '類型'],
			['width' => '200', 'text' => '留言者'],
			['width' => '400', 'text' => '留言內容'],
			['width' => '200', 'text' => '留言時間'],
			['width' => '70', 'text' => ''],
		];
		$functionBtn = [ ];

		if(count($query) == 0){
			$tableInfo[] = ['type' => 'nodata'];
		}else{
			foreach($query as $log){
				$type = '借客留言';
				if($log['cc_level'] == 2 && $log['cc_identity'] == 'custom' ) $type = '借客回覆';
				else if($log['cc_level'] == 2 && $log['cc_identity'] == 'investor' ) $type = '金主回覆';
				$identityName = '';
				if($log['cc_identity'] == 'custom') {
					$customInfo = custom::info($log['cc_identity_id']);
					$identityName = '借客:' . $customInfo['cus_name'] . '<br>(' . $customInfo['cus_phone'] . ')';
				} else if($log['cc_identity'] == 'investor') {
					$investorInfo = investor::contactInfo($log['cc_identity_id']);
					$identityName = '金主:' . $investorInfo['contact'] . '<br>(' . $investorInfo['phone'] . ')';
				}
				$tableInfo[] = [
					'id' => $log['cc_id'],
					['type' => 'show', 'text' => $log['cc_show'], 'table' => 'card_comment', 'field' => 'cc_show', 'idField' => 'cc_id'],
					['type' => 'text', 'text' => $type ],
					['type' => 'text', 'text' => $identityName ],
					['type' => 'text', 'text' => $log['cc_message'] ],
					['type' => 'center', 'text' => $log['cc_create_time'] ],
					['type' => 'function', 'info' => [
						['type' => 'url', 'url' => siteRootUrl . 'card/' . $log['card_id'], 'new' => true ],
					] ],
				];
			}
		}

		$inputInfo = [
			['type' => 'text', 'text' => '名片ID', 'name' => 'id', 'value' => GET::text('id'), 'width' => [4, 12, 12] ],
			['type' => 'text', 'text' => '留言內容', 'name' => 'text', 'value' => GET::text('text'), 'width' => [4, 6, 12] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/cardComment');

		$html .= manage::tableList($tableHead, $tableInfo, $functionBtn, $pageLink);

		return ['名片留言紀錄', $html];
	}
}
?>