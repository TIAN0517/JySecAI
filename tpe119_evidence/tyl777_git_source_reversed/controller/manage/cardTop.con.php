<?php 
class page {
	public static function pageScript() { }

	public static function pageStyle() { }

	public static function pageContent() {
		$amount = 30;
		$card_title = GET::text('title');
		$inv_phone = GET::text('investor');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `card_top_log`
				JOIN `card` ON `card_top_log`.`card_id` = `card`.`card_id`
				JOIN `investor` ON `investor`.`inv_id` = `card`.`inv_id`
				WHERE  (`card`.`card_title` LIKE '%{$card_title}%')
				AND (`investor`.`inv_phone` LIKE '%{$inv_phone}%')
				ORDER BY `ctl_id` DESC";
		$total = SQL::selectTotal($sql);
		$getUrl =  str_replace('&page=' . $page , '', $_SERVER['QUERY_STRING']);
		$url = '?' . $getUrl . '&page=';
		$pageLink = manage::pagingLink($url, $page, $total, $amount);
		$query = SQL::selectPage($sql, $amount, $page);

		$tableInfo = [];
		$tableHead = [
			['width' => '120', 'text' => '類型'],
			['width' => '200', 'text' => '金主帳號'],
			['width' => '500', 'text' => '名片資訊'],
			['width' => '200', 'text' => '置頂時間'],
			['width' => '70', 'text' => ''],
		];
		$functionBtn = [ ];

		if(count($query) == 0){
			$tableInfo[] = ['type' => 'nodata'];
		}else{
			foreach($query as $log){
				$type = '手動';
				if($log['ctl_type'] == 'auto' ) $type = '自動置頂';
				$tableInfo[] = [
					'id' => $log['wc_id'],
					['type' => 'center', 'text' => $type ],
					['type' => 'text', 'text' => $log['inv_phone'] ],
					['type' => 'text', 'text' => $log['card_contact'] . '<br>' . $log['card_title'] ],
					['type' => 'center', 'text' => $log['ctl_create_time'] ],
					['type' => 'function', 'info' => [
						['type' => 'url', 'url' => siteRootUrl . 'card/' . $log['card_id'], 'new' => true ],
					] ],
				];
			}
		}

		$inputInfo = [
			['type' => 'text', 'text' => '金主帳號', 'name' => 'investor', 'value' => GET::text('investor'), 'width' => [4, 12, 12] ],
			['type' => 'text', 'text' => '名片標題', 'name' => 'title', 'value' => GET::text('title'), 'width' => [4, 6, 12] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/cardTop');

		$html .= manage::tableList($tableHead, $tableInfo, $functionBtn, $pageLink);

		return ['名片置頂紀錄', $html];
	}
}
?>