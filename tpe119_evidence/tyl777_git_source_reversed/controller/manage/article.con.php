<?php 
class page {
	public static function pageScript() { }

	public static function pageStyle() { }

	public static function pageContent() {
		$amount = 30;
		$id = (GET::text('id') == '')? '%':GET::text('id');
		$art_category = (GET::text('category') == '')? '%':GET::text('category');
		$art_title = GET::text('title');
		$page = GET::text('page', 1);
		$sql = "SELECT * FROM `article`
				WHERE (`art_id` LIKE '{$id}')
				AND (`art_title` LIKE '%{$art_title}%')
				AND (`art_category` LIKE '{$art_category}')
				AND `art_delete_time` IS NULL
				ORDER BY `art_top` DESC,`art_id` DESC";
		$total = SQL::selectTotal($sql);
		$getUrl =  str_replace('&page=' . $page , '', $_SERVER['QUERY_STRING']);
		$url = '?' . $getUrl . '&page=';
		$pageLink = manage::pagingLink($url, $page, $total, $amount);
		$query = SQL::selectPage($sql, $amount, $page);

		$tableInfo = [];
		$tableHead = [
			['width' => '70', 'text' => '顯示'],
			['width' => '70', 'text' => '置頂'],
			['width' => '70', 'text' => 'ID'],
			['width' => '150', 'text' => '類型'],
			['width' => '500', 'text' => '文章標題'],
			['width' => '70', 'text' => ''],
		];
		$functionBtn = [
			['text' => '新增', 'class' => 'plus', 'url' => siteRootUrl . 'manage/article/addData']
		];
		if(count($query) == 0) {
			$tableInfo[] = ['type' => 'nodata'];
		}else{
			foreach($query as $article) {
				$tableInfo[] = [
					'id' => $article['art_id'],
					['type' => 'show', 'text' => $article['art_show'], 'table' => 'article', 'field' => 'art_show', 'idField' => 'art_id'],
					['type' => 'checkbox', 'text' => $article['art_top'], 'table' => 'article', 'field' => 'art_top', 'idField' => 'art_id'],
					['type' => 'center', 'text' => $article['art_id'] ],
					['type' => 'center', 'text' => $article['art_category'] ],
					['type' => 'text', 'text' => $article['art_title'] ],
					['type' => 'function', 'info' => [
						['type' => 'url', 'url' => siteRootUrl . 'article/' . $article['art_url'], 'new' => true ],
						['type' => 'edit', 'url' => siteRootUrl . 'manage/article/editData/' . $article['art_id'] ],
						['type' => 'delete', 'url' => siteRootUrl . 'manage/article/deleteData/' . $article['art_id'] ],
					] ],
				];
			}
		}

		$articleCategory = model::setArrayKey(articleCategory);
		$articleCategory[''] = '所有類型';
		ksort($articleCategory);

		$inputInfo = [
			['type' => 'select', 'text' => '文章類型', 'name' => 'category', 'value' => [$articleCategory, GET::text('category')], 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => '文章ID', 'name' => 'id', 'value' => GET::text('id'), 'width' => [4, 6, 6] ],
			['type' => 'text', 'text' => '文章標題', 'name' => 'title', 'value' => GET::text('title'), 'width' => [4, 6, 6] ],
		];
		$html .= manage::searchForm($inputInfo, [], siteRootUrl . 'manage/article');

		$html .= manage::tableList($tableHead, $tableInfo, $functionBtn, $pageLink);

		return ['文章管理', $html];
	}

