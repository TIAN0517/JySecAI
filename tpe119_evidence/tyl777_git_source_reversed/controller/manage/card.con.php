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

	public static function pageStyle() { }

	public static function pageContent() {
		$amount = 20;
		$id = (GET::text('id') == '')? '%':GET::text('id');
		$card_title = GET::text('title');
		$phone = GET::text('phone');
		$card_area = GET::text('area');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `card`
		JOIN `investor` ON `card`.`inv_id` = `investor`.`inv_id`
		WHERE (`card`.`card_id` LIKE '{$id}')
		AND (`card`.`card_title` LIKE '%{$card_title}%')
		AND (`card`.`card_phone_main` LIKE '%{$phone}%' OR `card`.`card_phone_spare` LIKE '%{$phone}%')
		AND (`card`.`card_area` LIKE '%{$card_area}%')
		AND `card_delete_time` IS NULL
		ORDER BY `card`.`card_id` DESC";
		$total = SQL::selectTotal($sql);
		$getUrl =  str_replace('&page=' . $page , '', $_SERVER['QUERY_STRING']);
		$url = '?' . $getUrl . '&page=';
		$pageLink = manage::pagingLink($url, $page, $total, $amount);
		$query = SQL::selectPage($sql, $amount, $page);

		$tableInfo = [];
		$tableHead = [
			['width' => '70', 'text' => '顯示'],
			['width' => '70', 'text' => 'VIP'],
			['width' => '70', 'text' => '地區'],
			['width' => '200', 'text' => '名片'],
			['width' => '150', 'text' => '金主資訊'],
			['width' => '200', 'text' => '標題'],
			['width' => '100', 'text' => '地區'],
			['width' => '150', 'text' => '到期時間'],
			['width' => '50', 'text' => ''],
		];
		$functionBtn = [ ];
		if(count($query) == 0){
			$tableInfo[] = ['type' => 'nodata'];
		}else{
			foreach($query as $card){
				$cardPic = (is_file(cardPathAbs . $card['card_image']) && $card['card_image'] != '')? cardPathRel . $card['card_image']:noPhoto;
				$areaText = implode(',', json_decode($card['card_area'], true));
				$showText = ['type' => 'show', 'text' => $card['card_show'], 'table' => 'card', 'field' => 'card_show', 'idField' => 'card_id'];
				if(strtotime($card['card_expiry_time']) < time()) $showText = ['type' => 'center', 'text' => '已過期' ];
				$warn = '';
				if(strtotime($card['inv_expiry_time']) < time()) $warn = '帳號已過期';
				
				$tableInfo[] = [
					'id' => $card['card_id'],
					$showText,
					['type' => 'checkbox', 'text' => $card['card_vip'], 'table' => 'card', 'field' => 'card_vip', 'idField' => 'card_id'],
					['type' => 'checkbox', 'text' => $card['card_normal'], 'table' => 'card', 'field' => 'card_normal', 'idField' => 'card_id'],
					['type' => 'img', 'text' => $cardPic, 'height' => '107', 'width' => '190'],
					['type' => 'text', 'text' => '帳號：' . $card['inv_phone'] . '<br>Line：' . $card['card_line_id'], 'warn' => $warn ],
					['type' => 'text', 'text' => 'ID：' . $card['card_id'] . '<br>' . $card['card_title'] ],
					['type' => 'text', 'text' => $areaText ],
					['type' => 'center', 'text' => $card['card_expiry_time'] ],
					['type' => 'function', 'info' => [
						['type' => 'url', 'url' => siteRootUrl . 'card/' . $card['card_id'], 'new' => true ],
						['type' => 'edit', 'url' => siteRootUrl . 'manage/card/editData/' . $card['card_id'] ],
					] ],
				];
			}
		}

		$areaList = model::setArrayKey(self::$areaList);
		$areaList = array_merge(['' => '全國地區'], $areaList);

		$inputInfo = [
			['type' => 'select', 'text' => '地區', 'name' => 'area', 'value' => [$areaList, GET::text('area') ], 'width' => [3, 6, 6] ],
			['type' => 'text', 'text' => '名片ID', 'name' => 'id', 'value' => GET::text('id'), 'width' => [3, 6, 6] ],
			['type' => 'text', 'text' => '名片標題', 'name' => 'title', 'value' => GET::text('title'), 'width' => [3, 6, 6] ],
			['type' => 'text', 'text' => '連絡電話', 'name' => 'phone', 'value' => GET::text('phone'), 'width' => [3, 6, 6] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/card');

		$html .= manage::tableList($tableHead, $tableInfo, $functionBtn, $pageLink);

		return ['名片管理', $html];
	}

	public static function addData() {
		$areaList = model::setArrayKey(self::$areaList);
		$areaList = array_merge(['all' => '全國'], $areaList);
		$cardTag = model::setArrayKey(cardTag);

		$invID = GET::int('invID');
		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_id` = ? AND `inv_delete_time` IS NULL", [$invID] );
		
		$inputInfo = [
			['text' => '金主資料', 'type' => 'label', 'width' => [12, 12, 12], 'other' => 'required',
			'value' => 'ID：' . $investor['inv_id'] . ' (' . $investor['inv_phone'] . ')' ],

			['text' => '金主名片', 'type' => 'img', 'name' => 'card_image', 'width' => [12, 12, 12], 'other' => 'required' ],

			['text' => '是否為VIP', 'type' => 'radio', 'name' => 'card_vip', 'width' => [6, 6, 12],
			'other' => 'requireda', 'value' => [['1' => '是', '0' => '否'], 0] ],

			['text' => '是否顯示', 'type' => 'radio', 'name' => 'card_show' . $key, 'width' => [6, 6, 12],
				'other' => 'requireda', 'value' => [['1' => '顯示', '0' => '隱藏'], 1] ],

			['name' => 'inv_id', 'type' => 'hidden', 'value' => $invID ],

			['text' => '名片標題', 'type' => 'text', 'name' => 'card_title', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入名片標題' ],

			['text' => '圖片替代文字(alt)', 'type' => 'text', 'name' => 'card_image_alt', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入圖片替代文字' ],

			['text' => '圖片標題(title)', 'type' => 'text', 'name' => 'card_image_title', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入圖片標題' ],

			['text' => '到期時間', 'type' => 'datetime', 'name' => 'card_expiry_time', 'width' => [3, 6, 12], 'other' => 'required',
			'value' => date("Y-m-d H:i:s")],

			['text' => '自動顯示時間', 'type' => 'datetime', 'name' => 'card_listing', 'width' => [3, 6, 12] ],

			['text' => '自動隱藏時間', 'type' => 'datetime', 'name' => 'card_delisting', 'width' => [3, 6, 12] ],

			['text' => '每日置頂次數', 'type' => 'number', 'name' => 'card_refresh', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入該名片每日置頂次數', 'value' => 1 ],

			['text' => '刊登地區上限', 'type' => 'number', 'name' => 'card_area_quota', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入該名片刊登地區上限', 'value' => 3 ],

			['text' => '刊登地區', 'type' => 'checkbox', 'name' => 'card_area', 'width' => [12, 12, 12],
			'value' => [$areaList, []], 'other' => 'class="areaArea"' ],

			['text' => '服務項目', 'type' => 'checkbox', 'name' => 'card_tag', 'width' => [12, 12, 12],
			'value' => [$cardTag, []] ],

			['text' => '姓名/暱稱', 'type' => 'text', 'name' => 'card_contact', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入姓名/暱稱' ],

			['text' => '電話號碼 1', 'type' => 'text', 'name' => 'card_phone_main', 'width' => [3, 6, 12],
			'placeholder' => '請輸入電話號碼 1' ],

			['text' => '電話號碼 2', 'type' => 'text', 'name' => 'card_phone_spare', 'width' => [3, 6, 12],
			'placeholder' => '請輸入電話號碼 2' ],

			['text' => 'Line ID', 'type' => 'text', 'name' => 'card_line_id', 'width' => [3, 6, 12],
			'placeholder' => '請輸入Line ID' ],

			['text' => '名片內容', 'type' => 'textarea', 'name' => 'card_content', 'width' => [12, 12, 12],
			'placeholder' => '名片內容'],

			['text' => '名片備註', 'type' => 'textarea', 'name' => 'card_remark', 'width' => [12, 12, 12],
			'placeholder' => '名片備註；僅管理員觀看'],
		];

		$submitURL = siteRootUrl . 'manage/card/actionAddData';
		$listURL = siteRootUrl . 'manage/card';
		$html = manage::submitForm($inputInfo, $submitURL, $listURL, '新增名片', '');
		return ['新增金主[ID：' . $investor['inv_id'] . ' (' . $investor['inv_phone'] . ')]名片', $html];
	}
	
	public static function actionAddData() {
		$card_vip = POST::int('card_vip');
		$card_show = POST::int('card_show');
		$inv_id = POST::int('inv_id');
		$card_title = POST::text('card_title');
		$card_image_alt = POST::text('card_image_alt');
		$card_image_title = POST::text('card_image_title');
		$card_expiry_time = POST::datetime('card_expiry_time');
		$card_listing = POST::datetime('card_listing');
		$card_delisting = POST::datetime('card_delisting');
		$card_refresh = POST::int('card_refresh');
		$card_area_quota = POST::int('card_area_quota');
		$card_area = POST::array('card_area');
		$card_tag = POST::array('card_tag');
		$card_contact = POST::text('card_contact');
		$card_phone_main = POST::text('card_phone_main');
		$card_phone_spare = POST::text('card_phone_spare');
		$card_line_id = POST::text('card_line_id');
		$card_content = POST::text('card_content');
		$card_remark = POST::text('card_remark');

		$card_listing = date("Y-m-d H:00:00", strtotime($card_listing));
		$card_delisting = date("Y-m-d H:00:00", strtotime($card_delisting));

		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_id` = ? AND `inv_delete_time` IS NULL", [$inv_id] );
		if(!$investor) die('查無該金主資料');

		$cardCurrent = investor::cardCurrent($inv_id);
		if($cardCurrent + 1 > $investor['inv_card_quota'] ) {
			$sqlStatus = SQL::update('investor', ['inv_card_quota' => $cardCurrent + 1], ['inv_id' => $inv_id] );
			if($sqlStatus) {
				model::setLog('manage', '自動增加金主(' . $investor['inv_phone'] . ')名片上限', ['inv_card_quota' => $cardCurrent + 1]);
			} else {
				model::setLog('error', 'manage-自動增加金主名片上限發生錯誤', $info);
				model::sendLineToAdmin("manage-自動增加金主名片上限發生錯誤\r\n" . siteRootUrl);
				die('增加金主名片上限發生錯誤');
			}
		}

		if(count($card_area) > $card_area_quota) $card_area_quota = count($card_area);
		/*
		$otherCardAreaQuantity = investor::otherCardAreaQuantity($inv_id, null);
		if($otherCardAreaQuantity + count($card_area) > $investor['inv_area_quota']) {
			$sqlStatus = SQL::update('investor', ['inv_area_quota' => $otherCardAreaQuantity + count($card_area)], ['inv_id' => $inv_id] );
			if($sqlStatus) {
				model::setLog('manage', '自動增加金主(' . $investor['inv_phone'] . ')地區上限', ['inv_area_quota' => $otherCardAreaQuantity + count($card_area)]);
			} else {
				model::setLog('error', 'manage-自動增加金主地區上限發生錯誤', $info);
				model::sendLineToAdmin("manage-自動增加金主地區上限發生錯誤\r\n" . siteRootUrl);
				die('自動增加金主地區上限發生錯誤');
			}
		}
		*/

		if($_FILES['card_image']['name'] == '' ) die('請上傳名片圖片');
		$cardImage = model::fileUpload(cardPathAbs, $_FILES['card_image'], date("Y-m-d_H_i_s"), true);
		if(!$cardImage){
			model::setLog('error', 'manage-新增名片圖片發生錯誤', $_POST);
			model::sendLineToAdmin("manage-新增名片圖片發生錯誤\r\n" . siteRootUrl);
			die('圖片上傳發生錯誤');
		} else {
			$file = cardPathAbs . $cardImage;
			list($width, $height, $type, $attr) = getimagesize($file);
			$zoom = (round(730 / $width, 6) > 1)? 1:round(730 / $width, 6);
			$image = (new imgcompress($file, $zoom))->compressImg($file);
			list($width, $height, $type, $attr) = getimagesize($file);
			if($width > 319){
				$zoom = (round(250 / $width, 6) > 1)? 1:round(250 / $width, 6);
				$newFileName = explode('.', $cardImage);
				$newFileName = cardPathAbs . $newFileName[0] . '_m.' . $newFileName[1];
				$image = (new imgcompress($file, $zoom))->compressImg($newFileName);
			}
		}

		if(array_search('all', $card_area) !== false) unset($card_area[array_search('all', $card_area)]);
		$card_area = json_encode($card_area, JSON_UNESCAPED_UNICODE);
		$card_tag = json_encode($card_tag, JSON_UNESCAPED_UNICODE);
		
		$info = [
			'card_vip' => $card_vip,
			'card_show' => $card_show,
			'inv_id' => $inv_id,
			'card_image' => $cardImage,
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
			'card_create_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::insert('card', $info);

		if($sqlStatus) {
			$cardID = SQL::autoID();
			model::setLog('manage', '新增平片(' . $cardID . ')', $info);
			exit('success');
		} else {
			model::setLog('error', 'manage-新增名片時發生錯誤', $info);
			model::sendLineToAdmin("manage-新增名片時發生錯誤\r\n" . siteRootUrl);
			die('資料新增時發生錯誤');
		}
		exit;
	}

	public static function editData() {
		$id = Router::getParameter(4);
		$card = SQL::selectOne("SELECT * FROM `card` WHERE `card_id` = ? AND `card_delete_time` IS NULL", [$id] );
		if(!$card) {
			header('Location: ' . siteRootUrl . 'manage/card');
			exit;
		}

		$areaList = model::setArrayKey(self::$areaList);
		$areaList = array_merge(['all' => '全國'], $areaList);
		$cardTag = model::setArrayKey(cardTag);

		$cardImage = (is_file(cardPathAbs . $card['card_image']) && $card['card_image'] != '')? cardPathRel . $card['card_image']:noPhoto;

		$card['card_area'] = json_decode($card['card_area'], true);
		$card['card_tag'] = json_decode($card['card_tag'], true);

		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_id` = ? AND `inv_delete_time` IS NULL", [$card['inv_id']] );
		
		$inputInfo = [
			['name' => 'id', 'type' => 'hidden', 'value' => $id ],

			['text' => '金主資料', 'type' => 'label', 'width' => [12, 12, 12], 'other' => 'required',
			'value' => 'ID：' . $investor['inv_id'] . ' (' . $investor['inv_phone'] . ')' ],

			['text' => '金主名片', 'type' => 'img', 'name' => 'card_image', 'width' => [12, 12, 12], 'value' => $cardImage ],

			['text' => '是否為VIP', 'type' => 'radio', 'name' => 'card_vip', 'width' => [6, 6, 12],
			'other' => 'requireda', 'value' => [['1' => '是', '0' => '否'], $card['card_vip']] ],

			['text' => '是否顯示', 'type' => 'radio', 'name' => 'card_show' . $key, 'width' => [6, 6, 12],
				'other' => 'requireda', 'value' => [['1' => '顯示', '0' => '隱藏'], $card['card_show']] ],

			['text' => '名片標題', 'type' => 'text', 'name' => 'card_title', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入名片標題', 'value' => $card['card_title'] ],

			['text' => '圖片替代文字(alt)', 'type' => 'text', 'name' => 'card_image_alt', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入圖片替代文字', 'value' => $card['card_image_alt'] ],

			['text' => '圖片標題(title)', 'type' => 'text', 'name' => 'card_image_title', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入圖片標題', 'value' => $card['card_image_title'] ],

			['text' => '到期時間', 'type' => 'datetime', 'name' => 'card_expiry_time', 'width' => [3, 6, 12], 'other' => 'required',
			'value' => $card['card_expiry_time'] ],

			['text' => '自動顯示時間', 'type' => 'datetime', 'name' => 'card_listing', 'width' => [3, 6, 12], 'value' => $card['card_listing'] ],

			['text' => '自動隱藏時間', 'type' => 'datetime', 'name' => 'card_delisting', 'width' => [3, 6, 12], 'value' => $card['card_delisting'] ],

			['text' => '每日置頂次數', 'type' => 'number', 'name' => 'card_refresh', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入該名片每日置頂次數', 'value' => $card['card_refresh'] ],

			['text' => '刊登地區上限', 'type' => 'number', 'name' => 'card_area_quota', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入該名片刊登地區上限', 'value' => $card['card_area_quota'] ],

			['text' => '刊登地區', 'type' => 'checkbox', 'name' => 'card_area', 'width' => [12, 12, 12],
			'value' => [$areaList, $card['card_area']], 'other' => 'class="areaArea"' ],

			['text' => '服務項目', 'type' => 'checkbox', 'name' => 'card_tag', 'width' => [12, 12, 12],
			'value' => [$cardTag, $card['card_tag']] ],

			['text' => '姓名/暱稱', 'type' => 'text', 'name' => 'card_contact', 'width' => [3, 6, 12], 'other' => 'required',
			'placeholder' => '請輸入姓名/暱稱', 'value' => $card['card_contact'] ],

			['text' => '電話號碼 1', 'type' => 'text', 'name' => 'card_phone_main', 'width' => [3, 6, 12],
			'placeholder' => '請輸入電話號碼 1', 'value' => $card['card_phone_main'] ],

			['text' => '電話號碼 2', 'type' => 'text', 'name' => 'card_phone_spare', 'width' => [3, 6, 12],
			'placeholder' => '請輸入電話號碼 2', 'value' => $card['card_phone_spare'] ],

			['text' => 'Line ID', 'type' => 'text', 'name' => 'card_line_id', 'width' => [3, 6, 12],
			'placeholder' => '請輸入Line ID', 'value' => $card['card_line_id'] ],

			['text' => '名片內容', 'type' => 'textarea', 'name' => 'card_content', 'width' => [12, 12, 12],
			'placeholder' => '名片內容', 'value' => $card['card_content']],

			['text' => '名片備註', 'type' => 'textarea', 'name' => 'card_remark', 'width' => [12, 12, 12],
			'placeholder' => '名片備註；僅管理員觀看', 'value' => $card['card_remark']],
		];

		$submitURL = siteRootUrl . 'manage/card/actionEditData';
		$listURL = siteRootUrl . 'manage/card';
		if(strpos($_SERVER['HTTP_REFERER'], $_SERVER['HTTP_HOST'] . $_SERVER['PHP_SELF'])){
			$listURL = $_SERVER['HTTP_REFERER'];
		}
		$html = manage::submitForm($inputInfo, $submitURL, $listURL, '修改名片', '');
		return array('修改金主名片 - ' . $card['card_id'], $html);
	}

	public static function actionEditData(){
		$id = POST::text('id');
		$card_vip = POST::int('card_vip');
		$card_show = POST::int('card_show');
		$card_title = POST::text('card_title');
		$card_image_alt = POST::text('card_image_alt');
		$card_image_title = POST::text('card_image_title');
		$card_expiry_time = POST::datetime('card_expiry_time');
		$card_listing = POST::datetime('card_listing');
		$card_delisting = POST::datetime('card_delisting');
		$card_refresh = POST::int('card_refresh');
		$card_area_quota = POST::int('card_area_quota');
		$card_area = POST::array('card_area');
		$card_tag = POST::array('card_tag');
		$card_contact = POST::text('card_contact');
		$card_phone_main = POST::text('card_phone_main');
		$card_phone_spare = POST::text('card_phone_spare');
		$card_line_id = POST::text('card_line_id');
		$card_content = POST::text('card_content');
		$card_remark = POST::text('card_remark');

		$card_listing = date("Y-m-d H:00:00", strtotime($card_listing));
		$card_delisting = date("Y-m-d H:00:00", strtotime($card_delisting));

		if(count($card_area) > $card_area_quota) $card_area_quota = count($card_area);
		/*
		$otherCardAreaQuantity = investor::otherCardAreaQuantity($inv_id, $id);
		if($otherCardAreaQuantity + count($card_area) > $investor['inv_area_quota']) {
			$sqlStatus = SQL::update('investor', ['inv_area_quota' => $otherCardAreaQuantity + count($card_area)], ['inv_id' => $inv_id] );
			if($sqlStatus) {
				model::setLog('manage', '自動增加金主(' . $investor['inv_phone'] . ')地區上限', ['inv_area_quota' => $otherCardAreaQuantity + count($card_area)]);
			} else {
				model::setLog('error', 'manage-自動增加金主地區上限發生錯誤', $info);
				model::sendLineToAdmin("manage-自動增加金主地區上限發生錯誤\r\n" . siteRootUrl);
				die('自動增加金主地區上限發生錯誤');
			}
		}
		*/

		if(array_search('all', $card_area) !== false) unset($card_area[array_search('all', $card_area)]);
		$card_area = json_encode($card_area, JSON_UNESCAPED_UNICODE);
		$card_tag = json_encode($card_tag, JSON_UNESCAPED_UNICODE);

		$card = SQL::selectOne("SELECT * FROM `card` WHERE `card_id` = ?", [$id] );
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

		if($_FILES['card_image']['name'] != ''){
			$cardImage = model::fileUpload(cardPathAbs, $_FILES['card_image'], date("Y-m-d_H_i_s"), true);
			if(!$cardImage){
				model::setLog('error', 'manage-修改名片圖片發生錯誤', $_POST);
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

		$sqlStatus = SQL::update('card', $info, ['card_id' => $id]);
		if($sqlStatus) {
			model::setLog('manage', '修改名片(' . $card['card_id'] . ')；原資料備份', $card);
			exit('success');
		} else {
			model::setLog('error', 'manage-修改名片時發生錯誤', $info);
			model::sendLineToAdmin("manage-修改名片時發生錯誤\r\n" . siteRootUrl);
			die('資料儲存時發生錯誤');
		}
		die;
	}
}
?>
