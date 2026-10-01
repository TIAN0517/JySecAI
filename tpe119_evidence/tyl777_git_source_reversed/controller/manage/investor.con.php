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
			$('.checkbox[value="all"]').click(function() {
				var status = $(this).is(":checked");
				$(this).closest('.areaArea').find('.checkbox').prop("checked", status);
			});
		</script>
		<?php
	}

	public static function pageStyle() {
		?>
		<style>
			a.btn.icon_btn.plus {
				width: 100%;
				margin-bottom: 10px;
			}
		</style>
		<?php
	}

	public static function pageContent() {
		$amount = 30;
		$inv_id = (GET::text('id') == '')? '%':GET::text('id');
		$inv_phone = GET::text('phone');
		$inv_remark = GET::text('remark');
		$inv_program = GET::text('program');
		$inv_line_id = GET::text('line');
		$inv_email = GET::text('email');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `investor`
				WHERE (`investor`.`inv_id` LIKE '{$inv_id}')
				AND (`investor`.`inv_phone` LIKE '%{$inv_phone}%')
				AND (`investor`.`inv_remark` LIKE '%{$inv_remark}%')
				AND (`investor`.`inv_program` LIKE '%{$inv_program}%')
				AND (`investor`.`inv_line_id` LIKE '%{$inv_line_id}%')
				AND (`investor`.`inv_email` LIKE '%{$inv_email}%')
				AND `inv_delete_time` IS NULL
				ORDER BY `investor`.`inv_id` DESC";
		$total = SQL::selectTotal($sql);
		$getUrl =  str_replace('&page=' . $page , '', $_SERVER['QUERY_STRING']);
		$url = '?' . $getUrl . '&page=';
		$pageLink = manage::pagingLink($url, $page, $total, $amount);
		$query = SQL::selectPage($sql, $amount, $page);

		$tableInfo = [];
		$tableHead = [
			['width' => '70', 'text' => '禁用'],
			['width' => '70', 'text' => 'VIP'],
			['width' => '70', 'text' => 'ID'],
			['width' => '150', 'text' => '金主帳號'],
			['width' => '150', 'text' => '金主方案'],
			['width' => '120', 'text' => 'Line ID'],
			['width' => '150', 'text' => '最後登入時間'],
			['width' => '110', 'text' => ''],
		];
		
		if(count($query) == 0){
			$tableInfo[] = ['type' => 'nodata'];
		}else{
			foreach($query as $investor){
				$warn = '';
				if(strtotime($investor['inv_expiry_time']) < time()) $warn = '已過期';

				$tableInfo[] = [
					'id' => $investor['inv_id'],
					['type' => 'ban', 'text' => $investor['inv_ban'], 'table' => 'investor', 'field' => 'inv_ban', 'idField' => 'inv_id'],
					['type' => 'checkbox', 'text' => $investor['inv_vip'], 'table' => 'investor', 'field' => 'inv_vip', 'idField' => 'inv_id'],
					['type' => 'center', 'text' => $investor['inv_id'] ],
					['type' => 'text', 'text' => $investor['inv_phone'], 'warn' => $warn ],
					['type' => 'text', 'text' => $investor['inv_program'] ],
					['type' => 'text', 'text' => $investor['inv_line_id'] ],
					['type' => 'center', 'text' => $investor['inv_last_login'] ],
					['type' => 'function', 'info' => [
						['type' => 'url', 'url' => siteRootUrl . 'manage/card/addData?invID=' . $investor['inv_id'],
							'title' => '新增名片', 'text' => '<i class="fas fa-plus"></i>'],
						['type' => 'edit', 'url' => siteRootUrl . 'manage/investor/editData/' . $investor['inv_id'] ],
						['type' => 'url', 'new' => true, 'url' => siteRootUrl . 'manage/investor/changeUser/' . $investor['inv_id'],
							'title' => '切換登入帳號', 'text' => '<i class="fas fa-sign-in-alt"></i>'],
						['type' => 'delete', 'url' => siteRootUrl . 'manage/investor/deleteData/' . $investor['inv_id'] ],
					] ],
				];
			}
		}

		$functionBtn = [
			['text' => '新增', 'class' => 'plus', 'url' => siteRootUrl . 'manage/investor/addData']
		];

		$inputInfo = [
			['type' => 'text', 'text' => '金主ID', 'name' => 'id', 'value' => GET::text('id'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => '金主帳號', 'name' => 'phone', 'value' => GET::text('phone'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => '方案名稱', 'name' => 'program', 'value' => GET::text('program'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => 'Line ID', 'name' => 'line', 'value' => GET::text('line'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => 'Email', 'name' => 'email', 'value' => GET::text('email'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => '備註包含', 'name' => 'remark', 'value' => GET::text('remark'), 'width' => [4, 6, 6] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/investor');

		$html .= manage::tableList($tableHead, $tableInfo, $functionBtn, $pageLink);

		return ['金主管理', $html];
	}

	public static function addData() {

		$inputInfo = [
			['text' => '金主帳號', 'type' => 'text', 'name' => 'phone', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入金主帳號(手機號碼)'],

			['text' => '金主密碼', 'type' => 'text', 'name' => 'pass', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入金主密碼'],

			['text' => 'Email', 'type' => 'text', 'name' => 'email', 'width' => [3, 6, 12], 'placeholder' => '請輸入Email'],

			['text' => 'Line ID', 'type' => 'text', 'name' => 'line', 'width' => [3, 6, 12], 'placeholder' => '請輸入Line ID'],

			['text' => '方案名稱', 'type' => 'text', 'name' => 'program', 'width' => [3, 6, 12], 'placeholder' => '請輸入方案名稱'],

			['text' => '帳號到期日', 'type' => 'datetime', 'name' => 'expiry', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請選擇方案到期日', 'value' => date("Y-m-d H:i:s") ],

			['text' => '開通名片數量', 'type' => 'number', 'name' => 'card', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入開通的名片數量', 'value' => 0 ],

			['text' => '簡訊餘額', 'type' => 'number', 'name' => 'short', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入目前簡訊餘額', 'value' => 0 ],

			['text' => '金主備註', 'type' => 'textarea', 'name' => 'remark', 'width' => [12, 12, 12], 'placeholder' => '金主備註；僅管理員觀看' ]
		];

		$submitURL = siteRootUrl . 'manage/investor/actionAddData';
		$listURL = siteRootUrl . 'manage/investor';
		if(strpos($_SERVER['HTTP_REFERER'], $_SERVER['HTTP_HOST'] . $_SERVER['PHP_SELF'])){
			$listURL = $_SERVER['HTTP_REFERER'];
		}
		$html = manage::submitForm($inputInfo, $submitURL, $listURL, '新增', '');
		return ['新增金主帳號', $html];
	}

	public static function actionAddData(){
		$inv_phone = POST::phone('phone');
		$inv_password = POST::text('pass');
		$inv_email = POST::text('email');
		$inv_line_id = POST::text('line');
		$inv_program = POST::text('program');
		$inv_expiry_time = POST::datetime('expiry');
		$inv_card_quota = POST::int('card');
		$inv_short_quota = POST::int('short');
		$inv_remark = POST::text('remark');

		$info = [
			'inv_phone' => $inv_phone,
			'inv_password' => password_hash($inv_password, PASSWORD_BCRYPT),
			'inv_email' => $inv_email,
			'inv_line_id' => $inv_line_id,
			'inv_program' => $inv_program,
			'inv_expiry_time' => $inv_expiry_time,
			'inv_card_quota' => $inv_card_quota,
			'inv_short_quota' => $inv_short_quota,
			'inv_remark' => $inv_remark,
			'inv_create_time' => date("Y-m-d H:i:s"),
			'inv_last_login' => date("Y-m-d H:i:s"),
		];

		$sqlStatus = SQL::insert('investor', $info);
		if($sqlStatus) {
			model::setLog('manage', '新增金主(' . $inv_phone . ')資料', $info);
			exit('success');
		} else {
			model::setLog('error', 'manage-新增金主資料時發生錯誤', $info);
			model::sendLineToAdmin("manage-新增金主資料時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		die;
	}

	public static function editData() {
		$id = Router::getParameter(4);
		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_id` = ? AND `inv_delete_time` IS NULL", [$id] );
		if(!$investor) {
			header('Location: ' . siteRootUrl . 'manage/investor');
			exit;
		}

		$areaList = model::setArrayKey(self::$areaList);
		$areaList = array_merge(['all' => '全國'], $areaList);
		$cardTag = model::setArrayKey(cardTag);

		$cardHtml = '';
		$cardList = SQL::selectAll("SELECT * FROM `card` WHERE `inv_id` = ? AND `card_delete_time` IS NULL", [$id] );
		foreach ($cardList as $key => $card) {
			$cardImage = (is_file(cardPathAbs . $card['card_image']) && $card['card_image'] != '')? cardPathRel . $card['card_image']:noPhoto;
			$card['card_area'] = json_decode($card['card_area'], true);
			$card['card_tag'] = json_decode($card['card_tag'], true);

			$inputInfo = [
				['name' => 'list[]', 'type' => 'hidden', 'value' => $key ],

				['type' => 'html', 'value' => '<hr>'],
				
				['name' => 'cardID' . $key, 'type' => 'hidden', 'value' => $card['card_id'] ],

				['text' => '金主名片', 'type' => 'img', 'name' => 'card_image' . $key, 'width' => [12, 12, 12], 'value' => $cardImage ],

				['text' => '是否為VIP', 'type' => 'radio', 'name' => 'card_vip' . $key, 'width' => [6, 6, 12],
				'other' => 'requireda', 'value' => [['1' => '是', '0' => '否'], $card['card_vip']] ],

				['text' => '是否顯示', 'type' => 'radio', 'name' => 'card_show' . $key, 'width' => [6, 6, 12],
				'other' => 'requireda', 'value' => [['1' => '顯示', '0' => '隱藏'], $card['card_show']] ],

				['text' => '名片標題', 'type' => 'text', 'name' => 'card_title' . $key, 'width' => [3, 6, 12], 'other' => 'required',
				'placeholder' => '請輸入名片標題', 'value' => $card['card_title'] ],

				['text' => '圖片替代文字(alt)', 'type' => 'text', 'name' => 'card_image_alt' . $key, 'width' => [3, 6, 12], 'other' => 'required',
				'placeholder' => '請輸入圖片替代文字', 'value' => $card['card_image_alt'] ],

				['text' => '圖片標題(title)', 'type' => 'text', 'name' => 'card_image_title' . $key, 'width' => [3, 6, 12], 'other' => 'required',
				'placeholder' => '請輸入圖片標題', 'value' => $card['card_image_title'] ],

				['text' => '到期時間', 'type' => 'datetime', 'name' => 'card_expiry_time' . $key, 'width' => [3, 6, 12], 'other' => 'required',
				'value' => $card['card_expiry_time'] ],

				['text' => '自動顯示時間', 'type' => 'datetime', 'name' => 'card_listing' . $key, 'width' => [3, 6, 12], 'value' => $card['card_listing'] ],

				['text' => '自動隱藏時間', 'type' => 'datetime', 'name' => 'card_delisting' . $key, 'width' => [3, 6, 12], 'value' => $card['card_delisting'] ],

				['text' => '每日置頂次數', 'type' => 'number', 'name' => 'card_refresh' . $key, 'width' => [3, 6, 12], 'other' => 'required',
				'placeholder' => '請輸入該名片每日置頂次數', 'value' => $card['card_refresh'] ],

				['text' => '刊登地區上限', 'type' => 'number', 'name' => 'card_area_quota' . $key, 'width' => [3, 6, 12], 'other' => 'required',
				'placeholder' => '請輸入該名片刊登地區上限', 'value' => $card['card_area_quota'] ],

				['text' => '刊登地區', 'type' => 'checkbox', 'name' => 'card_area' . $key, 'width' => [12, 12, 12],
				'value' => [$areaList, $card['card_area']], 'other' => 'class="areaArea"' ],

				['text' => '服務項目', 'type' => 'checkbox', 'name' => 'card_tag' . $key, 'width' => [12, 12, 12],
				'value' => [$cardTag, $card['card_tag']] ],

				['text' => '姓名/暱稱', 'type' => 'text', 'name' => 'card_contact' . $key, 'width' => [3, 6, 12], 'other' => 'required',
				'placeholder' => '請輸入姓名/暱稱', 'value' => $card['card_contact'] ],

				['text' => '電話號碼 1', 'type' => 'text', 'name' => 'card_phone_main' . $key, 'width' => [3, 6, 12], 'other' => 'required',
				'placeholder' => '請輸入電話號碼 1', 'value' => $card['card_phone_main'] ],

				['text' => '電話號碼 2', 'type' => 'text', 'name' => 'card_phone_spare' . $key, 'width' => [3, 6, 12],
				'placeholder' => '請輸入電話號碼 2', 'value' => $card['card_phone_spare'] ],

				['text' => 'Line ID', 'type' => 'text', 'name' => 'card_line_id' . $key, 'width' => [3, 6, 12],
				'placeholder' => '請輸入Line ID', 'value' => $card['card_line_id'] ],

				['text' => '名片內容', 'type' => 'textarea', 'name' => 'card_content' . $key, 'width' => [12, 12, 12],
				'placeholder' => '名片內容', 'value' => $card['card_content']],

				['text' => '名片備註', 'type' => 'textarea', 'name' => 'card_remark' . $key, 'width' => [12, 12, 12],
				'placeholder' => '名片備註；僅管理員觀看', 'value' => $card['card_remark']],
			];

			$cardHtml .= manage::getInputHtml($inputInfo);
		}

		$addCardHtml = '<div class="col-md-12">
							<a href="' . siteRootUrl . 'manage/card/addData?invID=' . $id . '" class="btn icon_btn plus">新增名片</a>
						</div>';

		$inputInfo = [
			['name' => 'id', 'type' => 'hidden', 'value' => $id ],

			['text' => '金主帳號', 'type' => 'text', 'name' => 'phone', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入金主帳號(手機號碼)', 'value' => $investor['inv_phone'] ],

			['text' => '金主密碼', 'type' => 'text', 'name' => 'pass', 'width' => [3, 6, 12],
			'placeholder' => '如不修改請勿輸入', 'value' => '' ],

			['text' => 'Email', 'type' => 'text', 'name' => 'email', 'width' => [3, 6, 12],
			'placeholder' => '請輸入Email', 'value' => $investor['inv_email'] ],

			['text' => 'Line ID', 'type' => 'text', 'name' => 'line', 'width' => [3, 6, 12],
			'placeholder' => '請輸入Line ID', 'value' => $investor['inv_line_id'] ],

			['text' => '方案名稱', 'type' => 'text', 'name' => 'program', 'width' => [3, 6, 12],
			'placeholder' => '請輸入方案名稱', 'value' => $investor['inv_program'] ],

			['text' => '帳號到期日', 'type' => 'datetime', 'name' => 'expiry', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請選擇方案到期日', 'value' => $investor['inv_expiry_time'] ],

			['text' => '開通名片數量', 'type' => 'number', 'name' => 'card', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入開通的名片數量', 'value' => $investor['inv_card_quota'] ],

			['text' => '簡訊餘額', 'type' => 'number', 'name' => 'short', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入目前簡訊餘額', 'value' => $investor['inv_short_quota'] ],

			['text' => '金主備註', 'type' => 'textarea', 'name' => 'remark', 'width' => [12, 12, 12],
			'placeholder' => '金主備註；僅管理員觀看', 'value' => $investor['inv_remark'] ],

			['type' => 'html', 'value' => $addCardHtml],

			['type' => 'html', 'value' => $cardHtml]
		];

		$submitURL = siteRootUrl . 'manage/investor/actionEditData';
		$listURL = siteRootUrl . 'manage/investor';
		if(strpos($_SERVER['HTTP_REFERER'], $_SERVER['HTTP_HOST'] . $_SERVER['PHP_SELF'])){
			$listURL = $_SERVER['HTTP_REFERER'];
		}
		$html = manage::submitForm($inputInfo, $submitURL, $listURL, '修改', '');


		return ['修改金主資料 - ID：' . $investor['inv_id'] . ' (' . $investor['inv_phone'] . ')', $html];
	}

	public static function actionEditData(){
		$id = POST::text('id');
		$inv_phone = POST::phone('phone');
		$inv_password = POST::text('pass');
		$inv_email = POST::text('email');
		$inv_line_id = POST::text('line');
		$inv_program = POST::text('program');
		$inv_expiry_time = POST::datetime('expiry');
		$inv_card_quota = POST::int('card');
		$inv_short_quota = POST::int('short');
		$inv_remark = POST::text('remark');

		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_id` = ? AND `inv_delete_time` IS NULL", [$id] );
		if(!$investor) die('查無該金主資料');

		SQL::begin();

		$info = [
			'inv_phone' => $inv_phone,
			'inv_email' => $inv_email,
			'inv_line_id' => $inv_line_id,
			'inv_program' => $inv_program,
			'inv_expiry_time' => $inv_expiry_time,
			'inv_card_quota' => $inv_card_quota,
			'inv_short_quota' => $inv_short_quota,
			'inv_remark' => $inv_remark,
			'inv_update_time' => date("Y-m-d H:i:s")
		];
		if($inv_password != '') {
			$info['inv_password'] = password_hash($inv_password, PASSWORD_BCRYPT);
		}

		$sqlStatus = SQL::update('investor', $info, ['inv_id' => $id]);
		if($sqlStatus) {
			model::setLog('manage', '修改金主(' . $investor['inv_phone'] . ')資料；原資料備份', $investor);
		} else {
			SQL::rollback();
			model::setLog('error', 'manage-修改金主資料時發生錯誤', $info);
			model::sendLineToAdmin("manage-修改金主資料時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}

		$list = POST::array('list');
		if(is_array($list)) {
			foreach ($list as $lsitID) {
				$card_id = POST::int('cardID' . $lsitID);
				$card_vip = POST::int('card_vip' . $lsitID);
				$card_show = POST::int('card_show' . $lsitID);
				$card_title = POST::text('card_title' . $lsitID);
				$card_image_alt = POST::text('card_image_alt' . $lsitID);
				$card_image_title = POST::text('card_image_title' . $lsitID);
				$card_expiry_time = POST::datetime('card_expiry_time' . $lsitID);
				$card_listing = POST::datetime('card_listing' . $lsitID);
				$card_delisting = POST::datetime('card_delisting' . $lsitID);
				$card_refresh = POST::int('card_refresh' . $lsitID);
				$card_area_quota = POST::int('card_area_quota' . $lsitID);
				$card_area = POST::array('card_area' . $lsitID);
				$card_tag = POST::array('card_tag' . $lsitID);
				$card_contact = POST::text('card_contact' . $lsitID);
				$card_phone_main = POST::text('card_phone_main' . $lsitID);
				$card_phone_spare = POST::text('card_phone_spare' . $lsitID);
				$card_line_id = POST::text('card_line_id' . $lsitID);
				$card_content = POST::text('card_content' . $lsitID);
				$card_remark = POST::text('card_remark' . $lsitID);

				$card_listing = date("Y-m-d H:00:00", strtotime($card_listing));
				$card_delisting = date("Y-m-d H:00:00", strtotime($card_delisting));

				if(count($card_area) > $card_area_quota) $card_area_quota = count($card_area);

				if(array_search('all', $card_area) !== false) unset($card_area[array_search('all', $card_area)]);
				$card_area = json_encode($card_area, JSON_UNESCAPED_UNICODE);
				$card_tag = json_encode($card_tag, JSON_UNESCAPED_UNICODE);

				$card = SQL::selectOne("SELECT * FROM `card` WHERE `card_id` = ?", [$card_id] );
				if(!$card) die('查無該名片');

				$info = [
					'card_vip' => $card_vip,
					'card_show' => $card_show,
					'card_title' => $card_title,
					'card_image_alt' => $card_image_alt,
					'card_image_title' => $card_image_title,
					'card_expiry_time' => $card_expiry_time,
					'card_listing' => $card_listing,
					'card_delisting' => $card_delisting,
					'card_refresh' => $card_refresh,
					'card_area_quota' => $card_area_quota,
					'card_area' => $card_area,
					'card_tag' => $card_tag,
					'card_contact' => $card_contact,
					'card_phone_main' => $card_phone_main,
					'card_phone_spare' => $card_phone_spare,
					'card_line_id' => $card_line_id,
					'card_content' => $card_content,
					'card_remark' => $card_remark,
					'card_update_time' => date("Y-m-d H:i:s")
				];

				if($_FILES['card_image' . $lsitID]['name'] != '') {
					$cardImage = model::fileUpload(cardPathAbs, $_FILES['card_image' . $lsitID], date("Y-m-d_H_i_s"), true);
					if(!$cardImage){
						model::setLog('error', 'manage-修改名片圖片發生錯誤', $_FILES['card_image' . $lsitID]);
						model::sendLineToAdmin("manage-修改名片圖片發生錯誤\r\n" . siteRootUrl);
					die('圖片上傳發生錯誤');
					} else {
						$file = cardPathAbs . $cardImage;
						list($width, $height, $type, $attr) = getimagesize($file);
						$zoom = (round(730 / $width, 6) > 1)? 1:round(730 / $width, 6);
						$image = (new imgcompress($file, $zoom))->compressImg($file);
						list($width, $height, $type, $attr) = getimagesize($file);
						if($width > 250){
							$zoom = (round(250 / $width, 6) > 1)? 1:round(250 / $width, 6);
							$newFileName = explode('.', $cardImage);
							$newFileName = cardPathAbs . $newFileName[0] . '_m.' . $newFileName[1];
							$image = (new imgcompress($file, $zoom))->compressImg($newFileName);
						}
						$info['card_image'] = $cardImage;
					}
				}

				$sqlStatus = SQL::update('card', $info, ['card_id' => $card_id]);
				if($sqlStatus) {
					model::setLog('manage', '修改名片(' . $card['card_id'] . ')；原資料備份', $card);
				} else {
					SQL::rollback();
					model::setLog('error', 'manage-修改名片時發生錯誤', $info);
					model::sendLineToAdmin("manage-修改名片時發生錯誤\r\n" . siteRootUrl);
					die('資料儲存時發生錯誤');
				}
			}
		}
		if($sqlStatus) {
			SQL::commit();
			exit('success');
		}
		die;
	}

	public static function changeUser() {
		$invID = Router::getParameter(4);
		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_id` = ? AND `inv_delete_time` IS NULL", [$invID]);
		if(!$investor) die(json_encode( ['status' => 'warning', 'message' => '查無金主資料'] ));
		model::setLog('manage', '管理者切換金主(' . $investor['inv_phone'] . ')帳號', []);
		unset ($_SESSION['investor']);
		unset ($_SESSION['custom']);
		$_SESSION['investor'] = $investor['inv_id'];
		$_SESSION['investor_vip'] = $investor['inv_vip'];
		header('Location: ' . siteRootUrl);
		exit;
	}

	public static function deleteData(){
		$invID = Router::getParameter(4);
		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_id` = ? AND `inv_delete_time` IS NULL", [$invID]);
		if(!$investor) die(json_encode( ['status' => 'warning', 'message' => '查無金主資料'] ));

		SQL::begin();

		$sqlStatus = SQL::update('investor', ['inv_delete_time' => date("Y-m-d H:i:s")], ['inv_id' => $invID ] );
		if(!$sqlStatus){
			SQL::rollback();
			model::setLog('error', 'manage-刪除金主時發生錯誤', []);
			model::sendLineToAdmin("manage-刪除金主時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		$sqlStatus = SQL::update('card', ['card_delete_time' => date("Y-m-d H:i:s")], ['inv_id' => $invID ] );
		if(!$sqlStatus){
			SQL::rollback();
			model::setLog('error', 'manage-刪除金主 一併刪除名片時發生錯誤', []);
			model::sendLineToAdmin("manage-刪除金主 一併刪除名片時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		$sqlStatus = SQL::update('card_comment', ['cc_delete_time' => date("Y-m-d H:i:s")], ['cc_identity' => 'investor','cc_identity_id' => $invID ] );
		if(!$sqlStatus){
			SQL::rollback();
			model::setLog('error', 'manage-刪除金主 一併刪除名片留言時發生錯誤', []);
			model::sendLineToAdmin("manage-刪除金主 一併刪除名片留言時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		$sqlStatus = SQL::update('wish_comment', ['wc_delete_time' => date("Y-m-d H:i:s")], ['wc_identity' => 'investor','wc_identity_id' => $invID ] );
		if(!$sqlStatus){
			SQL::rollback();
			model::setLog('error', 'manage-刪除金主 一併刪除借錢需求留言時發生錯誤', []);
			model::sendLineToAdmin("manage-刪除金主 一併刪除借錢需求留言時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}

		SQL::commit();
		model::setLog('manage', '刪除金主(' . $investor['inv_phone'] . ')', $investor);
		exit('success');
	}
}
?>