	public static function addData() {
		$articleCategory = model::setArrayKey(articleCategory);

		$inputInfo = [
			['text' => '文章顯示', 'type' => 'radio', 'name' => 'show', 'width' => [3, 6, 12],
			'other' => 'required', 'value' => [[1 => '顯示', 0 => '隱藏'], 1] ],

			['text' => '文章置頂', 'type' => 'radio', 'name' => 'top', 'width' => [3, 6, 12],
			'other' => 'required', 'value' => [[1 => '置頂', 0 => '不置頂'], 0] ],

			['text' => '文章類型', 'type' => 'select', 'name' => 'category', 'width' => [3, 12, 12],
			 'value' => [$articleCategory, ''], 'other' => 'required'],

			['text' => '發布日期', 'type' => 'datetime', 'name' => 'create_time', 'width' => [3, 6, 12],
			 'value' => date("Y-m-d H:i:s") ],

			['text' => '文章標題', 'type' => 'text', 'name' => 'title', 'width' => [12, 12, 12],
			'placeholder' => '請輸入文章標題', 'other' => 'required' ],

			['text' => '標籤', 'type' => 'text', 'name' => 'tag', 'width' => [12, 12, 12],
			'placeholder' => '請輸入標籤，並用 , 區隔，ex:借錢,借款,借貸' ],

			['text' => '文章內容', 'type' => 'summernote', 'name' => 'content', 'width' => [12, 12, 12],
			'placeholder' => '請輸入文章內容']
		];

		$submitURL = siteRootUrl . 'manage/article/actionAddData';
		$listURL = siteRootUrl . 'manage/article';
		$html = manage::submitForm($inputInfo, $submitURL, $listURL, '新增文章', '');
		return ['新增文章', $html];
	}
	
