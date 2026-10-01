<?php
class action {
	public static function register() {
		$phone = POST::phone('phone');
		$password = POST::text('password');
		$name = POST::text('name');
		$area = POST::text('area');
		$collateral = POST::text('collateral');
		$explanation = POST::text('explanation');
		$money = POST::int('money');
		$code = POST::text('code');
		
		if(!$phone) exit(json_encode(['return' => 'error', 'msg' => '請輸入正確的手機號碼']));
		if(strlen($password) > 20 || strlen($password) < 4) exit(json_encode(['return' => 'error', 'msg' => '密碼請輸入4-20字']));
		if(strlen($code) != 4) exit(json_encode(['return' => 'error', 'msg' => '驗證碼錯誤！']));

		if($name == '' || $area == '' || $collateral == '' || $explanation == '') exit(json_encode(['return' => 'error', 'msg' => '資料填寫錯誤']));

		$custom = SQL::selectOne("SELECT * FROM `custom` WHERE `cus_phone` = ? AND `cus_delete_time` IS NULL", [$phone]);
		if($custom) exit(json_encode(['return' => 'error', 'msg' => '該手機號碼已使用']));
		
		$logVerification = SQL::selectOne("SELECT * FROM `log_verification` WHERE `logv_phone` = ? AND `logv_type` = 'custom' ORDER BY `logv_id` DESC", [$phone]);
		if(!$logVerification) exit(json_encode(['return' => 'error', 'msg' => '驗證碼無效！']));
		if($logVerification['logv_code'] != $code || $code == '') exit(json_encode(['return' => 'error', 'msg' => '驗證碼錯誤！']));
		$waitingTime = strtotime($logVerification['logv_create_time']) + 600 - time();
		if($waitingTime < 0) exit(json_encode(['return' => 'error', 'msg' => '驗證碼已逾期！']));
		if($money > 1000000000) exit(json_encode(['return' => 'error', 'msg' => '借款金額過高！']));

		$info = [
			'cus_phone' => $phone,
			'cus_password' => password_hash($password, PASSWORD_BCRYPT),
			'cus_name' => $name,
			'cus_remark' => '',
			'cus_last_login' => date("Y-m-d H:i:s"),
			'cus_create_time' => date("Y-m-d H:i:s")
		];
		SQL::begin();
		$sqlStatus = SQL::insert('custom', $info);
		if($sqlStatus) {
			unset( $_SESSION['investor'] );
			$cusId = SQL::autoID();
			$_SESSION['custom'] = $cusId;
			model::setLog('custom', '借客(' . $phone . ')帳號註冊', $info);
			$info = [
				'cus_id' => $cusId,
				'wish_title' => $explanation,
				'wish_area' => $area,
				'wish_money' => $money,
				'wish_collateral' => $collateral,
				'wish_create_time' => date("Y-m-d H:i:s")
			];
			$sqlStatus = SQL::insert('wish', $info);
			if($sqlStatus) {
				$wishId = SQL::autoID();
				model::setLog('custom', '顧客(' . $phone . ')發布借錢需求(' . $wishId . ')', $info);
				SQL::commit();
				systemEvent::createWish($wishId);
				$toUrl = siteRootUrl . 'wish/info/' . $wishId;
				if( isset($_SESSION['reBackUrl'])) {
					$toUrl = $_SESSION['reBackUrl'];
					unset($_SESSION['reBackUrl']);
				}
				exit( json_encode( ['return' => 'success', 'toUrl' => $toUrl]) );
			} else {
				SQL::rollback();
				model::setLog('error', '註冊且發布借錢需求時發生錯誤', $info);
				model::sendLineToAdmin("註冊且發布借錢需求時發生錯誤\r\n" . siteRootUrl);
			}
		} else {
			SQL::rollback();
			model::setLog('error', '借客帳號註冊發生錯誤', $info);
			model::sendLineToAdmin("借客帳號註冊發生錯誤\r\n" . siteRootUrl);
		}
		exit(json_encode(['return' => 'error', 'msg' => '帳號註冊發生錯誤']));
	}

