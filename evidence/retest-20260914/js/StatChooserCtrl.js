CONTROLLERS.controller('StatChooserCtrl', function($q, $modal, $scope, $state,
	NgTableParams, $http, $element, EPCRServices) {

	$scope.stat = {};
	$scope.statList = [
		{ name: '分隊救護主訴統計', state: 'stat1' },
		{ name: '分隊出勤統計報表', state: 'stat2' },
		{ name: '公務統計報表', state: 'stat3' },
		{ name: '各大隊呼吸道及進階呼吸道氣管內管(ENDO)使用品質指標', state: 'stat4' },
		{ name: '各大隊呼吸道及進階呼吸道喉罩呼吸道(LMA)使用品質指標', state: 'stat5' },
		{ name: '呼吸衰竭患者指標', state: 'stat6' },
		{ name: '各大隊TP(高級救護技術員，以下簡稱TP)施打50GW(藥物)品質指標', state: 'stat7' },
		{ name: '各大隊TP施打Einephrine(藥物)品質指標', state: 'stat8' },
		{ name: '本局暨各大隊救護反應時間分析表', state: 'stat9' },
		{ name: '到院前心肺功能停止案件使用AED(自動體外電擊器)之心律變化', state: 'stat10' },
		{ name: '各大隊血糖測量品質指標', state: 'stat11' },
		{ name: '各大隊TP給予支氣管擴張劑品質指標', state: 'stat12' },
		{ name: '疑似腦中風案件評估指標', state: 'stat13' },
		{ name: '疑似高能量撞擊或墜落傷案件創傷處置執行情況', state: 'stat14' },
		{ name: '各大隊TP施打Amiodarone(藥物)品質指標', state: 'stat15' },
		{ name: '各大隊低血壓施打靜脈輸液品質指標', state: 'stat16' },
		{ name: '本局OHCA救活率', state: 'stat17' },
		{ name: '嚴重燒燙傷患者施打IV指標報表', state: 'stat18' },
		{ name: '正壓給氣患者給予NPA(經鼻導管)或OPA(經口咽導管)指標報表', state: 'stat19' },
		{ name: '心搏過緩品管指標報表-執行十二導程心電圖執行正確率', state: 'stat20' },
		{ name: '心搏過緩品管指標報表-心搏過緩檢出率', state: 'stat21' },
		{ name: '主動脈剝離監測品管指標報表', state: 'stat22' },
		{ name: 'PCR正確率指標報表', state: 'stat23' },
		{ name: '創傷病患後送醫院品管指標', state: 'stat24' },
		{ name: 'TP Aspirin(藥物)使用指標報表', state: 'stat25' },
		{ name: 'TP NTG(藥物)使用指標報表', state: 'stat26' },
		{ name: '氧氣治療品管指標', state: 'stat27' },
		{ name: '非再吸入式面罩使用品管指標', state: 'stat28' },
		{ name: '甦醒球使用品管指標', state: 'stat29' },
		// { name: '行動急診室設備失效率報表', state: 'stat30' },
		// { name: '行動急診室設備平均故障間隔時間報表', state: 'stat31' },
		// { name: '行動急診室派遣率品質管理報表', state: 'stat32' },
		// { name: '行動急診室派遣正確率品質管理報表', state: 'stat33' },
		// { name: '行動急診室案件現場處置時間品質管理報表', state: 'stat34' },
		// { name: '行動急診室案件後送醫院統計報表', state: 'stat35' },
		// { name: '行動急診室後送醫院資料回填率報表', state: 'stat36' },
		// { name: '行動急診室重大創傷案件後送統計報表', state: 'stat37' },
		// { name: '行動急診室指導醫師接案率報表', state: 'stat38' },
		// { name: '行動急診室MRX設備使用率統計報表', state: 'stat39' },
		// { name: '總表輸出', state: 'stat40' },
		{ name: '每日 OHCA 患者件數及相關報表', state: 'stat41' },
		{ name: '每日 OHCA 患者2小時存活率', state: 'stat42' },
		{ name: '每日 OHCA 患者24小時存活率', state: 'stat43' },
		{ name: '每日 OHCA 患者48小時存活率', state: 'stat44' },
		{ name: '每日 OHCA 患者72小時存活率', state: 'stat45' },
		{ name: '每日 OHCA 患者AED使用及電擊率報表', state: 'stat46' },
		{ name: '每日 OHCA 患者AED審查報表', state: 'stat47' },
		{ name: '每日 OHCA 患者康復出院率', state: 'stat48' },
		{ name: '每日 OHCA 患者追蹤紀錄報表', state: 'stat49' },
		{ name: '每日醫院端扣床及滿床報表', state: 'stat50' },
		{ name: '每日/月醫院後送統計報表', state: 'stat51' },
		{ name: '救護車交通事故統計報表', state: 'stat52' }

	]

	$scope.changeStat = function(stat){
		if(stat){
			$state.go(stat.state);
		}
	}

});