	public static function actionAddData() {
		$art_show = POST::int('show');
		$art_top = POST::int('top');
		$art_category = POST::text('category');
		$art_create_time = POST::datetime('create_time');
		$art_title = POST::text('title');
		$art_tag = POST::text('tag');
		$art_content = POST::html('content');

		$art_tag = self::sortOutTag($art_tag);
		
		$info = [
			'art_show' => $art_show,
			'art_top' => $art_top,
			'art_category' => $art_category,
			'art_title' => $art_title,
			'art_url' => model::slug($art_title),
			'art_tag' => $art_tag,
			'art_content' => $art_content,
			'art_create_time' => $art_create_time,
		];
		$sqlStatus = SQL::insert('article', $info);

		if($sqlStatus) {
			$artID = SQL::autoID();
			model::setLog('manage', '新增文章(' . $artID . ')', $info);
			exit('success');
		} else{
			model::setLog('error', 'manage-新增文章時發生錯誤', $info);
			model::sendLineToAdmin("manage-新增文章時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		exit;
	}

	public static function editData() {
		$id = Router::getParameter(4);
		$article = SQL::selectOne("SELECT * FROM `article` WHERE `art_id` = ? AND `art_delete_time` IS NULL", [$id] );
		if(!$article) {
			header('Location: ' . siteRootUrl . 'manage/article');
			exit;
		}

		$articleCategory = model::setArrayKey(articleCategory);
		$article['art_tag'] = json_decode($article['art_tag'], true);
		$article['art_tag'] = implode(",", $article['art_tag']);

		$inputInfo = [
			['name' => 'id', 'type' => 'hidden', 'value' => $id ],

			['text' => '文章顯示', 'type' => 'radio', 'name' => 'show', 'width' => [3, 6, 12],
			'other' => 'required', 'value' => [[1 => '顯示', 0 => '隱藏'], $article['art_show']] ],

			['text' => '文章置頂', 'type' => 'radio', 'name' => 'top', 'width' => [3, 6, 12],
			'other' => 'required', 'value' => [[1 => '置頂', 0 => '不置頂'], $article['art_top']] ],

			['text' => '文章類型', 'type' => 'select', 'name' => 'category', 'width' => [3, 12, 12],
			 'value' => [$articleCategory, $article['art_category']], 'other' => 'required'],

			['text' => '發布日期', 'type' => 'datetime', 'name' => 'create_time', 'width' => [3, 6, 12],
			 'value' => $article['art_create_time'] ],

			['text' => '文章標題', 'type' => 'text', 'name' => 'title', 'width' => [12, 12, 12],
			'placeholder' => '請輸入文章標題', 'other' => 'required', 'value' => $article['art_title'] ],

			['text' => '標籤', 'type' => 'text', 'name' => 'tag', 'width' => [12, 12, 12],
			'placeholder' => '請輸入標籤，並用 , 區隔，ex:借錢,借款,借貸', 'value' => $article['art_tag'] ],

			['text' => '文章內容', 'type' => 'summernote', 'name' => 'content', 'width' => [12, 12, 12],
			'placeholder' => '請輸入文章內容', 'value' => $article['art_content']]
		];

		$submitURL = siteRootUrl . 'manage/article/actionEditData';
		$listURL = siteRootUrl . 'manage/article';
		if(strpos($_SERVER['HTTP_REFERER'], $_SERVER['HTTP_HOST'] . $_SERVER['PHP_SELF'])) {
			$listURL = $_SERVER['HTTP_REFERER'];
		}
		$html = manage::submitForm($inputInfo, $submitURL, $listURL, '修改文章', '');
		return array('修改文章 - ' . $article['art_title'], $html);
	}

	public static function actionEditData() {
		$id = POST::text('id');
		$art_show = POST::int('show');
		$art_top = POST::int('top');
		$art_category = POST::text('category');
		$art_create_time = POST::datetime('create_time');
		$art_title = POST::text('title');
		$art_tag = POST::text('tag');
		$art_content = POST::html('content');

		$art_tag = self::sortOutTag($art_tag);

		$article = SQL::selectOne("SELECT * FROM `article` WHERE `art_id` = ?", [$id] );
		if(!$article) die('查無該文章資料');

		$info = [
			'art_show' => $art_show,
			'art_top' => $art_top,
			'art_category' => $art_category,
			'art_title' => $art_title,
			'art_url' => model::slug($art_title),
			'art_tag' => $art_tag,
			'art_content' => $art_content,
			'art_create_time' => $art_create_time,
			'art_update_time' => date("Y-m-d H:i:s"),
		];

		$sqlStatus = SQL::update('article', $info, ['art_id' => $id]);
		if($sqlStatus) {
			model::setLog('manage', '修改文章(' . $article['art_id'] . ')；原資料備份', $article);
			 exit('success');
		} else {
			model::setLog('error', 'manage-修改文章時發生錯誤', ['atag_total' => $total['titalCount']]);
			model::sendLineToAdmin("manage-修改文章時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		die;
	}

	public static function deleteData() {
		$id = Router::getParameter(3);
		$article = SQL::selectOne("SELECT * FROM `article` WHERE `id` = ?", [$id] );
		if(!$article) exit('查無資料');
		$ck = SQL::querySql('DELETE FROM `article` WHERE `id` = ?', [$id] );
		if($ck) {
			model::setLog('manage-article 刪除文章', $article);
			exit('success');
		} else {
			model::setLog('manage-article 刪除文章時發生錯誤', $article);
			model::sendLine(lineToken, "\r\nmanage-article\r\n刪除文章時發生錯誤\r\n" . siteRootUrl);
			die('資料修改時發生錯誤');
		}
		die;
	}

	public static function sortOutTag($tagText) {
		$tagList = explode(",", $tagText);
		SQL::begin();
		foreach ($tagList as $key => $tag) {
			$tagList[$key] = trim($tag);
			$selectTag = SQL::selectOne("SELECT * FROM `article_tag` WHERE `atag_name` = ?", [$tagList[$key]]);
			if(!$selectTag) {
				$sqlStatus = SQL::insert('article_tag', ['atag_name' => $tagList[$key]]);
				if(!$sqlStatus) {
					SQL::rollback();
					model::setLog('error', 'manage-新增文章標籤時發生錯誤', ['atag_name' => $tagList[$key]]);
					model::sendLineToAdmin("manage-新增文章標籤時發生錯誤\r\n" . siteRootUrl);
					die('資料修改時發生錯誤');
				}
			}
		}

		$allTag = SQL::selectAll("SELECT * FROM `article_tag`");
		foreach ($allTag as $tag) {
			$total = SQL::selectOne('SELECT count(*) AS `titalCount` FROM `article` WHERE `art_tag` LIKE \'%"' . $tag['atag_name'] . '"%\'');
			$sqlStatus = SQL::update('article_tag', ['atag_total' => $total['titalCount']], ['atag_id' => $tag['atag_id']]);
			if(!$sqlStatus) {
				SQL::rollback();
				model::setLog('error', 'manage-重新計算文章標籤時發生錯誤', ['atag_total' => $total['titalCount']]);
				model::sendLineToAdmin("manage-重新計算文章標籤時發生錯誤\r\n" . siteRootUrl);
				die('資料修改時發生錯誤');
			}
		}

		SQL::commit();
		return json_encode($tagList, JSON_UNESCAPED_UNICODE);

	}
}
?>