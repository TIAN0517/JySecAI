<?php
class action {
	public static function create() {
		$custom = custom::loginStatus();
		if(!$custom) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$title = POST::text('title');
		$area = POST::text('area');
		$money = POST::int('money');
		$collateral = POST::text('collateral');
		$job = POST::text('job');
		$contact = POST::text('contact');
		$explanation = POST::text('explanation');

		if(!$money || $money < 10000) exit(json_encode(['return' => 'error', 'msg' => '借款金額至少大於 10000']));
		if($money > 1000000000) exit(json_encode(['return' => 'error', 'msg' => '借款金額過高！']));
		if($title == '' || $area == '' || $collateral == '' || $job == '' || $contact == '') exit(json_encode(['return' => 'error', 'msg' => '請輸入必填欄位']));

		$info = [
			'cus_id' => $custom['cus_id'],
			'wish_title' => $title,
			'wish_area' => $area,
			'wish_money' => $money,
			'wish_collateral' => $collateral,
			'wish_job' => $job,
			'wish_explanation' => $explanation,
			'wish_contact_time' => $contact,
			'wish_create_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::insert('wish', $info);
		if($sqlStatus) {
			$wishId = SQL::autoID();
			model::setLog('custom', '顧客(' . $custom['cus_phone'] . ')發布借錢需求(' . $wishId . ')' , $info);
			systemEvent::createWish($wishId);
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '發布借錢需求時發生錯誤', $info);
			model::sendLineToAdmin("發布借錢需求時發生錯誤\r\n" . siteRootUrl);
		}
	}