	public static function login() {
		$phone = POST::phone('phone');
		$password = POST::text('password');

		if(!$phone) exit(json_encode(['return' => 'error', 'msg' => '請輸入正確的手機號碼']));
		$custom = SQL::selectOne("SELECT * FROM `custom` WHERE `cus_phone` = ? AND `cus_ban` = 0 AND `cus_delete_time` IS NULL", [$phone]);
		if(!$custom) exit(json_encode(['return' => 'error', 'msg' => '帳號密碼錯誤']));
		if($custom['cus_phone'] == $phone && password_verify( $password, $custom['cus_password'] ) ) {
			SQL::update('custom', ['cus_last_login' => date("Y-m-d H:i:s")], ['cus_id' => $custom['cus_id']] );
			unset( $_SESSION['investor'] );
			$_SESSION['custom'] = $custom['cus_id'];
			model::setLog('custom', '借客(' . $custom['cus_phone'] . ')登入', $info);
			$toUrl = siteURL.'custom/modify';
			if( isset($_SESSION['reBackUrl'])) {
				$toUrl = $_SESSION['reBackUrl'];
				unset($_SESSION['reBackUrl']);
			}
			exit(json_encode(['return' => 'success', 'toUrl' => $toUrl]));
		} else exit(json_encode(['return' => 'error', 'msg' => '帳號密碼錯誤']));
	}

