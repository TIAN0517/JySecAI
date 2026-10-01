<?php
class action {
	public static function login() {
		$username = POST::text('username');
		$password = md5(POST::text('password'));

		if(isset($_SESSION['false_time']) && (int)$_SESSION['false_time'] > strtotime("now")){
			exit('重複錯誤太多次，請稍後再進行登入');
		}else if(isset($_SESSION['false_time']) && (int)$_SESSION['false_time'] < strtotime("now")){
			if((int)$_SESSION['false_count'] >= 5) $_SESSION['false_count'] = 0;
		}

		if(!isset($_SESSION['false_count'])) $_SESSION['false_count'] = 0;
		if($username == '' || $password == '') exit('帳號密碼錯誤');

		if((int)$_SESSION['false_count'] >= 999){
			$_SESSION['false_time'] = strtotime("+30 seconds");
			exit('重複錯誤太多次，請稍後再進行登入');
		}

		$login = SQL::selectOne("SELECT * FROM `account` WHERE `acc_username` = ? AND `acc_password` = ?", array($username, $password));
		if($login['acc_username'] == $username){
			$_SESSION['manage_name'] = $login['acc_name'];
			$_SESSION['manage_login'] = true;
			$_SESSION['manage_identity'] = 'admin';
			model::setLog('manage', '總後台 ' . $login['acc_name'] . ' 登入', $_SESSION);
			exit('login');
		}else{
			$_SESSION['false_count'] = (int)$_SESSION['false_count'] + 1;
			model::setLog('manage', '總後台登入帳號密碼錯誤', ['user' => _POST('username'), 'pass' => _POST('password') ]);
			exit('帳號密碼錯誤');
		}
		die;
	}

	public static function logout() {
		unset( $_SESSION['manage_name'] );
		unset( $_SESSION['manage_login'] );
		unset( $_SESSION['manage_identity'] );
		header('Location: ' . siteRootUrl);
		exit();
	}

	public static function itemCheck() {
		if(!$_SESSION['manage_login'] && $_SESSION['manage_identity'] != 'admin') die;
		$table = POST::text('t');
		$field = POST::text('f');
		$ID = POST::text('d');
		$value = POST::text('v');
		$idField = POST::text('df');
		$re = SQL::update($table, [$field => $value],[$idField => $ID]);
		if($re) exit('success');
		else exit('資料修改時發生錯誤');
		die;
	}

	public static function getCityArea() {
		$city = POST::text('city');
		$area = model::getCityArea($city);
		exit( json_encode($area) );
	}

	public static function summernoteUploadImg(){
		$savePath = summerNotePathAbs;
		$saveUrl = summerNotePathRel;

		$ext_arr = [
			'images' => ['gif', 'jpg', 'jpeg', 'png', 'bmp'],
		];
	
		$savePath = realpath($savePath) . '/';
		$msg = null;
	
		if (!empty($_FILES['files']['error'])) {
			switch ($_FILES['files']['error']) {
				case '1':
					$error = '超過php.ini限制的大小。';
					break;
				case '2':
					$error = '超過表單限制的大小。';
					break;
				case '3':
					$error = '圖片無法完整上傳。';
					break;
				case '4':
					$error = '請選擇圖片。';
					break;
				case '6':
					$error = '找不到暫存目錄。';
					break;
				case '7':
					$error = '寫入文件出錯。';
					break;
				case '8':
					$error = '檔案上傳意外中止。';
					break;
				case '999':
				default:
					$error = '未知錯誤。';
			}
	
			$msg = $error;
		}
	
		if ($msg === NULL && empty($_FILES) === false) {
			$file_name = $_FILES['files']['name'];
			$tmp_name = $_FILES['files']['tmp_name'];
			$file_size = $_FILES['files']['size'];
	
			if (!$file_name) {
				$msg = "請選擇文件。";
			} else if (@is_dir($savePath) === false) {
				$msg = "上傳目錄不存在。";
			} else if (@is_writable($savePath) === false) {
				$msg = "上傳目錄沒有寫入權限。";
			} else if (@is_uploaded_file($tmp_name) === false) {
				$msg = "上傳失敗。";
			} else {
				$dir_name = 'images';
	
				if (empty($ext_arr[$dir_name])) {
					$msg = "檔案路徑錯誤。";
				} else {
					$temp_arr = explode(".", $file_name);
					$file_ext = array_pop($temp_arr);
					$file_ext = trim($file_ext);
					$file_ext = strtolower($file_ext);
	
					if (in_array($file_ext, $ext_arr[$dir_name]) === false) {
						$msg = "上傳文件副檔名是不允許的副檔名。\n只允許" . implode(",", $ext_arr[$dir_name]) . "格式。";
					} else {
						if ($dir_name !== '') {
							$savePath .= $dir_name . "/";
							$saveUrl .= $dir_name . "/";
							if (!file_exists($savePath)) {
								mkdir($savePath);
							}
						}
						$ymd = date("Ymd");
						$savePath .= $ymd . "/";
						$saveUrl .= $ymd . "/";
						if (!file_exists($savePath)) {
							mkdir($savePath);
						}
	
						$new_file_name = date("YmdHis") . '_' . rand(10000, 99999) . '.' . $file_ext;
	
						$file_path = $savePath . $new_file_name;
	
						if (move_uploaded_file($tmp_name, $file_path) === false) {
							$msg = "上傳文件失敗。";
						} else {
							chmod($file_path, 0755);
							$fileUrl = $saveUrl . $new_file_name;
							$data = ['error' => 0, 'url' => $fileUrl];
						}
					}
				}
			}

			if($msg === null){
				$result = ["error" => 0, "url" => $fileUrl];
			}else{
				$result = ["error" => 1, "message" => $msg];
			}
			echo json_encode( $result );
			exit();
		}
	}
}
?>