	public static function borrowed() {
		$custom = custom::loginStatus();
		if(!$custom) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$id = POST::int('id');
		$wish = SQL::selectOne("SELECT * FROM `wish` WHERE `cus_id` = ? AND `wish_id` = ?", [ $custom['cus_id'], $id ]);
		if(!$wish) exit(json_encode(['return' => 'error', 'msg' => '查無該資料']));
		if($wish['wish_status'] == 1) exit(json_encode(['return' => 'error', 'msg' => '該需求已結案']));

		$info = [
			'wish_status' => 1,
			'wish_borrow_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('wish', $info, ['wish_id' => $id ] );
		if($sqlStatus) {
			$info['wish_id'] = $id;
			model::setLog('custom', '借錢需求(' . $id . ')結案', $info);
			exit( json_encode( ['return' => 'success']) );
		} else {
			$info['wish_id'] = $id;
			model::setLog('error', '借錢需求結案時發生錯誤', $info);
			model::sendLineToAdmin("借錢需求結案時發生錯誤\r\n" . siteRootUrl);
		}
	}

	public static function more() {
		$page = POST::int('page');
		$area = POST::text('area', '全國');
		$start = $page * 20;
		$haveNext = false;

		if($area != '全國' && array_key_exists($area, cityArea)) {
			$cityList = cityArea[$area];
			$citySQLText = implode(',', $cityList);
			$sqlCommand = "AND FIND_IN_SET(`wish`.`wish_area`, '" . $citySQLText . "')";
		}

		$wishList = SQL::selectAll("SELECT * FROM `wish` JOIN `custom` ON `custom`.`cus_id` = `wish`.`cus_id`
									WHERE `wish`.`wish_show` = 1 AND `wish`.`wish_delete_time` IS NULL
									AND `custom`.`cus_ban` = 0 AND `custom`.`cus_delete_time` IS NULL " . $sqlCommand . "
									ORDER BY `wish`.`wish_id` DESC LIMIT " . $start . " ,21");
		$wishInfo = [];
		foreach ($wishList as $key => $wish) {
			if($key == 20) break;
			$statusHtml = '等待<br>借款';
			$statusClass = 'need-wait';
			if($wish['wish_status'] == 1) {
				$statusHtml = '借款<br>成功';
				$statusClass = '';
			}
			$wishInfo[] = [
				'id' => $wish['wish_id'],
				'status' => $statusHtml,
				'class' => $statusClass,
				'money' => ((int)$wish['wish_money']/10000) . '萬',
				'title' => $wish['wish_title'],
				'collateral' => $wish['wish_collateral'],
				'area' => $wish['wish_area'],
				'time' => $wish['wish_create_time']
			];
		}

		if(count($wishList) > 20) $haveNext = true;
		exit( json_encode( ['more' => $haveNext, 'wish' => $wishInfo]) );
	}

	public static function areaSearch() {
		$page = POST::int('page', 0);
		$area = POST::text('area', '全國');
		$start = $page * 8;
		$haveNext = false;

		if($area != '全國' && array_key_exists($area, cityArea)) {
			$cityList = cityArea[$area];
			$citySQLText = implode(',', $cityList);
			$sqlCommand = "AND FIND_IN_SET(`wish`.`wish_area`, '" . $citySQLText . "')";
		}

		$wishList = SQL::selectAll("SELECT * FROM `wish` JOIN `custom` ON `custom`.`cus_id` = `wish`.`cus_id`
									WHERE `wish`.`wish_show` = 1 AND `wish`.`wish_delete_time` IS NULL
									AND `custom`.`cus_ban` = 0 AND `custom`.`cus_delete_time` IS NULL " . $sqlCommand . "
									ORDER BY `wish`.`wish_id` DESC LIMIT " . $start . " ,9");
		$wishInfo = [];
		foreach ($wishList as $key => $wish) {
			if($key == 8) break;
			$statusHtml = '等待<br>借款';
			$statusClass = 'need-wait';
			if($wish['wish_status'] == 1) {
				$statusHtml = '借款<br>成功';
				$statusClass = '';
			}
			$wishInfo[] = [
				'id' => $wish['wish_id'],
				'status' => $statusHtml,
				'class' => $statusClass,
				'money' => ((int)$wish['wish_money']/10000) . '萬',
				'title' => $wish['wish_title'],
				'collateral' => $wish['wish_collateral'],
				'area' => $wish['wish_area'],
				'time' => $wish['wish_create_time']
			];
		}

		if(count($wishList) > 8) $haveNext = true;
		exit( json_encode( ['more' => $haveNext, 'wish' => $wishInfo, 'area' => $area]) );
	}

	public static function getPhone() {
		if( !isset($_SESSION['investor']) && (!isset($_SESSION['custom']) ||$_SESSION['custom'] != $wish['cus_id'] ) ) {
			exit(json_encode(['return' => 'error', 'msg' => '登入金主看更多...']));
		}

		$id = POST::int('id');
		$code = POST::text('code');
		if($code != $_SESSION['wishCode']) exit(json_encode(['return' => 'error', 'msg' => '無法取得資訊']));
		$wish = SQL::selectOne("SELECT * FROM `wish` JOIN `custom` ON `custom`.`cus_id` = `wish`.`cus_id`
								WHERE `wish`.`wish_id` = ? AND `wish`.`wish_delete_time` IS NULL AND `wish`.`wish_show` = 1", [$id]);
		if(!$wish) exit(json_encode(['return' => 'error', 'msg' => '查無該資料']));
		if($wish['wish_status'] == 1) exit(json_encode(['return' => 'error', 'msg' => '該需求已結案']));
		exit( json_encode( ['return' => 'success', 'phone' => $wish['cus_phone'] ]) );
	}

	public static function getLineID() {
		if( !isset($_SESSION['investor']) && (!isset($_SESSION['custom']) ||$_SESSION['custom'] != $wish['cus_id'] ) ) {
			exit(json_encode(['return' => 'error', 'msg' => '登入金主看更多...']));
		}

		$id = POST::int('id');
		$code = POST::text('code');
		$wish = SQL::selectOne("SELECT * FROM `wish` JOIN `custom` ON `custom`.`cus_id` = `wish`.`cus_id`
								WHERE `wish`.`wish_id` = ? AND `wish`.`wish_delete_time` IS NULL AND `wish`.`wish_show` = 1", [$id]);
		if(!$wish) exit(json_encode(['return' => 'error', 'msg' => '查無該資料']));
		if($wish['wish_status'] == 1) exit(json_encode(['return' => 'error', 'msg' => '該需求已結案']));
		if($wish['cus_line_id'] != '') exit( json_encode( ['return' => 'success', 'line' => $wish['cus_line_id'] ]) );
		exit(json_encode(['return' => 'error', 'msg' => '未填寫']));
	}

	public static function reply() {
		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));
		$wishID = POST::int('id');
		$content = POST::text('content');
		$code = POST::text('code');

		if($code != $_SESSION['wishCode']) exit(json_encode(['return' => 'error', 'msg' => '目前無法留言']));
		if(strtotime($investor['inv_expiry_time']) < time()) exit(json_encode(['return' => 'error', 'msg' => '帳號已過期，請與客服人員聯繫']));

		$wish = SQL::selectOne("SELECT * FROM `wish` WHERE `wish_id` = ? AND `wish_delete_time` IS NULL AND `wish_show` = 1", [$wishID]);
		if(!$wish) exit(json_encode(['return' => 'error', 'msg' => '查無該借款需求']));

		$info = [
			'wc_show' => 1,
			'wc_status' => 0,
			'wish_id' => $wishID,
			'wc_level' => 1,
			'wc_main_id' => null,
			'wc_identity' => 'investor',
			'wc_identity_id' => $investor['inv_id'],
			'wc_message' => $content,
			'wc_create_time' => date("Y-m-d H:i:s")
		];

		$sqlStatus = SQL::insert('wish_comment', $info);
		if($sqlStatus) {
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')於借錢需求(' . $wishID . ')留言' , $info);
			systemEvent::wishReply($wish);
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '借錢需求留言時發生錯誤', $info);
			model::sendLineToAdmin("借錢需求留言時發生錯誤\r\n" . siteRootUrl);
		}
	}

	public static function comment() {
		$wcID = POST::int('id');
		$content = POST::text('content');
		$code = POST::text('code');

		if($code != $_SESSION['wishCode']) exit(json_encode(['return' => 'error', 'msg' => '目前無法留言']));

		$wishComment = SQL::selectOne("SELECT * FROM `wish_comment` WHERE `wc_id` = ? AND `wc_delete_time` IS NULL AND `wc_show` = 1", [$wcID]);
		if(!$wishComment) exit(json_encode(['return' => 'error', 'msg' => '查無該則留言']));

		$custom = custom::loginStatus();
		$investor = investor::loginStatus();
		if(!$custom && !$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$identity = '';
		$identityID = '';
		$logText = '';
		if($custom) {
			$identity = 'custom';
			$identityID = $custom['cus_id'];
			$logText = '借客(' . $custom['cus_phone'] . ')於借錢需求(' . $wishComment['wish_id'] . ')回覆留言';
		} else {
			$identity = 'investor';
			$identityID = $investor['inv_id'];
			if(strtotime($investor['inv_expiry_time']) < time()) exit(json_encode(['return' => 'error', 'msg' => '帳號已過期，請與客服人員聯繫']));
			$logText = '金主(' . $investor['inv_phone'] . ')於借錢需求(' . $wishComment['wish_id'] . ')回覆留言';
		}

		$info = [
			'wc_show' => 1,
			'wc_status' => 0,
			'wish_id' => $wishComment['wish_id'],
			'wc_level' => 2,
			'wc_main_id' => $wcID,
			'wc_identity' => $identity,
			'wc_identity_id' => $identityID,
			'wc_message' => $content,
			'wc_create_time' => date("Y-m-d H:i:s")
		];

		$sqlStatus = SQL::insert('wish_comment', $info);
		if($sqlStatus) {
			model::setLog($identity, $logText, $info);
			systemEvent::wishComment($wishComment);
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '借錢需求留言回覆時發生錯誤', $info);
			model::sendLineToAdmin("借錢需求留言回覆時發生錯誤\r\n" . siteRootUrl);
		}
	}
}
?>