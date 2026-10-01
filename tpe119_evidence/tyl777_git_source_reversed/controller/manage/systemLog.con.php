<?php 
class page {
	public static function pageScript() { }

	public static function pageStyle() { }

	public static function pageContent() {
		$amount = 30;
		$log_type = GET::text('type');
		$log_text = GET::text('text');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `log_system`
				WHERE (`log_type` LIKE '%{$log_type}%')
				AND (`log_text` LIKE '%{$log_text}%')
				ORDER BY `log_id` DESC";
		$total = SQL::selectTotal($sql);
		$getUrl =  str_replace('&page=' . $page , '', $_SERVER['QUERY_STRING']);
		$url = '?' . $getUrl . '&page=';
		$pageLink = manage::pagingLink($url, $page, $total, $amount);
		$query = SQL::selectPage($sql, $amount, $page);

		$tableInfo = [];
		$tableHead = [
			['width' => '120', 'text' => '類型'],
			['width' => '120', 'text' => 'IP位置'],
			['width' => '500', 'text' => '紀錄內容'],
			['width' => '120', 'text' => '紀錄時間'],
		];
		$functionBtn = [ ];
		$typeList = [
			'' => '全部資料',
			'investor' => '金主紀錄',
			'custom' => '借客紀錄',
			'manage' => '管理者紀錄'
		];

		if(count($query) == 0){
			$tableInfo[] = ['type' => 'nodata'];
		}else{
			foreach($query as $log){
				$typeText = $typeList[$log['log_type']];
				$tableInfo[] = [
					'id' => $log['log_id'],
					['type' => 'center', 'text' => $typeText ],
					['type' => 'center', 'text' => $log['log_ip'] ],
					['type' => 'text', 'text' => $log['log_text'] ],
					['type' => 'center', 'text' => $log['log_time'] ],
				];
			}
		}

		$inputInfo = [
			['type' => 'select', 'text' => '文章類型', 'name' => 'type', 'value' => [$typeList, GET::text('type')], 'width' => [6, 12, 12] ],
			['type' => 'text', 'text' => '內容包含', 'name' => 'text', 'value' => GET::text('text'), 'width' => [6, 12, 12] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/systemLog');

		$html .= manage::tableList($tableHead, $tableInfo, $functionBtn, $pageLink);

		return ['操作紀錄', $html];
	}
}
?>