<?php
require_once('model/config.php');
$route = new Router(); //搭配 .htaccess 排除資料夾名稱後解析 URL

$pageHeader = "view/header.php";
$pageFooter = "view/footer.php";
$layout = indexLayout;

// 用參數決定載入某頁並讀取需要的資料
switch($route->getParameter(1)){
	case "action":
		include_once("routes/index.action.php");
		break;

	case "manage":
		include_once("routes/manage.page.php");
		break;

	default:
		include_once("routes/index.page.php");
		break;
}
$page = new page();
$pageTitle = ($pageTitle == '')? '速借款借錢網':$pageTitle;
$ogUrl = ($ogUrl == '')? nowUrl:$ogUrl;
$ogImage = ($ogImage == '')? siteRootUrl . 'docs/images/og-image.png':$ogImage;
require_once($layout);
?>
