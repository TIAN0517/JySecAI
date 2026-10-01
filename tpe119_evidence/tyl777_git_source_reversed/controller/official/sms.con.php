<?php
class action {
	public static function sendVerification() {
		$verificationKey = POST::text('key');
		$phone = POST::phone('phone');
		$type = POST::text('type');
		if(!$phone) exit(json_encode(['return' => 'error', 'msg' => '請輸入正確的手機號碼']));
		if($_SESSION['verificationKey'] != $verificationKey) exit(json_encode(['return' => 'error', 'msg' => '無法發送簡訊']));

		if($type == 'investor') {
			$investor = SQL::selectOne('SELECT * FROM `investor` WHERE `inv_phone` = ? AND `inv_delete_time` IS NULL', [$phone]);
			if($investor) exit(json_encode(['return' => 'error', 'msg' => '該手機號碼已使用']));
		} else if($type == 'custom') {
			$custom = SQL::selectOne('SELECT * FROM `custom` WHERE `cus_phone` = ? AND `cus_delete_time` IS NULL', [$phone]);
			if($custom) exit(json_encode(['return' => 'error', 'msg' => '該手機號碼已使用']));
		} else exit(json_encode(['return' => 'error', 'msg' => '無法發送簡訊']));

		$logVerification = SQL::selectOne('SELECT * FROM `log_verification` WHERE `logv_phone` = ? AND `logv_type` = ? ORDER BY `logv_id` DESC', [$phone, $type]);
		if($logVerification) {
			$waitingTime = strtotime($logVerification['logv_create_time']) + 600 - time();
			if($waitingTime > 0) exit(json_encode(['return' => 'waiting', 'msg' => '請勿重複嘗試，請於 ' . $waitingTime . '秒 後嘗試' , 'time' => $waitingTime]));
		}

		require_once(rootPath . '/model/libaries/sendSMS.php');
		$code = sprintf('%04d', rand(0, 9999));
		$send = SMSservice::sendSMS($phone, '[速借款借錢網]您的驗證碼：' . $code . '(10分鐘內有效)；請勿將驗證碼提供給他人，如您無申請此平台請勿理會。');
		if($send['result'] != 'success') {
			model::setLog('error', '手機驗證碼簡訊發送錯誤', ['phone' => $phone, 'code' => $code]);
			model::sendLineToAdmin("手機驗證碼簡訊發送錯誤\r\n電話：" . $phone . "\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '該手機號碼已使用']));
		} else {
			$info = [
				'logv_ip' => $_SERVER["REMOTE_ADDR"],
				'logv_type' => $type,
				'logv_phone' => $phone,
				'logv_code' => $code,
				'logv_status' => 0,
				'logv_create_time' => date("Y-m-d H:i:s")
			];

			$sqlStatus = SQL::insert('log_verification', $info);

			$_SESSION['verificationKey'] =  randomString(10);
			exit( json_encode( ['return' => 'success', 'msg' => '驗證碼已發送至該手機', 'verificationKey' => $_SESSION['verificationKey']] ) );
		}
		exit(json_encode(['return' => 'error', 'msg' => '']));
	}

	public static function create() {
		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$smsContent = POST::text('smsContent');

		if($smsContent == '' ) exit(json_encode(['return' => 'error', 'msg' => '請輸入簡訊內容']));

		$info = [
			'inv_id' => $investor['inv_id'],
			'sms_text' => $smsContent,
			'sms_create_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::insert('sms', $info);
		if($sqlStatus) {
			$wishId = SQL::autoID();
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')新增簡訊版型', $info);
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '新增簡訊版型時發生錯誤', $info);
			model::sendLineToAdmin("新增簡訊版型時發生錯誤\r\n" . siteRootUrl);
			exit( json_encode( ['return' => 'error', 'msg' => '系統發生錯誤，請稍後再嘗試']) );
		}
	}

