<?php 
class page {
	public static function pageScript() { }

	public static function pageStyle() { }

	public static function pageContent() {
		$amount = 30;
		$logs_text = GET::text('text');
		$logs_phone = GET::text('phone');
		$inv_phone = GET::text('investor');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `log_sms`
				JOIN `investor` ON `investor`.`inv_id` = `log_sms`.`inv_id`
				WHERE (`log_sms`.`logs_phone` LIKE '%{$logs_phone}%')
				AND (`log_sms`.`logs_text` LIKE '%{$logs_text}%')
				AND (`investor`.`inv_phone` LIKE '%{$inv_phone}%')
				ORDER BY `logs_id` DESC";
		$total = SQL::selectTotal($sql);
		$getUrl =  str_replace('&page=' . $page , '', $_SERVER['QUERY_STRING']);
		$url = '?' . $getUrl . '&page=';
		$pageLink = manage::pagingLink($url, $page, $total, $amount);
		$query = SQL::selectPage($sql, $amount, $page);

		$tableInfo = [];
		$tableHead = [
			['width' => '120', 'text' => '金主帳號'],
			['width' => '120', 'text' => '借客電話'],
			['width' => '500', 'text' => '簡訊內容'],
			['width' => '120', 'text' => '紀錄時間'],
		];
		$functionBtn = [ ];

		if(count($query) == 0){
			$tableInfo[] = ['type' => 'nodata'];
		}else{
			foreach($query as $log){
				$tableInfo[] = [
					'id' => $log['logs_id'],
					['type' => 'text', 'text' => $log['inv_phone'] ],
					['type' => 'center', 'text' => $log['logs_phone'] ],
					['type' => 'text', 'text' => $log['logs_text'] ],
					['type' => 'center', 'text' => $log['logs_create_time'] ],
				];
			}
		}

		$inputInfo = [
			['type' => 'text', 'text' => '金主帳號', 'name' => 'investor', 'value' => GET::text('investor'), 'width' => [4, 12, 12] ],
			['type' => 'text', 'text' => '借客電話', 'name' => 'phone', 'value' => GET::text('phone'), 'width' => [4, 6, 12] ],
			['type' => 'text', 'text' => '簡訊內容', 'name' => 'text', 'value' => GET::text('text'), 'width' => [4, 6, 12] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/smsLog');

		$html .= manage::tableList($tableHead, $tableInfo, $functionBtn, $pageLink);

		return ['簡訊紀錄', $html];
	}
}
?>