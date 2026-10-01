<?php 
class page {
	static $areaList = [];

	function __construct(){
		$areaList = [];
		$cityArea = cityArea;
		foreach ($cityArea as $key => $value) {
			$areaList = array_merge($areaList, $value);
		}
		self::$areaList = $areaList;
	}

	public static function pageScript() {
		?>
		<script>
			$('input[data-type=tableChekbox]').on('change', function () {
				var field = $(this).data('f');
				console.log(field);
				if(field == 'wish_status') {
					var cb_value = $(this).closest('tr').data('id');
					var cd_status = ($(this).is(":checked")) ? '1' : '0';
					var table = $(this).data('t');
					var idField = $(this).data('df');
					$.ajax({
						type: "POST",
						url: siteRootUrl + 'manage/wish/borrow',
						data: {
							t: table,
							f: field,
							d: cb_value,
							v: cd_status,
							df: idField
						},
						success: function (re) {
							if (re == 'success') {
								toastr["success"]("資料已儲存");
							} else {
								toastr["error"](re);
							}
						},
						error: function (e) {}
					});
				}
			});
		</script>
		<?php
	}

	public static function pageStyle() { }

	public static function pageContent() {
		$amount = 30;
		$id = (GET::text('id') == '')? '%':GET::text('id');
		$wish_title = GET::text('title');
		$wish_area = GET::text('area');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `wish`
				JOIN `custom` ON `wish`.`cus_id` = `custom`.`cus_id`
				WHERE (`wish`.`wish_id` LIKE '{$id}')
				AND (`wish`.`wish_title` LIKE '%{$wish_title}%')
				AND (`wish`.`wish_area` LIKE '%{$wish_area}%')
				AND `wish`.`wish_delete_time` IS NULL
				ORDER BY `wish`.`wish_id` DESC";
		$total = SQL::selectTotal($sql);
		$getUrl =  str_replace('&page=' . $page , '', $_SERVER['QUERY_STRING']);
		$url = '?' . $getUrl . '&page=';
		$pageLink = manage::pagingLink($url, $page, $total, $amount);
		$query = SQL::selectPage($sql, $amount, $page);

		$tableInfo = [];
		$tableHead = [
			['width' => '70', 'text' => '顯示'],
			['width' => '100', 'text' => '借款完成'],
			['width' => '70', 'text' => 'ID'],
			['width' => '120', 'text' => '地區'],
			['width' => '120', 'text' => '借客名稱'],
			['width' => '500', 'text' => '借款原因'],
			['width' => '120', 'text' => '借款金額'],
			['width' => '70', 'text' => ''],
		];
		$functionBtn = [
			['text' => '新增', 'class' => 'plus', 'url' => siteRootUrl . 'manage/wish/addData']
		];
		if(count($query) == 0){
			$tableInfo[] = ['type' => 'nodata'];
		}else{
			foreach($query as $wish){
				$tableInfo[] = [
					'id' => $wish['wish_id'],
					['type' => 'show', 'text' => $wish['wish_show'], 'table' => 'wish', 'field' => 'wish_show', 'idField' => 'wish_id'],
					['type' => 'checkbox', 'text' => $wish['wish_status'], 'table' => 'wish', 'field' => 'wish_status', 'idField' => 'wish_id'],
					['type' => 'center', 'text' => $wish['wish_id'] ],
					['type' => 'center', 'text' => $wish['wish_area'] ],
					['type' => 'center', 'text' => $wish['cus_name'] ],
					['type' => 'text', 'text' => $wish['wish_title'] ],
					['type' => 'money', 'text' => $wish['wish_money'] ],
					['type' => 'function', 'info' => [
						['type' => 'url', 'url' => siteRootUrl . 'wish/info/' . $wish['wish_id'], 'new' => true ],
						['type' => 'edit', 'url' => siteRootUrl . 'manage/wish/editData/' . $wish['wish_id'] ],
						['type' => 'delete', 'url' => siteRootUrl . 'manage/wish/deleteData/' . $wish['wish_id'] ],
					] ],
				];
			}
		}

		$inputInfo = [
			['type' => 'text', 'text' => '借錢需求ID', 'name' => 'id', 'value' => GET::text('id'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => '借錢需求標題', 'name' => 'title', 'value' => GET::text('title'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => '地區', 'name' => 'name', 'value' => GET::text('area'), 'width' => [4, 6, 6] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/wish');

		$html .= manage::tableList($tableHead, $tableInfo, $functionBtn, $pageLink);

		return ['借錢需求管理', $html];
	}

	public static function addData() {
		$areaList = model::setArrayKey(self::$areaList);
		$collateralList = ['信用本票', '汽/機車', '房地產', '支客票', '珠寶/名牌/古董', '3C產品'];
		$collateralList = model::setArrayKey($collateralList);
		$jobList = ['自營攤商店家', '八大行業', '計程車司機', '軍公教', '上市櫃員工', '中小企業主',
					'勞工上班族', '在學學生', '暫無工作', '其他'];
		$jobList = model::setArrayKey($jobList);
		$contactList = ['全時段', '早上 9:00 ~ 中午 12:00', '早上 9:00 ~ 下午 ６:00', '中午 12:00 ~ 下午 1:00',
					'下午 1:00 ~ 下午 ６:00', '下午 ６:00 ~ 晚上 12:00'];
		$contactList = model::setArrayKey($contactList);

		$inputInfo = [
			['text' => '借客帳號', 'type' => 'text', 'name' => 'phone', 'width' => [3, 6, 12],
			'placeholder' => '請輸入借客帳號(手機號碼)' ],

			['text' => '借客密碼', 'type' => 'text', 'name' => 'pass', 'width' => [3, 6, 12],
			'placeholder' => '請輸入借客密碼' ],

			['text' => '借客名稱', 'type' => 'text', 'name' => 'name', 'width' => [3, 6, 12],
			'placeholder' => '請輸入借客名稱' ],

			['text' => 'Line ID', 'type' => 'text', 'name' => 'line', 'width' => [3, 6, 12],
			'placeholder' => '請輸入Line ID' ],

			['text' => '借客備註', 'type' => 'textarea', 'name' => 'remark', 'width' => [12, 12, 12],
			'placeholder' => '借客備註；僅管理員觀看' ],

			['text' => '借款地區', 'type' => 'select', 'name' => 'area', 'width' => [3, 6, 12], 'other' => 'required',
			 'value' => [$areaList, '' ]],

			['text' => '借款標題', 'type' => 'text', 'name' => 'title', 'width' => [9, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入借款標題(原因)' ],

			['text' => '借款金額', 'type' => 'number', 'name' => 'money', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入借款金額' ],

			['text' => '抵押品', 'type' => 'select', 'name' => 'collateral', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請選擇抵押品', 'value' => [$collateralList, '' ] ],

			['text' => '目前執業', 'type' => 'select', 'name' => 'job', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請選擇目前執業', 'value' => [$jobList, ''] ],

			['text' => '方便聯絡時間', 'type' => 'select', 'name' => 'contact', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請選擇方便聯絡時間', 'value' => [$contactList, ''] ],

			['text' => '借款詳細說明', 'type' => 'textarea', 'name' => 'explanation', 'width' => [12, 12, 12],
			'placeholder' => '借款詳細說明' ],
		];

		$submitURL = siteRootUrl . 'manage/wish/actionAddData';
		$listURL = siteRootUrl . 'manage/wish';
		if(strpos($_SERVER['HTTP_REFERER'], $_SERVER['HTTP_HOST'] . $_SERVER['PHP_SELF'])){
			$listURL = $_SERVER['HTTP_REFERER'];
		}
		$html = manage::submitForm($inputInfo, $submitURL, $listURL, '儲存', '');
		return ['新增借錢需求資料', $html];
	}

	public static function actionAddData(){
		$cus_phone = POST::phone('phone');
		$cus_password = POST::text('pass');
		$cus_name = POST::text('name');
		$cus_line_id = POST::text('line');
		$cus_remark = POST::text('remark');

		$wish_area = POST::text('area');
		$wish_title = POST::text('title');
		$wish_money = POST::int('money');
		$wish_collateral = POST::text('collateral');
		$wish_job = POST::text('job');
		$wish_contact_time = POST::text('contact');
		$wish_explanation = POST::text('explanation');

		$custom = SQL::selectOne("SELECT * FROM `custom` WHERE `cus_phone` = ? AND `cus_delete_time` IS NULL", [$cus_phone] );
		if($custom) die('借客電話號碼重複');

		SQL::begin();
		$info = [
			'cus_phone' => $cus_phone,
			'cus_password' => password_hash($cus_password, PASSWORD_BCRYPT),
			'cus_name' => $cus_name,
			'cus_line_id' => $cus_line_id,
			'cus_remark' => $cus_remark,
			'cus_last_login' => date("Y-m-d H:i:s"),
			'cus_create_time' => date("Y-m-d H:i:s")
		];

		$sqlStatus = SQL::insert('custom', $info);
		if($sqlStatus) {
			$autoID = SQL::autoID();
			model::setLog('manage', '新增借客(' . $autoID . ')資料', $info);
			$info = [
				'cus_id' => $autoID,
				'wish_area' => $wish_area,
				'wish_title' => $wish_title,
				'wish_money' => $wish_money,
				'wish_collateral' => $wish_collateral,
				'wish_job' => $wish_job,
				'wish_contact_time' => $wish_contact_time,
				'wish_explanation' => $wish_explanation,
				'wish_create_time' => date("Y-m-d H:i:s")
			];
			$sqlStatus = SQL::insert('wish', $info);
			if($sqlStatus) {
				$autoID = SQL::autoID();
				SQL::commit();
				model::setLog('manage', '新增借錢需求(' . $autoID . ')資料', $info);
				systemEvent::createWish($autoID);
				exit('success');
			} else {
				SQL::rollback();
				model::setLog('error', 'manage-新增借錢需求時發生錯誤', $info);
				model::sendLineToAdmin("manage-新增借錢需求時發生錯誤\r\n" . siteRootUrl);
				die('資料修改時發生錯誤');
			}
		} else {
			SQL::rollback();
			model::setLog('error', 'manage-新增借客資料時發生錯誤', $info);
			model::sendLineToAdmin("manage-新增借客資料時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		die;
	}

	public static function editData() {
		$id = Router::getParameter(4);
		$wish = SQL::selectOne("SELECT * FROM `wish` WHERE `wish_id` = ? AND `wish_delete_time` IS NULL", [$id] );
		if(!$wish) {
			header('Location: ' . siteRootUrl . 'manage/wish');
			exit;
		}

		$areaList = model::setArrayKey(self::$areaList);
		$collateralList = ['信用本票', '汽/機車', '房地產', '支客票', '珠寶/名牌/古董', '3C產品'];
		$collateralList = model::setArrayKey($collateralList);
		$jobList = ['自營攤商店家', '八大行業', '計程車司機', '軍公教', '上市櫃員工', '中小企業主',
					'勞工上班族', '在學學生', '暫無工作', '其他'];
		$jobList = model::setArrayKey($jobList);
		$contactList = ['全時段', '早上 9:00 ~ 中午 12:00', '早上 9:00 ~ 下午 ６:00', '中午 12:00 ~ 下午 1:00',
					'下午 1:00 ~ 下午 ６:00', '下午 ６:00 ~ 晚上 12:00'];
		$contactList = model::setArrayKey($contactList);


		$inputInfo = [
			['name' => 'id', 'type' => 'hidden', 'value' => $id ],

			['text' => '借款地區', 'type' => 'select', 'name' => 'area', 'width' => [3, 6, 12], 'other' => 'required',
			 'value' => [$areaList, $wish['wish_area']]],

			['text' => '借款標題', 'type' => 'text', 'name' => 'title', 'width' => [9, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入借款標題(原因)', 'value' => $wish['wish_title'] ],

			['text' => '借款金額', 'type' => 'number', 'name' => 'money', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入借款金額', 'value' => $wish['wish_money'] ],

			['text' => '抵押品', 'type' => 'select', 'name' => 'collateral', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請選擇抵押品', 'value' => [$collateralList, $wish['wish_collateral']] ],

			['text' => '目前執業', 'type' => 'select', 'name' => 'job', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請選擇目前執業', 'value' => [$jobList, $wish['wish_job']] ],

			['text' => '方便聯絡時間', 'type' => 'select', 'name' => 'contact', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請選擇方便聯絡時間', 'value' => [$contactList, $wish['wish_contact_time']] ],

			['text' => '借款詳細說明', 'type' => 'textarea', 'name' => 'explanation', 'width' => [12, 12, 12],
			'placeholder' => '借款詳細說明', 'value' => $wish['wish_explanation'] ],
		];

		$submitURL = siteRootUrl . 'manage/wish/actionEditData';
		$listURL = siteRootUrl . 'manage/wish';
		if(strpos($_SERVER['HTTP_REFERER'], $_SERVER['HTTP_HOST'] . $_SERVER['PHP_SELF'])){
			$listURL = $_SERVER['HTTP_REFERER'];
		}
		$html = manage::submitForm($inputInfo, $submitURL, $listURL, '修改', '');
		return ['修改借錢需求資料 - ' . $wish['wish_title'], $html];
	}

	public static function actionEditData(){
		$id = POST::text('id');
		$wish_area = POST::text('area');
		$wish_title = POST::text('title');
		$wish_money = POST::int('money');
		$wish_collateral = POST::text('collateral');
		$wish_job = POST::text('job');
		$wish_contact_time = POST::text('contact');
		$wish_explanation = POST::text('explanation');

		$wish = SQL::selectOne("SELECT * FROM `wish` WHERE `wish_id` = ? AND `wish_delete_time` IS NULL", [$id] );
		if(!$wish) die('查無借錢需求資料');

		$info = [
			'wish_area' => $wish_area,
			'wish_title' => $wish_title,
			'wish_money' => $wish_money,
			'wish_collateral' => $wish_collateral,
			'wish_job' => $wish_job,
			'wish_contact_time' => $wish_contact_time,
			'wish_explanation' => $wish_explanation,
		];

		$sqlStatus = SQL::update('wish', $info, ['wish_id' => $id]);
		if($sqlStatus) {
			model::setLog('manage', '修改借錢需求(' . $wish['wish_id'] . ')資料；原資料備份', $wish);
			exit('success');
		} else{
			model::setLog('error', 'manage-修改借錢需求時發生錯誤', $info);
			model::sendLineToAdmin("manage-修改借錢需求時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		die;
	}

	public static function deleteData(){
		$id = Router::getParameter(4);
		$wish = SQL::selectOne("SELECT * FROM `wish` WHERE `wish_id` = ?", [$id] );
		if(!$wish) exit('查無資料');
		$info = ['wish_delete_time' => date("Y-m-d H:i:s") ];
		$sqlStatus = SQL::update('wish', ['wish_delete_time' => date("Y-m-d H:i:s")], ['wish_id' => $id ] );
		if($sqlStatus){
			model::setLog('manage', '刪除借錢需求', $wish);
			exit('success');
		} else {
			model::setLog('error', 'manage-刪除借錢需求時發生錯誤', $info);
			model::sendLineToAdmin("manage-刪除借錢需求時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		die;
	}

	public static function borrow() {
		$ID = POST::text('d');
		$value = POST::text('v');
		$wish_borrow_time = ($value == 1)? date("Y-m-d H:i:s"):null;
		$info = [
			'wish_status' => $value,
			'wish_borrow_time' => $wish_borrow_time
		];
		$sqlStatus = SQL::update('wish', $info, ['wish_id' => $ID]);
		if($sqlStatus){
			model::setLog('manage', '修改借錢需求(' . $ID . ')借款狀態', $info);
			exit('success');
		} else {
			model::setLog('error', 'manage-借錢需求狀態修改發生錯誤', $info);
			model::sendLineToAdmin("manage-借錢需求狀態修改發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		die;
	}
}
?>