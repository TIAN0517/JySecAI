<?php 
class page {
	public static function pageScript() { }

	public static function pageStyle() { }

	public static function pageContent() {
		$amount = 30;
		$wish_id = (GET::text('id') == '')? '%':GET::text('id');
		$wc_message = GET::text('message');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `wish_comment`
				JOIN `wish` ON `wish_comment`.`wish_id` = `wish`.`wish_id`
				WHERE  (`wish_comment`.`wish_id` LIKE '{$wish_id}')
				AND (`wish_comment`.`wc_message` LIKE '%{$wc_message}%')
				ORDER BY `wc_id` DESC";
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
				$type = '金主留言';
				if($log['wc_level'] == 2 && $log['wc_identity'] == 'custom' ) $type = '借客回覆';
				else if($log['wc_level'] == 2 && $log['wc_identity'] == 'investor' ) $type = '金主回覆';
				$identityName = '';
				if($log['wc_identity'] == 'custom') {
					$customInfo = custom::info($log['wc_identity_id']);
					$identityName = '借客:' . $customInfo['cus_name'] . '<br>(' . $customInfo['cus_phone'] . ')';
				} else if($log['wc_identity'] == 'investor') {
					$investorInfo = investor::contactInfo($log['wc_identity_id']);
					$identityName = '金主:' . $investorInfo['contact'] . '<br>(' . $investorInfo['phone'] . ')';
				}
				$tableInfo[] = [
					'id' => $log['wc_id'],
					['type' => 'show', 'text' => $log['wc_show'], 'table' => 'wish_comment', 'field' => 'wc_show', 'idField' => 'wc_id'],
					['type' => 'text', 'text' => $type ],
					['type' => 'text', 'text' => $identityName ],
					['type' => 'text', 'text' => $log['wc_message'] ],
					['type' => 'center', 'text' => $log['wc_create_time'] ],
					['type' => 'function', 'info' => [
						['type' => 'url', 'url' => siteRootUrl . 'wish/info/' . $log['wish_id'], 'new' => true ],
					] ],
				];
			}
		}

		$inputInfo = [
			['type' => 'text', 'text' => '借錢需求ID', 'name' => 'id', 'value' => GET::text('id'), 'width' => [4, 12, 12] ],
			['type' => 'text', 'text' => '留言內容', 'name' => 'text', 'value' => GET::text('text'), 'width' => [4, 6, 12] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/smsLog');

		$html .= manage::tableList($tableHead, $tableInfo, $functionBtn, $pageLink);

		return ['借錢需求留言紀錄', $html];
	}
}
?>