	public static function modify() {
		$name = POST::text('name');
		$lineid = POST::text('lineid');

		$custom = custom::loginStatus();
		if(!$custom) exit(json_encode(['return' => 'error', 'msg' => '目前無法修改資料']));

		if($name == '') exit(json_encode(['return' => 'error', 'msg' => '請輸入暱稱/姓名']));

		$info = [
			'cus_name' => $name,
			'cus_line_id' => $lineid,
			'cus_update_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('custom', $info, ['cus_id' => $custom['cus_id']] );
		if($sqlStatus) {
			model::setLog('custom', '借客(' . $custom['cus_phone'] . ')修改基本資料', $info);
			exit(json_encode(['return' => 'success']));
		} else {
			model::setLog('error', '借客(' . $custom['cus_phone'] . ')修改資料發生錯誤', $info);
			model::sendLineToAdmin("借客修改資料發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}
	}
	
	public static function modifyPassword() {
		$oPassword = POST::text('oPassword');
		$nPassword = POST::text('nPassword');
		$confirm = POST::text('confirm');

		$custom = custom::loginStatus();
		if(!$custom) exit(json_encode(['return' => 'error', 'msg' => '目前無法修改資料']));
		if($nPassword != $confirm) exit(json_encode(['return' => 'error', 'msg' => '密碼與密碼確認不符']));
		if(strlen($nPassword) > 20 || strlen($nPassword) < 4) exit(json_encode(['return' => 'error', 'msg' => '密碼請輸入4-20字']));
		if( !password_verify( $oPassword, $custom['cus_password'] ) ) exit(json_encode(['return' => 'error', 'msg' => '舊密碼輸入錯誤']));

		$info = [
			'cus_password' => password_hash($nPassword, PASSWORD_BCRYPT),
			'cus_update_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('custom', $info, ['cus_id' => $custom['cus_id']] );
		if($sqlStatus) {
			model::setLog('custom', '借客(' . $custom['cus_phone'] . ')修改密碼', $info);
			exit(json_encode(['return' => 'success']));
		} else {
			model::setLog('error', '借客(' . $custom['cus_phone'] . ')修改密碼發生錯誤', $info);
			model::sendLineToAdmin("借客修改密碼發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}
	}

	public static function forgetPassword() {
		$phone = POST::phone('phone');
		$identity = POST::text('identity');

		if($identity != 'custom') exit(json_encode(['return' => 'error', 'msg' => '查無借客資料']));
		$custom = SQL::selectOne("SELECT * FROM `custom` WHERE `cus_phone` = ? AND `cus_ban` = 0 AND `cus_delete_time` IS NULL", [$phone]);
		if(!$custom) exit(json_encode(['return' => 'error', 'msg' => '查無借客資料']));

		$token = randomString(10);
		$ckToken = SQL::selectOne("SELECT * FROM `log_forget_password` WHERE `logf_token` = ? AND `logf_status` = 0 ", [$token]);
		while ($ckToken) {
			$token = randomString(10);
			$ckToken = SQL::selectOne("SELECT * FROM `log_forget_password` WHERE `logf_token` = ? AND `logf_status` = 0 ", [$token]);
		}

		$info = [
			'logf_status' => 0,
			'logf_ip' => $_SERVER["REMOTE_ADDR"],
			'logf_identity' => 'custom',
			'logf_identity_id' => $custom['cus_id'],
			'logf_phone' => $custom['cus_phone'],
			'logf_token' => $token,
			'logf_create_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::insert('log_forget_password', $info);
		if($sqlStatus) {
			model::setLog('custom', '借客(' . $custom['cus_phone'] . ')，忘記密碼', $info);

			$resetUrl = siteRootUrl . 'resetPassword?t=' . $token;
			require_once(rootPath . '/model/libaries/sendSMS.php');
			$send = SMSservice::sendSMS($custom['cus_phone'], '[速借款借錢網]我們收到您重設帳戶密碼的請求，請點擊下方網址進行密碼重設；如不重設密碼請忽略此訊息。 ' . $resetUrl);
			if($send['result'] != 'success') {
				model::setLog('error', '借客重設密碼簡訊發送錯誤', ['phone' => $custom['cus_phone'], 'send' => $send]);
				model::sendLineToAdmin("借客重設密碼簡訊發送錯誤\r\n電話：" . $custom['cus_phone'] . "\r\n" . siteRootUrl);
				exit(json_encode(['return' => 'error', 'msg' => '簡訊發送發生問題，請稍後再試']));
			}
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '儲存借客忘記密碼紀錄發生錯誤', $info);
			model::sendLineToAdmin("儲存借客忘記密碼紀錄發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存時發生錯誤，請稍後再試']));
		}
	}

	public static function resetPassword() {
		$password = POST::text('password');
		$token = POST::text('token');

		$ckToken = SQL::selectOne("SELECT * FROM `log_forget_password` WHERE `logf_token` = ? AND `logf_status` = 0 AND `logf_identity` = 'custom'", [$token]);
		if(!$ckToken) exit(json_encode(['return' => 'error', 'msg' => '無法重設密碼，請與客服人員聯繫']));

		if(strlen($password) > 20 || strlen($password) < 4) exit(json_encode(['return' => 'error', 'msg' => '密碼請輸入4-20字']));
		$custom = SQL::selectOne("SELECT * FROM `custom` WHERE `cus_id` = ? AND `cus_ban` = 0 AND `cus_delete_time` IS NULL", [$ckToken['logf_identity_id']]);
		if(!$custom) exit(json_encode(['return' => 'error', 'msg' => '查無借客資料，請與客服人員聯繫']));

		SQL::begin();

		$info = [
			'cus_password' => password_hash($password, PASSWORD_BCRYPT),
			'cus_update_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('custom', $info, ['cus_id' => $custom['cus_id']] );
		if($sqlStatus) {
			model::setLog('custom', '借客(' . $custom['cus_phone'] . ')，重設密碼', $info);
		} else {
			SQL::rollback();
			model::setLog('error', '借客(' . $custom['cus_phone'] . ')重設密碼發生錯誤', $info);
			model::sendLineToAdmin("借客重設密碼發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}

		$sqlStatus = SQL::update('log_forget_password', ['logf_status' => '1'], ['logf_identity' => 'custom', 'logf_identity_id' => $custom['cus_id']] );
		if(!$sqlStatus) {
			SQL::rollback();
			model::setLog('error', '借客(' . $custom['cus_phone'] . ')重設密碼發生錯誤', $info);
			model::sendLineToAdmin("借客重設密碼發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}

		$sqlStatus = SQL::update('custom', ['cus_last_login' => date("Y-m-d H:i:s")], ['cus_id' => $custom['cus_id']] );
		if(!$sqlStatus) {
			SQL::rollback();
			model::setLog('error', '借客(' . $custom['cus_phone'] . ')重設密碼修改登入時間發生錯誤', $info);
			model::sendLineToAdmin("重設密碼修改登入時間發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}
		$_SESSION['custom'] = $custom['cus_id'];
		SQL::commit();

		exit(json_encode(['return' => 'success', 'toUrl' => siteRootUrl . 'custom/modify']));
	}
}
?>