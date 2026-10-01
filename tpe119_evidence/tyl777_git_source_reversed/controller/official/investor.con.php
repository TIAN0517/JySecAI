<?php
class action {
	public static function register() {
		$phone = POST::phone('phone');
		$password = POST::text('password');
		$code = POST::text('code');
		
		if(!$phone) exit(json_encode(['return' => 'error', 'msg' => '請輸入正確的手機號碼']));
		if(strlen($password) > 20 || strlen($password) < 4) exit(json_encode(['return' => 'error', 'msg' => '密碼請輸入4-20字']));
		if(strlen($code) != 4) exit(json_encode(['return' => 'error', 'msg' => '驗證碼錯誤！']));

		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_phone` = ? AND `inv_delete_time` IS NULL", [$phone]);
		if($investor) exit(json_encode(['return' => 'error', 'msg' => '該手機號碼已使用']));
		
		$logVerification = SQL::selectOne("SELECT * FROM `log_verification` WHERE `logv_phone` = ? AND `logv_type` = 'investor' ORDER BY `logv_id` DESC", [$phone]);
		if(!$logVerification) exit(json_encode(['return' => 'error', 'msg' => '驗證碼無效！']));
		if($logVerification['logv_code'] != $code || $code == '') exit(json_encode(['return' => 'error', 'msg' => '驗證碼錯誤！']));
		$waitingTime = strtotime($logVerification['logv_create_time']) + 600 - time();
		if($waitingTime < 0) exit(json_encode(['return' => 'error', 'msg' => '驗證碼已逾期！']));

		$info = [
			'inv_phone' => $phone,
			'inv_password' => password_hash($password, PASSWORD_BCRYPT),
			'inv_short_quota' => 0,
			'inv_card_quota' => 1,
			'inv_program' => '一般會員',
			'inv_remark' => '',
			'inv_expiry_time' => '9999-12-31 23:59:59',
			'inv_last_login' => date("Y-m-d H:i:s"),
			'inv_create_time' => date("Y-m-d H:i:s"),
		];

		$sqlStatus = SQL::insert('investor', $info);
		if($sqlStatus) {
			unset( $_SESSION['custom'] );
			$invID = SQL::autoID();
			$_SESSION['investor'] = $invID;
			$_SESSION['investor_vip'] = 0;
			model::setLog('investor', '金主(' . $phone . ')帳號註冊', $info);
			exit( json_encode( ['return' => 'success', 'toUrl' => siteURL.'investor/card']) );
		} else {
			model::setLog('error', '金主帳號註冊發生錯誤', $info);
			model::sendLineToAdmin("金主帳號註冊發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '帳號註冊發生錯誤']));
		}
	}

	public static function login() {
		$phone = POST::phone('phone');
		$password = POST::text('password');

		if(!$phone) exit(json_encode(['return' => 'error', 'msg' => '請輸入正確的手機號碼']));
		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_phone` = ? AND `inv_ban` = 0 AND `inv_delete_time` IS NULL", [$phone]);
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '帳號密碼錯誤']));
		if($investor['inv_phone'] == $phone && password_verify( $password, $investor['inv_password'] ) ) {
			SQL::update('investor', ['inv_last_login' => date("Y-m-d H:i:s")], ['inv_id' => $investor['inv_id']] );
			unset( $_SESSION['custom'] );
			$_SESSION['investor'] = $investor['inv_id'];
			$_SESSION['investor_vip'] = $investor['inv_vip'];
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')登入', $info);
			$toUrl = siteURL.'investor/modify';
			if( isset($_SESSION['reBackUrl'])) $toUrl = $_SESSION['reBackUrl'];
			exit(json_encode(['return' => 'success', 'toUrl' => $toUrl]));
		} else exit(json_encode(['return' => 'error', 'msg' => '帳號密碼錯誤']));
	}

	public static function modify() {
		$email = POST::text('email');
		$lineid = POST::text('lineid');

		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$info = [
			'inv_email' => $email,
			'inv_line_id' => $lineid,
			'inv_update_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('investor', $info, ['inv_id' => $investor['inv_id']] );
		if($sqlStatus) {
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')修改基本資料', $info);
			exit(json_encode(['return' => 'success']));
		} else {
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')修改資料發生錯誤', $info);
			model::sendLineToAdmin("金主修改資料發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}
	}

	public static function modifyPassword() {
		$oPassword = POST::text('oPassword');
		$nPassword = POST::text('nPassword');
		$confirm = POST::text('confirm');

		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '目前無法修改資料']));
		if($nPassword != $confirm) exit(json_encode(['return' => 'error', 'msg' => '密碼與密碼確認不符']));
		if(strlen($nPassword) > 20 || strlen($nPassword) < 4) exit(json_encode(['return' => 'error', 'msg' => '密碼請輸入4-20字']));
		if( !password_verify( $oPassword, $investor['inv_password'] ) ) exit(json_encode(['return' => 'error', 'msg' => '舊密碼輸入錯誤']));

		$info = [
			'inv_password' => password_hash($nPassword, PASSWORD_BCRYPT),
			'inv_update_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('investor', $info, ['inv_id' => $investor['inv_id']] );
		if($sqlStatus) {
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')修改密碼', $info);
			exit(json_encode(['return' => 'success']));
		} else {
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')修改密碼發生錯誤', $info);
			model::sendLineToAdmin("金主修改密碼發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}
	}

	public static function creationCard() {
		$id = POST::int('id');
		if($id != 0) exit(json_encode(['return' => 'error', 'msg' => '目前無法建立刊登']));

		$contact = POST::text('contact');
		$area = POST::array('area');
		$type = POST::array('type');
		$phone_main = POST::text('phone_main');
		$phone_spare = POST::text('phone_spare');
		$line = POST::text('line');
		$title = POST::text('title');
		$content = POST::text('content');

		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));
		if($phone_main == '' || $contact == '' || $title == '') exit(json_encode(['return' => 'error', 'msg' => '請填寫必要資料']));

		if(count($area) > 3) exit(json_encode(['return' => 'swal', 'msg' => '服務地區最多不可超過 3 個']));

		$typeList = cardTag;
		$typeQuota = ($investor['inv_vip'] == 0)? 5:count($typeList);
		if(count($type) > $typeQuota ) exit(json_encode(['return' => 'swal', 'msg' => '服務項目不可超過 ' . $typeQuota . ' 種']));

		$area = json_encode($area, JSON_UNESCAPED_UNICODE);
		$type = json_encode($type, JSON_UNESCAPED_UNICODE);

		$info = [
			'card_vip' => 0,
			'card_show' => 1,
			'inv_id' => $investor['inv_id'],
			'card_image' => '',
			'card_title' => $title,
			'card_image_alt' => $title,
			'card_image_title' => $title,
			'card_expiry_time' => '9999-12-31 23:59:59',
			'card_listing' => '1970-01-01 08:00:00',
			'card_delisting' => '9999-12-31 23:59:59',
			'card_refresh' => 1,
			'card_area_quota' => 3,
			'card_area' => $area,
			'card_tag' => $type,
			'card_contact' => $contact,
			'card_phone_main' => $phone_main,
			'card_phone_spare' => $phone_spare,
			'card_line_id' => $line,
			'card_content' => $content,
			'card_remark' => '',
			'card_create_time' => date("Y-m-d H:i:s"),
			'card_update_time' => date("Y-m-d H:i:s")
		];

		$sqlStatus = SQL::insert('card', $info);
		if($sqlStatus) {
			$cardID = SQL::autoID();
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')建立名片(' . $cardID . ')', $info);
			exit(json_encode(['return' => 'success', 'card' => $cardID]));
		} else {
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')建立名片發生錯誤', $info);
			model::sendLineToAdmin("金主建立名片發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}
	}

	public static function card() {
		$id = POST::int('id');
		$contact = POST::text('contact');
		$area = POST::array('area');
		$type = POST::array('type');
		$phone_main = POST::text('phone_main');
		$phone_spare = POST::text('phone_spare');
		$line = POST::text('line');
		$title = POST::text('title');
		$content = POST::text('content');

		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));
		if($phone_main == '' || $contact == '' || $title == '') exit(json_encode(['return' => 'error', 'msg' => '請填寫必要資料']));

		$card = SQL::selectOne("SELECT * FROM `card` WHERE `inv_id` = ? AND `card_id` = ? AND `card_delete_time` IS NULL", [ $investor['inv_id'], $id ]);
		if(!$card) exit(json_encode(['return' => 'error', 'msg' => '查無該資料']));

		if(count($area) > $card['card_area_quota'] ) exit(json_encode(['return' => 'swal', 'msg' => '服務地區最多不可超過' . $card['card_area_quota'] . '個']));

		$typeList = cardTag;
		$typeQuota = ($investor['inv_vip'] == 0)? 5:count($typeList);
		if(count($type) > $typeQuota ) exit(json_encode(['return' => 'swal', 'msg' => '服務項目不可超過' . $typeQuota . '種']));

		$area = json_encode($area, JSON_UNESCAPED_UNICODE);
		$type = json_encode($type, JSON_UNESCAPED_UNICODE);

		$info = [
			'card_title' => $title,
			'card_area' => $area,
			'card_tag' => $type,
			'card_contact' => $contact,
			'card_phone_main' => $phone_main,
			'card_phone_spare' => $phone_spare,
			'card_line_id' => $line,
			'card_content' => $content,
			'card_update_time' => date("Y-m-d H:i:s")
		];

		$sqlStatus = SQL::update('card', $info, ['card_id' => $id] );
		if($sqlStatus) {
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')修改名片(' . $id . ')，原資料備份', $card);
			exit(json_encode(['return' => 'success']));
		} else {
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')修改名片發生錯誤', $info);
			model::sendLineToAdmin("金主修改名片發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}
	}

	public static function cardSticky() {
		$id = POST::int('id');

		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));
		$card = SQL::selectOne("SELECT * FROM `card` WHERE `inv_id` = ? AND `card_id` = ? AND `card_delete_time` IS NULL", [ $investor['inv_id'], $id ]);
		if(!$card) exit(json_encode(['return' => 'error', 'msg' => '查無該資料']));

		$logList = SQL::selectOne("SELECT count(*) AS `listCount` FROM `card_top_log` WHERE `card_id` = ? AND TO_DAYS(`ctl_create_time`) = TO_DAYS(NOW())", [$id]);
		if((int)$logList['listCount'] >= (int)$card['card_refresh'] ) exit(json_encode(['return' => 'error', 'msg' => '該名片已達到每日置頂上限']));

		SQL::begin();
		$info = [
			'ctl_type' => 'manual',
			'card_id' => $id,
			'ctl_create_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::insert('card_top_log', $info);
		if(!$sqlStatus) {
			SQL::rollback();
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')，手動置頂名片(' . $id . ')發生錯誤；log', $info);
			model::sendLineToAdmin("金主手動置頂名片發生錯誤；log\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存時發生錯誤，請稍後再試']));
		}

		$info = [
			'card_sticky_time' =>  date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('card', $info, ['card_id' => $id] );
		if($sqlStatus) {
			SQL::commit();
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')，手動置頂名片(' . $id . ')', $info);
			exit(json_encode(['return' => 'success']));
		} else {
			SQL::rollback();
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')，手動置頂名片(' . $id . ')發生錯誤；sticky_time', $info);
			model::sendLineToAdmin("金主手動置頂名片發生錯誤；sticky_time\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}

	}

	public static function getCardStickySetting() {
		$id = POST::int('id');

		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));
		$card = SQL::selectOne("SELECT * FROM `card` WHERE `inv_id` = ? AND `card_id` = ? AND `card_delete_time` IS NULL", [ $investor['inv_id'], $id ]);
		if(!$card) exit(json_encode(['return' => 'error', 'msg' => '查無該名片']));

		$topSetting = SQL::selectAll("SELECT * FROM `card_top_setting` WHERE `inv_id` = ? AND `card_id` = ?", [ $investor['inv_id'], $id ]);
		$timing = [];
		foreach ($topSetting as $value) {
			$timing[] = $value['cts_timing'];
		}
		exit(json_encode(['return' => 'success', 'timing' => $timing, 'quota' => $card['card_refresh']]));
	}

	public static function stickySettingSave() {
		$id = POST::int('id');
		$timing = POST::array('timing');

		$investor = investor::loginStatus();
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));
		if($investor['inv_vip'] == 0) exit(json_encode(['return' => 'error', 'msg' => '免費會員無法設定自動置頂功能']));

		$card = SQL::selectOne("SELECT * FROM `card` WHERE `inv_id` = ? AND `card_id` = ? AND `card_delete_time` IS NULL", [ $investor['inv_id'], $id ]);
		if(!$card) exit(json_encode(['return' => 'error', 'msg' => '查無該名片']));

		SQL::begin();
		$sqlStatus = SQL::querySql('DELETE FROM `card_top_setting` WHERE `card_id` = ?', [$id]);
		if(!$sqlStatus) {
			SQL::rollback();
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')，設定名片(' . $id . ')自動置頂發生錯誤；DELETE', [$id, $timing]);
			model::sendLineToAdmin("金主設定名片自動置頂發生錯誤；DELETE\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存時發生錯誤，請稍後再試']));
		}

		foreach ($timing as $value) {
			$info = [
				'cts_status' => 1,
				'inv_id' => $investor['inv_id'],
				'card_id' => $id,
				'cts_timing' => $value,
				'cts_create_time' => date("Y-m-d H:i:s")
			];

			$sqlStatus = SQL::insert('card_top_setting', $info);
			if(!$sqlStatus) {
				SQL::rollback();
				model::setLog('error', '金主(' . $investor['inv_phone'] . ')，設定名片(' . $id . ')自動置頂發生錯誤；setting', [$id, $timing]);
				model::sendLineToAdmin("金主設定名片自動置頂發生錯誤；setting\r\n" . siteRootUrl);
				exit(json_encode(['return' => 'error', 'msg' => '資料儲存時發生錯誤，請稍後再試']));
			}
		}
		SQL::commit();
		exit(json_encode(['return' => 'success']));
	}

	public static function vipSearch() {
		$area = POST::text('area', '全國');

		if($area != '全國' && array_key_exists($area, cityArea)) {
			$cityList = cityArea[$area];
			foreach ($cityList as $key => $city) {
				$cityList[$key] = "'%" . $city . "%'";
			}
			$sqlCommand = implode(' OR `card`.`card_area` LIKE ', $cityList);
			$sqlCommand = 'AND (`card`.`card_area` LIKE ' . $sqlCommand . ')';
		}

		$vipCardList = SQL::selectAll("SELECT * FROM `card` WHERE `card_vip` = 1 AND `card_show` = 1 AND `card_status` = 0 AND `card_expiry_time` > NOW()
										AND `card_delete_time` IS NULL " . $sqlCommand . " ORDER BY RAND()");
		
		$cardInfo = [];
		foreach ($vipCardList as $key => $card) {
			$cardPic = '';
			$miniPic = explode('.', $card['card_image']);
			if( is_array($miniPic) && count($miniPic) > 0 ) {
				$cardPic = $miniPic[0] . '_m.' . $miniPic[1];
				if(is_file(cardPathAbs . $cardPic)) $cardPic = cardPathRel . $cardPic;
				else $cardPic = (is_file(cardPathAbs . $card['card_image']) && $card['card_image'] != '')? cardPathRel . $card['card_image']:noPhoto;
			} else {
				$cardPic = (is_file(cardPathAbs . $card['card_image']) && $card['card_image'] != '')? cardPathRel . $card['card_image']:noPhoto;
			}
			$cardInfo[] = [
				'id' => $card['card_id'],
				'pic' => $cardPic,
				'pic_alt' => $card['card_image_title'],
				'pic_title' => $card['card_image_alt'],
				'title' => $card['card_title'],
			];
		}
		exit( json_encode( ['card' => $cardInfo]) );
	}

	public static function cardReply() {
		$custom = custom::loginStatus();
		if(!$custom) exit(json_encode(['return' => 'error', 'msg' => '尚未登入借客會員']));
		$cardID = POST::int('id');
		$content = POST::text('content');
		$code = POST::text('code');

		if($code != $_SESSION['cardCode']) exit(json_encode(['return' => 'error', 'msg' => '目前無法留言']));

		$card = SQL::selectOne("SELECT * FROM `card` WHERE `card_id` = ? AND `card_delete_time` IS NULL AND `card_show` = 1 AND `card_status` = 0", [$cardID]);
		if(!$card) exit(json_encode(['return' => 'error', 'msg' => '已查無該名片']));

		$info = [
			'cc_show' => 1,
			'cc_status' => 0,
			'card_id' => $cardID,
			'cc_level' => 1,
			'cc_main_id' => null,
			'cc_identity' => 'custom',
			'cc_identity_id' => $custom['cus_id'],
			'cc_message' => $content,
			'cc_create_time' => date("Y-m-d H:i:s")
		];

		$sqlStatus = SQL::insert('card_comment', $info);
		if($sqlStatus) {
			model::setLog('custom', '借客(' . $custom['cus_phone'] . ')於名片(' . $cardID . ')留言' , $info);
			systemEvent::cardReply($card);
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '名片留言時發生錯誤', $info);
			model::sendLineToAdmin("名片留言時發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存時發生錯誤，請稍後再試']));
		}
	}

	public static function cardComment() {
		$ccID = POST::int('id');
		$content = POST::text('content');
		$code = POST::text('code');

		if($code != $_SESSION['cardCode']) exit(json_encode(['return' => 'error', 'msg' => '目前無法留言']));

		$cardComment = SQL::selectOne("SELECT * FROM `card_comment` WHERE `cc_id` = ? AND `cc_delete_time` IS NULL AND `cc_show` = 1", [$ccID]);
		if(!$cardComment) exit(json_encode(['return' => 'error', 'msg' => '查無該則留言']));

		$custom = custom::loginStatus();
		$investor = investor::loginStatus();
		if(!$custom && !$investor) exit(json_encode(['return' => 'error', 'msg' => '尚未登入會員']));

		$identity = '';
		$identityID = '';
		$logText = '';
		if($custom) {
			$identity = 'custom';
			$identityID = $custom['cus_id'];
			$logText = '借客(' . $custom['cus_phone'] . ')於名片(' . $cardComment['card_id'] . ')回覆留言';
		} else {
			$identity = 'investor';
			$identityID = $investor['inv_id'];
			if(strtotime($investor['inv_expiry_time']) < time()) exit(json_encode(['return' => 'error', 'msg' => '帳號已過期，請與客服人員聯繫']));
			$logText = '金主(' . $investor['inv_phone'] . ')於名片(' . $cardComment['card_id'] . ')回覆留言';
		}

		$info = [
			'cc_show' => 1,
			'cc_status' => 0,
			'card_id' => $cardComment['card_id'],
			'cc_level' => 2,
			'cc_main_id' => $ccID,
			'cc_identity' => $identity,
			'cc_identity_id' => $identityID,
			'cc_message' => $content,
			'cc_create_time' => date("Y-m-d H:i:s")
		];

		$sqlStatus = SQL::insert('card_comment', $info);
		if($sqlStatus) {
			model::setLog($identity, $logText, $info);
			systemEvent::cardComment($cardComment, $info);
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '名片留言回覆時發生錯誤', $info);
			model::sendLineToAdmin("名片留言回覆時發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存時發生錯誤，請稍後再試']));
		}
	}

	public static function forgetPassword() {
		$phone = POST::phone('phone');
		$identity = POST::text('identity');

		if($identity != 'investor') exit(json_encode(['return' => 'error', 'msg' => '查無金主資料']));
		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_phone` = ? AND `inv_ban` = 0 AND `inv_delete_time` IS NULL", [$phone]);
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '查無金主資料']));

		$token = randomString(10);
		$ckToken = SQL::selectOne("SELECT * FROM `log_forget_password` WHERE `logf_token` = ? AND `logf_status` = 0 ", [$token]);
		while ($ckToken) {
			$token = randomString(10);
			$ckToken = SQL::selectOne("SELECT * FROM `log_forget_password` WHERE `logf_token` = ? AND `logf_status` = 0 ", [$token]);
		}

		$info = [
			'logf_status' => 0,
			'logf_ip' => $_SERVER["REMOTE_ADDR"],
			'logf_identity' => 'investor',
			'logf_identity_id' => $investor['inv_id'],
			'logf_phone' => $investor['inv_phone'],
			'logf_token' => $token,
			'logf_create_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::insert('log_forget_password', $info);
		if($sqlStatus) {
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')，忘記密碼', $info);

			$resetUrl = siteRootUrl . 'resetPassword?t=' . $token;
			require_once(rootPath . '/model/libaries/sendSMS.php');
			$send = SMSservice::sendSMS($investor['inv_phone'], '[速借款借錢網]我們收到您重設帳戶密碼的請求，請點擊下方網址進行密碼重設；如不重設密碼請忽略此訊息。');
			if($send['result'] != 'success') {
				model::setLog('error', '金主重設密碼簡訊發送錯誤-1', ['phone' => $investor['inv_phone'], 'send' => $send]);
				model::sendLineToAdmin("金主重設密碼簡訊發送錯誤-1\r\n電話：" . $investor['inv_phone'] . "\r\n" . siteRootUrl);
				exit(json_encode(['return' => 'error', 'msg' => '簡訊發送發生問題，請稍後再試']));
			}
			$send = SMSservice::sendSMS($investor['inv_phone'], $resetUrl);
			if($send['result'] != 'success') {
				model::setLog('error', '金主重設密碼簡訊發送錯誤-2', ['phone' => $investor['inv_phone'], 'send' => $send]);
				model::sendLineToAdmin("金主重設密碼簡訊發送錯誤-2\r\n電話：" . $investor['inv_phone'] . "\r\n" . siteRootUrl);
				exit(json_encode(['return' => 'error', 'msg' => '簡訊發送發生問題，請稍後再試']));
			}
			exit( json_encode( ['return' => 'success']) );
		} else {
			model::setLog('error', '儲存金主忘記密碼紀錄發生錯誤', $info);
			model::sendLineToAdmin("儲存金主忘記密碼紀錄發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存時發生錯誤，請稍後再試']));
		}
	}

	public static function resetPassword() {
		$password = POST::text('password');
		$token = POST::text('token');

		$ckToken = SQL::selectOne("SELECT * FROM `log_forget_password` WHERE `logf_token` = ? AND `logf_status` = 0 AND `logf_identity` = 'investor'", [$token]);
		if(!$ckToken) exit(json_encode(['return' => 'error', 'msg' => '無法重設密碼，請與客服人員聯繫']));

		if(strlen($password) > 20 || strlen($password) < 4) exit(json_encode(['return' => 'error', 'msg' => '密碼請輸入4-20字']));
		$investor = SQL::selectOne("SELECT * FROM `investor` WHERE `inv_id` = ? AND `inv_ban` = 0 AND `inv_delete_time` IS NULL", [$ckToken['logf_identity_id']]);
		if(!$investor) exit(json_encode(['return' => 'error', 'msg' => '查無金主資料，請與客服人員聯繫']));

		SQL::begin();

		$info = [
			'inv_password' => password_hash($password, PASSWORD_BCRYPT),
			'inv_update_time' => date("Y-m-d H:i:s")
		];
		$sqlStatus = SQL::update('investor', $info, ['inv_id' => $investor['inv_id']] );
		if($sqlStatus) {
			model::setLog('investor', '金主(' . $investor['inv_phone'] . ')，重設密碼', $info);
		} else {
			SQL::rollback();
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')重設密碼發生錯誤', $info);
			model::sendLineToAdmin("金主重設密碼發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}

		$sqlStatus = SQL::update('log_forget_password', ['logf_status' => '1'], ['logf_identity' => 'investor', 'logf_identity_id' => $investor['inv_id']] );
		if(!$sqlStatus) {
			SQL::rollback();
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')重設密碼發生錯誤', $info);
			model::sendLineToAdmin("金主重設密碼發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}

		$sqlStatus = SQL::update('investor', ['inv_last_login' => date("Y-m-d H:i:s")], ['inv_id' => $investor['inv_id']] );
		if(!$sqlStatus) {
			SQL::rollback();
			model::setLog('error', '金主(' . $investor['inv_phone'] . ')重設密碼修改登入時間發生錯誤', $info);
			model::sendLineToAdmin("重設密碼修改登入時間發生錯誤\r\n" . siteRootUrl);
			exit(json_encode(['return' => 'error', 'msg' => '資料儲存發生問題，請稍後再試']));
		}
		$_SESSION['investor'] = $investor['inv_id'];
		$_SESSION['investor_vip'] = $investor['inv_vip'];
		SQL::commit();

		exit(json_encode(['return' => 'success', 'toUrl' => siteRootUrl . 'investor/modify']));
	}
}
?>