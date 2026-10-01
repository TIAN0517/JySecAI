<?php
require_once('model/config.php');
/*
$info = [
	'inv_phone' => '0916582068',
	'inv_password' => '$2y$10$7amL0HInjT3haMvaUxGgMub3k6vDPSrlCdX.kAKEXZVEb4Crwcb/O',
	'inv_short_quota' => 0,
	'inv_card_quota' => 0,
	'inv_area_quota' => 0,
	'inv_program' => '一般會員',
	'inv_remark' => '',
	'inv_expiry_time' => date("Y-m-d H:i:s"),
	'inv_last_login' => date("Y-m-d H:i:s"),
	'inv_create_time' => date("Y-m-d H:i:s"),
];

$sqlStatus = SQL::insert('investor', $info);
if($sqlStatus) {
	exit('OK');
} else {
	exit('帳號註冊發生錯誤');
}
/*
$articleCategory = array_reverse(articleCategory);
$postList = SQL::selectALL("SELECT * FROM `wp_posts` WHERE `post_type` LIKE 'post'");

foreach ($postList as $post) {
	$slug = model::slug($post['post_title']);
	$content = $post['post_content'];
	$createTime = $post['post_date'];

	$content = str_replace("<!-- wp:paragraph -->", "", $content);
	$content = str_replace("<!-- /wp:paragraph -->", "", $content);
	$content = str_replace("<!-- /wp:image -->", "", $content);
	$content = str_replace("wp-block-image", "", $content);
	$content = str_replace('<!-- wp:image {"id":' . ((int)$post['ID'] + 1) . '} -->', '', $content);
	$content = str_replace('<!-- wp:image {"id":' . ((int)$post['ID'] + 1) . ',"align":"center"} -->', '', $content);
	$content = str_replace('wp-image-' . ((int)$post['ID'] + 1) . '', '', $content);

	$artCategory = '借錢';
	foreach ($articleCategory as $value) {
		if(strpos($content, $value) !== false) {
			$artCategory = $value;
			break;
		}
	}

	$info = [
		'art_show' => 1,
		'art_top' => 0,
		'art_category' => $artCategory,
		'art_title' => $post['post_title'],
		'art_url' => $slug,
		'art_tag' => '',
		'art_content' => $content,
		'art_create_time' => $createTime
	];

	$sqlStatus = SQL::insert('article', $info);
}
*/
/*
$text = "0916582068";
$size = 18;
$box = imagettfbbox($size, 0, imgFont, $text);
$min_x = min( array($box[0], $box[2], $box[4], $box[6]) );
$max_x = max( array($box[0], $box[2], $box[4], $box[6]) );
$min_y = min( array($box[1], $box[3], $box[5], $box[7]) );
$max_y = max( array($box[1], $box[3], $box[5], $box[7]) );
$width  = ( $max_x - $min_x );
$height = ( $max_y - $min_y );
$img = imagecreate($width + 30, $height * 2);
imagecolorallocate($img, 0xff, 0xff, 0xff);
$black = imagecolorallocate($img, 0x7b, 0x7a, 0x7a);
imagettftext($img, $size, 0, 15, 25, $black, imgFont, $text);
//header('Content-Type: image/jpeg');
//imagejpeg($img);
ob_start ();
imagejpeg($img);
$image_data = ob_get_contents ();
ob_end_clean ();
$image_data_base64 = base64_encode ($image_data);
$base64_image = 'data:image/jpeg;base64,' . chunk_split($image_data_base64);
*/
?>