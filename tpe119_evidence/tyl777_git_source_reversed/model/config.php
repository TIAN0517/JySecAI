<?php
	define('siteVer'			, '1.4.2');

	define('rootPath'			, dirname(dirname(__FILE__)));
	error_reporting(E_ALL & ~E_NOTICE);
	// 設定時區、開啟SESSION
	date_default_timezone_set("Asia/Taipei");
	session_start();

	if(!is_file(rootPath . '/model/systemConfig.php')) {
		copy(rootPath . '/model/systemConfig.php.example', rootPath . '/model/systemConfig.php');
	}
	require_once(rootPath . '/model/systemConfig.php');		//系統環境變數

	// 系統參數設定
	define('siteName'			, '速借款借錢網');
	define('manageLayout'		, rootPath . '/view/manage.layout.php');						// 後台layout檔案位置與名稱
	define('indexLayout'		, rootPath . '/view/index.layout.php');							// 前台layout檔案位置與名稱
	define('line_token'			, 'xDiRhmrP4dGGTdm6iRvWVqqh37Qynllk8IejXzjw59s');	// 系統 line token
	define('siteRootUrl'		,  $_SERVER['REQUEST_SCHEME'] . '://' . $_SERVER ['HTTP_HOST'] . siteURL);	//系統網址
	define('nowUrl'				,  $_SERVER['REQUEST_SCHEME'] . '://' . $_SERVER ['HTTP_HOST'] . $_SERVER['REQUEST_URI']);	//系統網址

	// Line Developers
	define('lineChannelID'		, '1648561141');
	define('lineChannelSecret'	, '3699416e5e55735da366475ada563998');

	// 資料路徑-用於上傳檔案用 Abs[絕對路徑] Rel[相對路徑]
	define('noPhoto'				, siteURL . 'docs/images/photo.png');
	define('summerNotePathAbs'		, $_SERVER['DOCUMENT_ROOT'] . siteURL . 'docs/summerNote_img/');
	define('summerNotePathRel'		, siteURL . 'docs/summerNote_img/');
	define('cardPathAbs'			, $_SERVER['DOCUMENT_ROOT'] . siteURL . 'docs/card_images/');
	define('cardPathRel'			, siteURL . 'docs/card_images/');
	define('adPathAbs'				, $_SERVER['DOCUMENT_ROOT'] . siteURL . 'docs/left_images/');
	define('adPathRel'				, siteURL . 'docs/left_images/');
	

	define('cityArea' , 
		[
			'北北基' => ['台北', '新北', '基隆'],
			'桃竹苗' => ['桃園', '新竹', '苗栗'],
			'中彰投' => ['台中', '彰化', '南投'],
			'雲嘉南' => ['雲林', '嘉義', '台南'],
			'高屏' => ['高雄', '屏東'],
			'宜花東' => ['宜蘭', '花蓮' ,'台東']
		]
	);

	define('cardTag' , 
		['貸款', '當鋪', '借現金', '小額借款', '我要借錢', '如何借款', '易借款', '民間借款',
		'薪轉信貸', '快速借錢', '無工作借錢', '貸款代辦', '找保人', '代償高利', '借10萬', '當日撥款', '沒工作想借錢', '身分證借款條件', '小額貸款', '融資借款',
		'急借錢', '小額借錢', '網路借錢', '借貸', '借款', '土地一二胎', '房屋一二胎', '身分證借款', '門號換現金', '日仔會'
		,'房屋二胎', '土地二胎', '汽機車借款', '機車借款', '汽車借款', '支票借款', '證件借款', '債務整合']
	);

	define('articleCategory' , 
		['借錢', '借款', '借貸', '融資', '當鋪', '票貼', '二胎', '貸款', '小額借款', '汽機車借款']
	);

	// 載入模組
	require_once(rootPath . '/model/routerModel.php');	// 載入router model
	require_once(rootPath . '/model/phpPdo.php');		// 載入Pdo
	require_once(rootPath . '/model/methodModel.php');	// HTTP Method判斷模組
	require_once(rootPath . '/model/sqlModel.php');		// 載入SQL model
	require_once(rootPath . '/model/model.php');		// 載入通用model
	require_once(rootPath . '/model/manageModel.php');	// 載入後台model
	require_once(rootPath . '/model/imgcompress.php');	// 圖片壓縮
	require_once(rootPath . '/model/universalModel.php');

?>