	public static function modify() {
		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$smsID = POST::int('smsStatus');
		$smsContent = POST::text('smsContent');
		if($smsContent == '' ) exit(json_encode(['return' => 'error', 'msg' => '請輸入簡訊內容']));
		$sms = SQL::selectOne("SELECT * FROM `sms` WHERE `inv_id` = ? AND `sms_id` = ?", [ $investor['inv_id'], $smsID ]);
		if(!$sms) exit(json_encode(['return' => 'error', 'msg' => '查無該資料']));

		$info = [
			'sms_text' => $smsContent,
			'sms_update_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('sms', $info, ['sms_id' => $smsID ] );
		if($sqlStatus) {
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')修改簡訊版型：' . $smsID, $info);
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '修改簡訊版型時發生錯誤', $info);
			model::sendLineToAdmin("修改簡訊版型時發生錯誤\r\n" . siteRootUrl);
			exit( json_encode( ['return' => 'error', 'msg' => '系統發生錯誤，請稍後再嘗試']) );
		}
	}

	public static function delete() {
		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$smsID = POST::int('smsID');
		if(!$smsID) exit(json_encode(['return' => 'error', 'msg' => '無法刪除該版型']));
		$sms = SQL::selectOne("SELECT * FROM `sms` WHERE `inv_id` = ? AND `sms_id` = ?", [ $investor['inv_id'], $smsID ]);
		if(!$sms) exit(json_encode(['return' => 'error', 'msg' => '查無該資料']));

		$info = [
			'inv_id' => $investor['inv_id'],
			'sms_delete_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('sms', $info, ['sms_id' => $smsID ] );
		if($sqlStatus) {
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')刪除簡訊版型：' . $smsID, $info);
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '刪除簡訊版型時發生錯誤', $info);
			model::sendLineToAdmin("刪除簡訊版型時發生錯誤\r\n" . siteRootUrl);
			exit( json_encode( ['return' => 'error', 'msg' => '系統發生錯誤，請稍後再嘗試']) );
		}
	}

	public static function searchAudience() {
		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$start = POST::date('start');
		$end = POST::date('end');
		$smsID = POST::int('text');
		$area = POST::array('area');
		if(!$start || !$end) exit(json_encode(['return' => 'error', 'msg' => '請選擇正確的日期']));
		if(count($area) == 0) exit(json_encode(['return' => 'error', 'msg' => '請選擇發送地區']));
		if(!$smsID) exit(json_encode(['return' => 'error', 'msg' => '請選擇簡訊版型']));

		$sms = SQL::selectOne("SELECT * FROM `sms` WHERE `inv_id` = ? AND `sms_id` = ?", [ $investor['inv_id'], $smsID ]);
		if(!$sms) exit(json_encode(['return' => 'error', 'msg' => '查無該簡訊版型']));

		$areaList = [];
		$cityArea = cityArea;
		foreach ($cityArea as $key => $value) {
			if(in_array($key, $area)) $areaList = array_merge($areaList, $value);
		}
		$citySQLText = implode(',', $areaList);

		$wish = SQL::selectAll("SELECT `custom`.`cus_name`, `custom`.`cus_phone` FROM `wish`
								JOIN `custom` ON `custom`.`cus_id` = `wish`.`cus_id`
								WHERE `wish`.`wish_delete_time` IS NULL AND `wish`.`wish_show` = 1
								AND `wish`.`wish_create_time` BETWEEN '" . $start . " 00:00:00' AND '" . $end . " 23:59:59.999'
								AND FIND_IN_SET(`wish`.`wish_area`, '" . $citySQLText . "')
								AND `custom`.`cus_delete_time` IS NULL
								GROUP BY `wish`.`cus_id`;");
		if(!$wish || count($wish) == 0) exit( json_encode( ['return' => 'error', 'msg' => '查無符合的借客']) );

		$wishList = [];
		foreach ($wish as $key => $custom) {
			$wishList[$key]['phone'] = model::textEncryption($custom['cus_phone']);
			$wishList[$key]['name'] = model::textEncryption($custom['cus_name']);
		}

		exit( json_encode( ['return' => 'success', 'wish' => $wishList]) );
	}

	public static function sendAudience() {
		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$start = POST::date('start');
		$end = POST::date('end');
		$smsID = POST::int('text');
		$area = POST::array('area');
		if(!$start || !$end) exit(json_encode(['return' => 'error', 'msg' => '請選擇正確的日期']));
		if(count($area) == 0) exit(json_encode(['return' => 'error', 'msg' => '請選擇發送地區']));
		if(!$smsID) exit(json_encode(['return' => 'error', 'msg' => '請選擇簡訊版型']));
		$sms = SQL::selectOne("SELECT * FROM `sms` WHERE `inv_id` = ? AND `sms_id` = ?", [ $investor['inv_id'], $smsID ]);
		if(!$sms) exit(json_encode(['return' => 'error', 'msg' => '查無該簡訊版型']));

		$areaList = [];
		$cityArea = cityArea;
		foreach ($cityArea as $key => $value) {
			if(in_array($key, $area)) $areaList = array_merge($areaList, $value);
		}
		$citySQLText = implode(',', $areaList);

		$wish = SQL::selectAll("SELECT `custom`.`cus_id`, `custom`.`cus_name`, `custom`.`cus_phone` FROM `wish`
								JOIN `custom` ON `custom`.`cus_id` = `wish`.`cus_id`
								WHERE `wish`.`wish_delete_time` IS NULL AND `wish`.`wish_show` = 1
								AND `wish`.`wish_create_time` BETWEEN '" . $start . " 00:00:00' AND '" . $end . " 23:59:59.999'
								AND FIND_IN_SET(`wish`.`wish_area`, '" . $citySQLText . "')
								AND `custom`.`cus_delete_time` IS NULL
								GROUP BY `wish`.`cus_id`;");
		if(!$wish || count($wish) == 0) exit( json_encode( ['return' => 'error', 'msg' => '查無符合的借客']) );

		if((int)$investor['inv_short_quota'] < count($wish)) exit( json_encode( ['return' => 'error', 'msg' => '簡訊餘額不足，目前餘額：' . $investor['inv_short_quota']]) );

		SQL::begin();
		$info = [
			'sms_id' => $smsID,
			'ss_start' => $start,
			'ss_end' => $end,
			'ss_area' => $citySQLText,
			'ss_people' => count($wish),
			'ss_create_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::insert('sms_setting', $info);
		if(!$sqlStatus) {
			SQL::rollback();
			model::setLog('error', '儲存發送紀錄發生錯誤', $info);
			model::sendLineToAdmin("儲存發送紀錄發生錯誤\r\n" . siteRootUrl);
			exit( json_encode( ['return' => 'error', 'msg' => '系統發生錯誤，請稍後再嘗試']) );
		}
		$sqlStatus = SQL::update('investor', ['inv_short_quota' => (int)$investor['inv_short_quota'] - count($wish)], ['inv_id' => $investor['inv_id'] ] );
		if(!$sqlStatus) {
			SQL::rollback();
			model::setLog('error', '扣抵簡訊餘額發生錯誤', ['inv_short_quota' => (int)$investor['inv_short_quota'] - count($wish), 'inv_id' => $investor['inv_id']]);
			model::sendLineToAdmin("扣抵簡訊餘額發生錯誤\r\n" . siteRootUrl);
			exit( json_encode( ['return' => 'error', 'msg' => '系統發生錯誤，請稍後再嘗試']) );
		}
		require_once('model/libaries/sendSMS.php');
		foreach ($wish as $custom) {
			$info = [
				'logs_ip' => $_SERVER["REMOTE_ADDR"],
				'inv_id' => $investor['inv_id'],
				'cus_id' => $custom['cus_id'],
				'logs_type' => 'audience',
				'logs_phone' => $custom['cus_phone'],
				'logs_text' => $sms['sms_text'],
				'logs_create_time' => date("Y-m-d H:i:s")
			];
			$sqlStatus = SQL::insert('log_sms', $info);
			if(!$sqlStatus) {
				SQL::rollback();
				model::setLog('error', '儲存發送紀錄發生錯誤', $info);
				model::sendLineToAdmin("儲存發送紀錄發生錯誤\r\n" . siteRootUrl);
				exit( json_encode( ['return' => 'error', 'msg' => '系統發生錯誤，請稍後再嘗試']) );
			}
			$send = SMSservice::sendSMS($custom['cus_phone'], $sms['sms_text']);
		}
		SQL::commit();
		exit( json_encode( ['return' => 'success', 'quota' => (int)$investor['inv_short_quota'] - count($wish)]) );
	}
}
?>