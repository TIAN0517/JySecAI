CONTROLLERS.controller('OhcaCaseListCtrl', function($q, $modal, $scope, $state, $http, $element, $window, $document,
		NgTableParams, EPCRServices, AuthService) {
	// $scope.$emit('topBar.content', '案件回溯');
	const PCR_CLASSFICATION_OHCA = 1;

	$scope.responseList = [];

    $scope.record ={}

	var hospitalUuid;
	var currentUser = AuthService.getCurrentUser();
	// $scope.search = {};
	$scope.TOKEN = AuthService.getToken();

	let watchSet = []
	$scope.isItemChecked = false;

	let CATEGORY_ID_CENTER = 1;
	let CATEGORY_ID_QC = 2;

	$scope.BACKTRACK_TYPE_CENTER = 1;
	$scope.BACKTRACK_TYPE_QC = 2;

	let loginType = {
		admin: 0,
		center: 1,
		qc: 2
	}

	let LOGIN_TYPE;	// 0:               
	let G_ORIGIN = "*";

	getLoginType();
	defaultCondition();

	function getLoginType(){
		if(AuthService.checkPerm('EPCR_PAGE_BACKTRACK_ADMIN') == true){
			LOGIN_TYPE = loginType.admin;
		}else if(AuthService.checkPerm('EPCR_PAGE_BACKTRACK_CENTER') == true){
			LOGIN_TYPE = loginType.center;
		}else if(AuthService.checkPerm('EPCR_PAGE_BACKTRACK_QC') == true){
			LOGIN_TYPE = loginType.qc;
		} // else 咋辦？
	}

    function getDropDownList(onePcr, formVersionId){
    	onePcr.optionsData = {};

    	return getDropDownListByCode(formVersionId, 'OHCA23')
    	.then(function(result){
    		onePcr.optionsData.gcse = [];
    		assignDropDownData(onePcr.optionsData.gcse, result.data)
    	})
    	.then(function(){
    		return getDropDownListByCode(formVersionId, 'OHCA24')
	    	.then(function(result){
	    		onePcr.optionsData.gcsv = [];
	    		assignDropDownData(onePcr.optionsData.gcsv, result.data)
	    	})
    	})
    	.then(function(){
    		return getDropDownListByCode(formVersionId, 'OHCA25')
	    	.then(function(result){
	    		onePcr.optionsData.gcsm = [];
	    		assignDropDownData(onePcr.optionsData.gcsm, result.data)
	    	})
    	})
    	.then(function(){
    		return getDropDownListByCode(formVersionId, 'OHCA26')
	    	.then(function(result){
	    		onePcr.optionsData.cpc = [];
	    		assignDropDownData(onePcr.optionsData.cpc, result.data)
	    	})
    	})
    	.then(function(){
    		return getDropDownListByCode(formVersionId, 'OHCA28')
	    	.then(function(result){
	    		onePcr.optionsData.result = [];
	    		assignDropDownData(onePcr.optionsData.result, result.data)
	    	})
    	})
    }

    function assignDropDownData(destAry, srcList){
    	for(var i in srcList){
    		for(var j in srcList[i].FormAnswers){
    			destAry.push({
    				id: srcList[i].FormAnswers[j].id,
    				code: srcList[i].FormAnswers[j].code,
    				displayLabel: srcList[i].FormAnswers[j].displayLabel
    			})
    		}
    	}
    }

    function getDropDownListByCode(formVersionId, qCode){
    	return $http.get('/FormQuestionMap',{
    		params: {
    			code: qCode,
    			FormVersionId: formVersionId
    		}
    	})
    }

	function getBranchId(currentUser){
	    if(currentUser && currentUser.role){
	        if(currentUser.role=='BRANCH'){
	            return currentUser.customData;
	        }
	    }
	    return null;
	}

	function getPcrDoctorOrderStatus(){
		return $http.get('/PcrDoctorOrderStatus')
		.then(function(response){
			return response.data;
		})
	}

	function getAmbulanceList(branchId){
		return $http.get('/Ambulances/byUserRole',{
			params: {
				BranchId: branchId
			},
			paramSerializer: '$httpParamSerializerJQLike'
		})
		.then(function(response){
			return response.data;
		})
	}

	function setupAmbulanceList(branchId){
		return getAmbulanceList(branchId)
		.then(function(results){
			$scope.showAmbulances = _.keyBy(results, 'id');
		})
	}

	var currentBranchId = getBranchId(currentUser);
	$scope.currentBranchId = currentBranchId;
	if(currentBranchId){
		$scope.search.BranchId = currentBranchId;
	}

	console.log('CURRENT USER', currentUser);
	if (currentUser.role != 'HOSPITAL') {
		$scope.isHospital = false;
		hospitalUuid = null;
	} // if
	else {
		$scope.isHospital = true;
		hospitalUuid = currentUser.customData;
	} // else

	// $scope.search = {
	// 	isSimulation: false,
	// 	isRealTime: false
	// };

	// $scope.hasTPList = {
	// 	false: '否',
	// 	true: '是'
	// }
	function defaultCondition()
	{
		$scope.checkboxes = {
			checked: false,
			items: {}
		}
		$scope.search = {};
		$scope.search = {
			// FeatureChange 2021-08-31 取消時間範圍的限制
			// WorkAround 2022-11-22 loading ，後端分頁寫法必須調整，載入太久
			dateBegin: moment().startOf('day').toDate(),
			dateEnd: moment().endOf('day').toDate(),
			isSimulation: false,
			isRealTime: false,
			ohcaBacktrackingMode: 0,
			defaultDateRange: true,
			PcrClassificationId: PCR_CLASSFICATION_OHCA,
			withFormBundle: true	
		};

		//  BACKTRACK_TYPE_CENTER, BACKTRACK_TYPE_QC
		if(LOGIN_TYPE == loginType.admin){
			$scope.search.backtrackFrom = 0;
		}else if(LOGIN_TYPE == loginType.center){
			$scope.search.backtrackFrom = $scope.BACKTRACK_TYPE_CENTER;
		}else if(LOGIN_TYPE == loginType.qc){
			$scope.search.backtrackFrom = $scope.BACKTRACK_TYPE_QC;
		}
	}

	$scope.clear = function() {
		defaultCondition();
		$scope.searchCase($scope.search);
		// refreshList();
	}

	$scope.searchCaseConfirm = function(objSearch) {
		if(objSearch.defaultDateRange == true){
			objSearch.defaultDateRange = false;
		}

		$scope.searchCase(objSearch)
	}

	$scope.searchCase = function(objSearch) {
		// FeatureChange 2021-08-31 取消時間範圍的限制
		// if ((objSearch.dateBegin && _.isNil(objSearch.dateEnd)) || (_.isNil(objSearch.dateBegin) && objSearch.dateEnd)) {
		// 	return EPCRServices.failAlert('錯誤！', '請輸入起迄區間！', null)
		// }

		$scope.tableParams = tableInit(objSearch);
	}


	function dataInit() {
		return $http.get('/config')
	    .then(function(response){
	        G_ORIGIN = response.data.hostname + ':' + response.data.port;
	        return $http.get('/Branches')
	    })
			.then(function(response) {
				//分隊清單
				$scope.showBranches = _.keyBy(response.data, 'id')
				return $http.get('/Hospitals')
			})
			.then(function(response) {
				//醫院清單
				$scope.showHospitals = _.keyBy(response.data, 'uuid')
				return $http.get('/PcrClassification')
			})
			.then(function(response) {
				//案件類別
				$scope.showPcrClassifications = _.keyBy(response.data, 'id')
				return $http.get('/')
			})
			.then(function(response) {
				//案件狀態
				$scope.showStatus = _.keyBy(response.data, 'id')
				return $http.get('/json/hasTP.json')
			})
			.then(function(response) {
				//TP狀態
				$scope.showTPStatus = _.keyBy(response.data, 'id')
				//只取用10000~19999 與CaseRecord 有關的狀態
				return $http.get('/Statuses?code[$between][0]=10000&code[$between][1]=19999')
			})
			.then(function(response) {
				$scope.showStatuses = _.keyBy(response.data, 'id');
				return $http.get('/json/isSimulation.json')
			})
			.then(function(response) {
				$scope.showSimulation = _.keyBy(response.data, 'id');
				return setupAmbulanceList()
			})
			.then(function(){
				return getPcrDoctorOrderStatus();
			})
			.then(function(results){
				$scope.PcrDoctorOrderStatusList = results;
			})
			.then(function(){
				$scope.ohcaModeList = [
					{ id: 0, name: '未填寫'},
					//{ id: 1, name: '有填寫'},
					{ id: 2, name: '追蹤中'},
					{ id: 3, name: '已完成'}
				]
			})
			.then(function(){
				defaultCondition();
				$scope.searchCase($scope.search);
			})
	}
	dataInit();


	
	// OHCA29 出院日期
	$scope.$watch('record.OHCA29', function(newValue,oldValue){ 
		console.log("$scope.record.OHCA29=",$scope.record.OHCA29)
		// 治療狀態會自動帶入出院日期，再由這邊計算住院天數、統計月份，避免形成事件迴圈
		if(!_.isNil($scope.record) && !_.isNil($scope.record.OHCA29) && !_.isNil($scope.record.idx)){

			var oneCase = $scope.responseList[$scope.record.idx];
			console.log("oneCase=",oneCase)
			// 住院天數
			if(!_.isNil(oneCase.arrivedHospitalAt)){
				$scope.record.OHCA32 = moment($scope.record.OHCA29).startOf('day').diff(moment(oneCase.arrivedHospitalAt).startOf('day'), 'days');	// 自動計算 住院天數
			}
			// 統計月份
			$scope.record.OHCA33 = moment($scope.record.OHCA29).startOf('month').format("YYYY-MM-DD");	// 預設本月1號
		} 
	},true);

	function clearAdd() {

	}
	//------------------------------------------------------------------------------------------
  //出院日期視窗
  var setDateModal = $modal({
    scope: $scope,
    templateUrl: 'templates/modal/backtrackBeHospitalModal.html',
    animation: 'no-animation',
    placement: 'center',
    backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
    show: false,
    onHide: clearAdd
  });
  //GCS視窗
  var setGCSModal = $modal({
    scope: $scope,
    templateUrl: 'templates/modal/backtrackGCSModal.html',
    animation: 'no-animation',
    placement: 'center',
    backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
    show: false,
    onHide: clearAdd
  });

  $scope.showSetGCSModal = function (index) { 
		let runNext = false

		for(var i in $scope.responseList[index].FormBundles){
			if($scope.responseList[index].FormBundles[i].FormCategoryId == CATEGORY_ID_CENTER){
				runNext = true;
				break;
			}
		}

		if(runNext == true){
			$scope.record = _.cloneDeep($scope.responseList[index].centerRecord);
			setGCSModal.$promise.then(setGCSModal.show);
		}else{
			EPCRServices.failAlert('錯誤！', '請先執行中心回溯', null);
		}
  }

  $scope.showSetDateModal = function (index) { 
		let runNext = false

		for(var i in $scope.responseList[index].FormBundles){
			if($scope.responseList[index].FormBundles[i].FormCategoryId == CATEGORY_ID_CENTER){
				runNext = true;
				break;
			}
		}

		if(runNext == true){
			$scope.record = _.cloneDeep($scope.responseList[index].centerRecord);
			setDateModal.$promise.then(setDateModal.show);
		}else{
			EPCRServices.failAlert('錯誤！', '請先執行中心回溯', null);
		}
		
  }

  function showLoading(){
    let deferred = $q.defer();
    $scope.anyPageBusy = deferred.promise;
    return deferred
  }
  //------------------------------------------------------------------------------------------
  $scope.saveTrackFromModal = function(idx){

  	$scope.responseList[idx].centerRecord = _.cloneDeep($scope.record);

  	$scope.saveTrack(idx, true)
  	.then(function(){
  		setDateModal.$promise.then(setDateModal.hide);
  	})
  }
  $scope.saveGCSFromModal = function(idx){

  	$scope.responseList[idx].centerRecord = _.cloneDeep($scope.record);

  	$scope.saveTrack(idx, true)
  	.then(function(){
  		setGCSModal.$promise.then(setGCSModal.hide);
  	})
  }
	//儲存追蹤記錄
	$scope.saveTrack = function(idx, isFromModal){
		// 收集資訊，組合成 formly.model 格式，呼叫 /updateTo/:FormBundleUuid 進行儲存
		/*
		 	param: 
		 		FormBundleUuid, 	
		 		isComplete: 有壓統計月份時為 true
		 		model: formly.model 格式，後端會對答案進行處理
		*/
		var loadingPromise = showLoading();
		var rowOneCase = $scope.responseList[idx];
		var centerFormBundleUuid = null;
		var idxCenterFormBundle = 0;
		var isComplete = false;	// 要判斷統計月份以決定 true / false

		// 取得中心回溯的 uuid & index
		for(var i in rowOneCase.FormBundles){
			if(rowOneCase.FormBundles[i].FormCategoryId == CATEGORY_ID_CENTER){
				centerFormBundleUuid = rowOneCase.FormBundles[i].uuid;
				idxCenterFormBundle = i;
				break;
			}
		}

		if(!_.isNil(centerFormBundleUuid)){
			// tarceDatas 寫回 FormBundles[idxCenterFormBundle].formlyModel.OHCA21				rowOneCase.tarceDatas
			rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA21 = [];
			rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA21 = _.cloneDeep(rowOneCase.tarceDatas);
			// 
			// 不需要判斷，因為 $scope.record & responseList.centerRecord 是連結在一起的
			// if(isFromModal==true){
				// 出院日期 OHCA29、統計月份 OHCA33、住院天數 OHCA32 填回 FormBundles[idxCenterFormBundle].formlyModel,   rowOneCase.centerRecord
				// 追蹤結果
				rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA28 = (!_.isNil(rowOneCase.centerRecord.OHCA28))? rowOneCase.centerRecord.OHCA28: null;
				// 出院日期
				rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA29 = (!_.isNil(rowOneCase.centerRecord.OHCA29))? rowOneCase.centerRecord.OHCA29: null;
				// 住院天數
				rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA32 = (!_.isNil(rowOneCase.centerRecord.OHCA32))? rowOneCase.centerRecord.OHCA32: null;
				// 統計月份
				rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA33 = (!_.isNil(rowOneCase.centerRecord.OHCA33))? rowOneCase.centerRecord.OHCA33: null;
			
			// }
			// 24,48,72 小時 GCS
			rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA7 = (!_.isNil(rowOneCase.centerRecord.OHCA7))? rowOneCase.centerRecord.OHCA7: null;
			rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA8 = (!_.isNil(rowOneCase.centerRecord.OHCA8))? rowOneCase.centerRecord.OHCA8: null;
			rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA9 = (!_.isNil(rowOneCase.centerRecord.OHCA9))? rowOneCase.centerRecord.OHCA9: null;

			// 有追蹤結果就算是完成，原本定義是用統計月份，但，死亡的話並不會填統計月份？所以 … 私自改成用追蹤結果
			if(!_.isNil(rowOneCase.centerRecord.OHCA28)){
				// #1919 有追蹤結果，自動標示為 已完成
				rowOneCase.FormBundles[idxCenterFormBundle].formlyModel.OHCA50 = 'OHCA50_2';
				// isComplete = true;
			}

			return $http.put('/FormBundles/updateTo/'+centerFormBundleUuid, {
	      		model: rowOneCase.FormBundles[idxCenterFormBundle].formlyModel,
	      // isComplete: isComplete	// 後端會判斷
	    })
	    .then(function(){
	    	EPCRServices.successAlert('通知！', '儲存成功', 1);
	    	// 要不要重整畫面更新資料呢？
	    })
	    .catch(function(err){
	    	EPCRServices.failAlert('錯誤！', err, null);
	    })
	    .finally(function(){
	    	loadingPromise.resolve();
	    })
		}else{
			EPCRServices.successAlert('通知！', '請先進行中心回溯資料填寫，可點擊中心回溯編輯按鈕進行編輯，謝謝', 1)
			// do nothing.
			loadingPromise.resolve();
			return $q.when();
		}
	}
		//新增一筆追蹤記錄
	$scope.addNewTrack = function(idx, rowData ){
		rowData.tarceDatas.push({
			"OHCA22": moment().toDate(),	// 追蹤日期
			"OHCA23": null,	// gcs e
			"OHCA24": null,	// gcs v
			"OHCA25": null, // gcs m
			"OHCA26": null, // cpc
			"OHCA27": null // 追蹤備註
		})
	}

	//刪除一筆追蹤記錄
	$scope.delOneTrack = function(idxTarceData,rowOneCase){
		rowOneCase.tarceDatas.splice(idxTarceData,1);	// 移除畫面上的項目
	}

	$scope.onOHCA28_Changed = function(caseIdx, selectedCode){
		var oneCase = $scope.responseList[caseIdx]

		if(selectedCode == 'OHCA28_1'){
			// result = MBD
			$scope.record.OHCA29 = moment().toDate();	// 預帶今日 出院日期
			// $scope.record.OHCA32 = moment().startOf('day').diff(moment(oneCase.DispatchRecord.dispatchedAt).startOf('day'), 'days');	// 自動計算 住院天數
			// $scope.record.OHCA33 = moment().startOf('month').format("YYYY-MM-DD");	// 預設本月1號
		}else if(selectedCode == 'OHCA28_3'){
			// result = AAD
			if(!_.isNil(oneCase.arrivedHospitalAt)){
				$scope.record.OHCA32 = moment().startOf('day').diff(moment(oneCase.arrivedHospitalAt).startOf('day'), 'days');	// 自動計算 住院天數
			}
			$scope.record.OHCA33 = moment().startOf('month').format("YYYY-MM-DD");	// 預設本月1號
		}
	}

	$scope.onPcrClassficationChanged = function(){
		if(!_.isNil($scope.search.PcrClassificationId)){
			var obj = _.find($scope.showPcrClassifications, function(o){
				return o.id == $scope.search.PcrClassificationId;
			})
			$scope.search.PcrClassificationName = obj.name;
		}else{
			$scope.search.PcrClassificationName = '所有類別'
		}

		$scope.searchCase($scope.search);
	}

	$scope.oneWeekNoBackTrack = function(){
		if($scope.search.defaultDateRange == true){
			// FeatureChange 2021-08-31 取消時間範圍的限制
			$scope.search.dateBegin = null;
			$scope.search.dateEnd = null;
			// $scope.search.dateBegin = moment().add(-730,'days').startOf('day').toDate();
			// $scope.search.dateEnd = moment().endOf('day').toDate();
			$scope.search.ohcaBacktrackingMode = 0;

			// FeatureAdd 2021-08-25 需根據登入權限調整鉤選的項目
			//  BACKTRACK_TYPE_CENTER, BACKTRACK_TYPE_QC
			if(LOGIN_TYPE == loginType.admin){
				$scope.search.backtrackFrom = 0;
			}else if(LOGIN_TYPE == loginType.center){
				$scope.search.backtrackFrom = $scope.BACKTRACK_TYPE_CENTER;
			}else if(LOGIN_TYPE == loginType.qc){
				$scope.search.backtrackFrom = $scope.BACKTRACK_TYPE_QC;
			}

			$scope.searchCase($scope.search);
		}else{
			// default search
			$scope.searchCase($scope.search);
		}
	}

	$scope.showDetail = function(index) {
		var pcrUuid = $scope.responseList[index].uuid;
		$window.open('/#/caseDetail/' + pcrUuid, '_blank');
	}

	$scope.showPrint = function(pcrUuid) {
		// var pcrUuid = $scope.responseList[index].uuid;
		$window.open('/#/caseDetailPrint/' + pcrUuid + '/' + 1, '_blank');
	}

	$scope.showTemsis = function(index){
		var pcrUuid = $scope.responseList[index].uuid;
		window.open('/#/caseTemsis/' + pcrUuid, '_blank');
	}

	$scope.branchChanged = function(branchId){
		setupAmbulanceList(branchId);
	}

	function tableInit(objSearch) {
		return new NgTableParams({
			page: 1, // show first page
			count: 10, // count per page,
			sorting: {
				// createdAt: 'desc'
			}
		}, {
			filterDelay: 300,
			getData: function(params) {
				var deferred = $q.defer();
				$scope.anyPageBusy = deferred.promise;
				console.log(params.sorting())
				var url = params.url();
				var limit = url.count,
					skip = url.count * (url.page - 1);
				var sortString;
				// 如果使用 epilogue 免費 api sort需要做調整
				// 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
				sortString = params.sorting();
				// for (var key in params.sorting()) {
				//     if (params.sorting()[key] == 'desc') {
				//         sortString = '-' + key;
				//     } else {
				//         sortString = key;
				//     }
				// }

				var query = {
					sort: sortString,
					offset: skip,
					count: limit,
					time: new Date().getTime()
				}
				
				if (!_.isEmpty(objSearch)) {
					for (var key in objSearch) {
						if(key == 'dateBegin' && !_.isNil(objSearch[key])){
							query[key] = moment(objSearch[key]).startOf('day').toDate();
						}else if(key == 'dateEnd' && !_.isNil(objSearch[key])){
							query[key] = moment(objSearch[key]).endOf('day').toDate();
						}else{
							query[key] = objSearch[key];
						}
					}
				}

				if (hospitalUuid) {
					query['HospitalUuid'] = hospitalUuid;
				} // if

				// FeatureAdd #1919 Jordan 2021-07-16 只列有送醫的
				query.isArrivedHospital = true;

				// console.log("query", query)

				return $http.get('/Pcrs/pcrCaseList', {
						params: query,
						paramSerializer: '$httpParamSerializerJQLike'
					})
					.then(function(response) { 
						var range = contentRange.parse(response.headers('Content-Range'));
						var count = range.length;
						params.total(count);
						$scope.responseList = response.data;
						deferred.resolve()
						$scope.extInfo = JSON.parse(response.headers('extInfo'));
						// console.log('@@ list=', $scope.responseList)
						$scope.checkboxes.items = {};
						$scope.isItemChecked = false;
						//
						// console.log('=============> $scope.responseList:',$scope.responseList)
						custSrcData($scope.responseList);
						return $scope.responseList
					})
					.catch(function(err) {
						deferred.resolve();
						console.log('tableInit err =', err)
					})

			}
		})
	}

	function custSrcData(ref_src){
		for(var i in ref_src){
			var oneCase = ref_src[i];
			oneCase.centerRecord = {};	// 記錄非 Repeat Section，中心回溯的結果 ( 這邊有預期 EPCR 不會有歷次記錄的狀況 )
			oneCase.tarceDatas = [];	// init
			
			for(var j in oneCase.FormBundles){
				var oneFormBundle = oneCase.FormBundles[j];
				if(oneFormBundle.FormCategoryId == CATEGORY_ID_CENTER){
					// get dropdown list
					getDropDownList(oneCase, oneFormBundle.FormVersionId);
					// oneCase.tarceDatas = [];
					// console.log('========= oneFormBundle.formlyModel:',oneFormBundle.formlyModel)
					for(var qCode in oneFormBundle.formlyModel){
						// 問題追蹤這個 Repeat Section
						if(qCode == 'OHCA21'){
							for(var k in oneFormBundle.formlyModel[qCode]){
								// key: questionCode, value: answerCode(string, date)
								oneCase.tarceDatas.push(oneFormBundle.formlyModel[qCode][k])
							}
						}else if(qCode == 'OHCA29' || qCode == 'OHCA33'){		// 29:康復出院 32:住院天數 33:統計月份
							if(!_.isNil(oneFormBundle.formlyModel[qCode])){
								oneCase.centerRecord[qCode] = moment(oneFormBundle.formlyModel[qCode]).toDate();
							}else{
								oneCase.centerRecord[qCode] = null;
							}
						// FeatureAdd 2021-09-01 24,48,72 小時GCS也要移到頁面編輯
						}else if(qCode == 'OHCA7' || qCode == 'OHCA8' || qCode == 'OHCA9'){		// 7:24小時 8:48小時 9:72小時
							if(!_.isNil(oneFormBundle.formlyModel[qCode])){
								oneCase.centerRecord[qCode] = oneFormBundle.formlyModel[qCode];
							}else{
								oneCase.centerRecord[qCode] = null;
							}
						}else if(qCode == 'OHCA32' || qCode == 'OHCA28' || qCode == 'PRE0'){		// 29:康復出院 32:住院天數 33:統計月份 28:追蹤結果
							// PRE0, PRE1 決定了後續會不會需要回答問題，所以需要它們來控制出院日期可不可以點選，因為會有連動關系
							// 若這邊不控制，填完出院日期再回到表單填寫，可能會發現出院日期消失了，比方該問題被隱藏時的狀況
							oneCase.centerRecord[qCode] = oneFormBundle.formlyModel[qCode];
						}else if(qCode == 'PRE1'){
							oneCase.centerRecord[qCode] = oneFormBundle.formlyModel[qCode];
							// FeatureAdd 2021-08-31 若為 到院急救 未滿三十分鐘，要用顏色區別
							if(oneFormBundle.formlyModel[qCode] == 'PRE1_2'){
								oneCase.isUnder30min = true;
							}else{
								oneCase.isUnder30min = false;
							}
						}
						oneCase.centerRecord.idx = i;
					}
				} // do nothing , 只處理 OHCA
			}
		}
	}

	// ============ 接收回溯填完關閉視窗的事件 ====== START
	function receiveMessage(event){
    if(event.data == 'addVisitDone.refresh' && event.origin == G_ORIGIN){
    	console.log('=====> GOT addVisitDone.refresh')
      $scope.searchCaseConfirm($scope.search);
      $scope.$apply();
    } // if
  } // receiveMessage function

  $document.ready(function(){
    $window.addEventListener("message", receiveMessage, false);
  })
  // ============ 接收回溯填完關閉視窗的事件 ====== END

	// watch for check all checkbox
	watchSet.push( 
		$scope.$watch(function() {
			return $scope.checkboxes.checked;
		}, function(value) {  
			angular.forEach($scope.responseList, function(item) {
				$scope.checkboxes.items[item.uuid] = value;
			});
		})
	)
	// watch for data checkboxes
	watchSet.push(
		$scope.$watch(function() {
			return $scope.checkboxes.items;
		}, function(values) {  
			var checked = 0,
				unchecked = 0,
				total = $scope.responseList.length;
			angular.forEach($scope.responseList, function(item) {
				checked += ($scope.checkboxes.items[item.uuid]) || 0;
				unchecked += (!$scope.checkboxes.items[item.uuid]) || 0;
			});
			if (total > 0 && ((unchecked == 0) || (checked == 0))) {
				console.log('checked=', checked, 'total=', total);
				$scope.checkboxes.checked = (checked == total);
			}
			// FeatureAdd 記錄是否有任何項目被鉤選
			if(checked > 0){
				$scope.isItemChecked = true;
			}else{
				$scope.isItemChecked = false;
			}

			// grayed checkbox
			angular.element($element[0].getElementsByClassName("select-all")).prop("indeterminate", (checked != 0 && unchecked != 0));
		}, true)
	)

	// 取得分隊id (若使用者屬於特定分隊，就只能查詢該分隊的案件

	$scope.goState = function goState(str, uuid){
		let dataToTrans = {
	      uuids: []
	    }

	    if(!_.isNil(uuid)){
	    	// 點選單一列
	    	dataToTrans.uuids.push(uuid);
	    }else{
	    	// 批次
	    	let items = $scope.checkboxes.items;
	    	angular.forEach(items, function(boolean, id){
		      if(boolean){
		        dataToTrans.uuids.push(id);
		      } // if
		    }) // angular.forEach
	    }

	  // FeatureChange 2021-08-31 為了維持前一頁的查詢條件，所以改成用 _blank 的方法
		if(str == 'center'){
			dataToTrans.categoryId = CATEGORY_ID_CENTER;
			$window.open('/#/centerBacktrack/' + JSON.stringify(dataToTrans), '_blank')
			// $state.go('centerBacktrack', dataToTrans)
		}else if(str == 'qc'){
			dataToTrans.categoryId = CATEGORY_ID_QC;
			$window.open('/#/qcBacktrack/' + JSON.stringify(dataToTrans), '_blank')
			// $state.go('qcBacktrack', dataToTrans)
		}// else do nothing
    }

    $scope.$on('$destroy', function(){
      if(watchSet.length > 0){
        angular.forEach(watchSet, function(call){
          call();
        })
      }
    })
});
