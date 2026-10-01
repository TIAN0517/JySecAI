<?php 
class page {
	public static function pageScript() { }

	public static function pageStyle() { }

	public static function pageContent() {
		$amount = 30;
		$cus_id = (GET::text('id') == '')? '%':GET::text('id');
		$cus_phone = GET::text('phone');
		$cus_name = GET::text('name');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `custom`
				WHERE (`custom`.`cus_id` LIKE '{$cus_id}')
				AND (`custom`.`cus_phone` LIKE '%{$cus_phone}%')
				AND (`custom`.`cus_name` LIKE '%{$cus_name}%')
				AND `cus_delete_time` IS NULL
				ORDER BY `custom`.`cus_id` DESC";
		$total = SQL::selectTotal($sql);
		$getUrl =  str_replace('&page=' . $page , '', $_SERVER['QUERY_STRING']);
		$url = '?' . $getUrl . '&page=';
		$pageLink = manage::pagingLink($url, $page, $total, $amount);
		$query = SQL::selectPage($sql, $amount, $page);

		$tableInfo = [];
		$tableHead = [
			['width' => '70', 'text' => '禁用'],
			['width' => '70', 'text' => 'ID'],
			['width' => '150', 'text' => '借客帳號'],
			['width' => '200', 'text' => '借客名稱'],
			['width' => '120', 'text' => 'Line ID'],
			['width' => '150', 'text' => '最後登入時間'],
			['width' => '90', 'text' => ''],
		];
		
		if(count($query) == 0){
			$tableInfo[] = ['type' => 'nodata'];
		}else{
			foreach($query as $custom){
				$tableInfo[] = [
					'id' => $custom['cus_id'],
					['type' => 'ban', 'text' => $custom['cus_ban'], 'table' => 'custom', 'field' => 'cus_ban', 'idField' => 'cus_id'],
					['type' => 'center', 'text' => $custom['cus_id'] ],
					['type' => 'text', 'text' => $custom['cus_phone'] ],
					['type' => 'text', 'text' => $custom['cus_name'] ],
					['type' => 'text', 'text' => $custom['cus_line_id'] ],
					['type' => 'center', 'text' => $custom['cus_last_login'] ],
					['type' => 'function', 'info' => [
						['type' => 'edit', 'url' => siteRootUrl . 'manage/custom/editData/' . $custom['cus_id'] ],
						['type' => 'url', 'url' => siteRootUrl . 'manage/custom/changeUser/' . $custom['cus_id'],
							'title' => '切換登入帳號', 'text' => '<i class="fas fa-sign-in-alt"></i>'],
						['type' => 'delete', 'url' => siteRootUrl . 'manage/custom/deleteData/' . $custom['cus_id'] ],
					] ],
				];
			}
		}

		$inputInfo = [
			['type' => 'text', 'text' => '借客ID', 'name' => 'id', 'value' => GET::text('id'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => '借客帳號', 'name' => 'phone', 'value' => GET::text('phone'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => '借客名稱', 'name' => 'name', 'value' => GET::text('name'), 'width' => [4, 6, 6] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/custom');

		$html .= manage::tableList($tableHead, $tableInfo, [], $pageLink);

		return ['借客管理', $html];
	}

	public static function editData() {
		$id = Router::getParameter(4);
		$custom = SQL::selectOne("SELECT * FROM `custom` WHERE `cus_id` = ? AND `cus_delete_time` IS NULL", [$id] );
		if(!$custom) {
			header('Location: ' . siteRootUrl . 'manage/custom');
			exit;
		}

		$inputInfo = [
			['name' => 'id', 'type' => 'hidden', 'value' => $id ],

			['text' => '借客帳號', 'type' => 'text', 'name' => 'phone', 'width' => [3, 6, 12],
			'placeholder' => '請輸入借客帳號(手機號碼)', 'value' => $custom['cus_phone'] ],

			['text' => '借客密碼', 'type' => 'text', 'name' => 'pass', 'width' => [3, 6, 12],
			'placeholder' => '如不修改請勿輸入', 'value' => '' ],

			['text' => '借客名稱', 'type' => 'text', 'name' => 'name', 'width' => [3, 6, 12],
			'placeholder' => '請輸入借客名稱', 'value' => $custom['cus_name'] ],

			['text' => 'Line ID', 'type' => 'text', 'name' => 'line', 'width' => [3, 6, 12],
			'placeholder' => '請輸入Line ID', 'value' => $custom['cus_line_id'] ],

			['text' => '借客備註', 'type' => 'textarea', 'name' => 'remark', 'width' => [12, 12, 12],
			'placeholder' => '借客備註；僅管理員觀看', 'value' => $custom['cus_remark'] ],
		];

		$submitURL = siteRootUrl . 'manage/custom/actionEditData';
		$listURL = siteRootUrl . 'manage/custom';
		if(strpos($_SERVER['HTTP_REFERER'], $_SERVER['HTTP_HOST'] . $_SERVER['PHP_SELF'])){
			$listURL = $_SERVER['HTTP_REFERER'];
		}
		$html = manage::submitForm($inputInfo, $submitURL, $listURL, '修改', '');
		return ['修改借客資料 - ' . $custom['cus_phone'], $html];
	}

	public static function actionEditData(){
		$id = POST::text('id');
		$cus_phone = POST::phone('phone');
		$cus_password = POST::text('pass');
		$cus_name = POST::text('name');
		$cus_line_id = POST::text('line');
		$cus_remark = POST::text('remark');

		$custom = SQL::selectOne("SELECT * FROM `custom` WHERE `cus_id` = ? AND `cus_delete_time` IS NULL", [$id] );
		if(!$custom) die('查無該借客資料');

		$info = [
			'cus_phone' => $cus_phone,
			'cus_name' => $cus_name,
			'cus_line_id' => $cus_line_id,
			'cus_remark' => $cus_remark,
		];
		if($cus_password != '') {
			$info['cus_password'] = password_hash($cus_password, PASSWORD_BCRYPT);
		}

		$sqlStatus = SQL::update('custom', $info, ['cus_id' => $id]);
		if($sqlStatus) {
			model::setLog('manage', '修改資料借客(' . $custom['cus_phone'] . ')資料；原資料備份', $custom);
			exit('success');
		} else{
			model::setLog('error', 'manage-修改借客資料時發生錯誤', $info);
			model::sendLineToAdmin("manage-修改借客資料時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		die;
	}

	public static function changeUser() {
		$cusID = Router::getParameter(4);
		$custom = SQL::selectOne("SELECT * FROM `custom` WHERE `cus_id` = ? AND `cus_delete_time` IS NULL", [$cusID]);
		if(!$custom) die(json_encode( ['status' => 'warning', 'message' => '查無借客資料'] ));
		model::setLog('manage', '管理者切換借客(' . $custom['cus_phone'] . ')帳號', []);
		unset ($_SESSION['investor']);
		unset ($_SESSION['custom']);
		$_SESSION['custom'] = $custom['cus_id'];
		header('Location: ' . siteRootUrl);
		exit;
	}

	public static function deleteData(){
		$cusID = Router::getParameter(4);
		$custom = SQL::selectOne("SELECT * FROM `custom` WHERE `cus_id` = ? AND `cus_delete_time` IS NULL", [$cusID]);
		if(!$custom) die(json_encode( ['status' => 'warning', 'message' => '查無借客資料'] ));

		SQL::begin();

		$sqlStatus = SQL::update('custom', ['cus_delete_time' => date("Y-m-d H:i:s")], ['cus_id' => $cusID ] );
		if(!$sqlStatus){
			SQL::rollback();
			model::setLog('error', 'manage-刪除借客時發生錯誤', []);
			model::sendLineToAdmin("manage-刪除借客時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		$sqlStatus = SQL::update('wish', ['wish_delete_time' => date("Y-m-d H:i:s")], ['cus_id' => $cusID ] );
		if(!$sqlStatus){
			SQL::rollback();
			model::setLog('error', 'manage-刪除借客 一併刪除借錢需求時發生錯誤', []);
			model::sendLineToAdmin("manage-刪除借客 一併刪除借錢需求時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		$sqlStatus = SQL::update('card_comment', ['cc_delete_time' => date("Y-m-d H:i:s")], ['cc_identity' => 'custom','cc_identity_id' => $cusID ] );
		if(!$sqlStatus){
			SQL::rollback();
			model::setLog('error', 'manage-刪除借客 一併刪除名片留言時發生錯誤', []);
			model::sendLineToAdmin("manage-刪除借客 一併刪除名片留言時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		$sqlStatus = SQL::update('wish_comment', ['wc_delete_time' => date("Y-m-d H:i:s")], ['wc_identity' => 'custom','wc_identity_id' => $cusID ] );
		if(!$sqlStatus){
			SQL::rollback();
			model::setLog('error', 'manage-刪除借客 一併刪除借錢需求留言時發生錯誤', []);
			model::sendLineToAdmin("manage-刪除借客 一併刪除借錢需求留言時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}

		SQL::commit();
		model::setLog('manage', '刪除借客(' . $custom['cus_phone'] . ')', $custom);
		exit('success');
	}
}
?>