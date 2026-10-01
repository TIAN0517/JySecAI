CONTROLLERS.controller('HospitalCtrl', function($q, $scope, $state, $modal,
 $http, AlertService, AuthService,NgTableParams) {

var defaultSorting = {};
	var responseList = []

	var defaultParams = {
		disabled: false
	};
	var customParams = angular.copy(defaultParams); // 前端輸入的查詢條件放這

	function tableInit() {
		return new NgTableParams({
			page: 1, // show first page
			count: 10, // count per page,
			sorting: defaultSorting
		}, {
			filterDelay: 300,
			getData: function(params) {
				var deferred = $q.defer();
				$scope.anyPageBusy = deferred.promise;
				var url = params.url();
				var limit = url.count,
					skip = url.count * (url.page - 1);
				var sortString;
				// 如果使用 epilogue 免費 api sort需要做調整
				// 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
				sortString = params.sorting();
				// for (var key in params.sorting()) {
				// 	if (params.sorting()[key] == 'desc') {
				// 		sortString = '-' + key;
				// 	} else {
				// 		sortString = key;
				// 	}
				// }

				// ------------------------------------------------------------------------
				var conditions = {
					sort: sortString,
					offset: skip,
					count: limit,
					time: new Date().getTime()
				};

				if (!_.isEmpty(customParams)) {
					for (var key in customParams)
						conditions[key] = customParams[key];
				} // if
				// ------------------------------------------------------------------------

				console.log('conditions',conditions);
				return $http.get('/Hospitals', {
						params: conditions,
						paramSerializer: '$httpParamSerializerJQLike'
					})
					.then(function(HospitalsResponse) {
						var range = contentRange.parse(HospitalsResponse.headers('Content-Range'));
						var count = range.length;
						params.total(count);

						deferred.resolve()

					$http.get('/Hospitals/hospitalFullData', {
						paramSerializer: '$httpParamSerializerJQLike'
					})
					.then(function(HospitalFullresponse){

						angular.forEach(HospitalFullresponse.data, function(data){
							var Idx = _.findIndex(HospitalsResponse.data, ['name', data.HospitalName])
							if(Idx != -1) {
								HospitalsResponse.data[Idx]['isFull']=true
							}
						});
					})

						responseList = HospitalsResponse.data
						return HospitalsResponse.data
					})
					.catch(function(err) {
						deferred.resolve();
						console.log('tableInit err =', err)
					})
			}
		})
	}

	// ===============================================================================================

	$scope.Init = function() {
			// 區域
			return $http.get('/districts', {
				params: {
					disabled: false
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
			.then(function(response) {
				$scope.ddlDistricts = response.data;
				$scope.tableParams = tableInit();
			})
			.catch(function(err) {
				console.log('Init err =', err)
			});

	};

	$scope.Init();

	// ===============================================================================================

	$scope.selectedDistricts = function(districtId) {
		if (districtId == '' || _.isNil(districtId)) {
			return $scope.ddlZipcodes = [];
		} // if

		$http.get('/zipcodes', {
				params: {
					disabled: false,
					DistrictId: districtId
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
			.then(function(response) {
				$scope.ddlZipcodes = response.data;
				// console.log(response.data, $scope.ddlZipcodes);
			})
			.catch(function(err) {
				console.log('selectedDistricts err =', err)
			});
	};

	// ===============================================================================================

	$scope.searchBranch = function(searchParams) {
		if (!_.isNil(searchParams)) {
			customParams = angular.copy(defaultParams);

			for (var key in searchParams) {
				if (key == 'includeDisabled') {
					if (searchParams[key]) delete customParams['disabled'];
				} // if
				else if (searchParams[key] != '' && !_.isNil(searchParams[key])) {
					customParams[key] = searchParams[key];
				} // else if
			} // for
		} // if

		$scope.tableParams = tableInit();
	};

	// -----------------------------------------------------------------------------------------------

	$scope.clear = function() {
		$scope.search = {};
		$scope.ddlZipcodes = {};
		customParams = angular.copy(defaultParams);
		$scope.tableParams = tableInit();
	};

	// ===============================================================================================

	var AddModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/hospitalAdd.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------
	// 顯示新增視窗
	$scope.showAddModal = function() {
		$scope.add = {
			ddlDistricts: $scope.ddlDistricts
		};
		AddModel.$promise.then(AddModel.show)
	};

	// -----------------------------------------------------------------------------------------
	// 發生於縣市選擇時, 要帶入其所屬的鄉鎮市資料
	$scope.addSelectedDistricts = function(districtId) {
		if (districtId == '' || _.isNil(districtId)) {
			return $scope.add['ddlZipcodes'] = [];
		} // if

		$http.get('/zipcodes', {
				params: {
					disabled: false,
					DistrictId: districtId
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
			.then(function(response) {
				$scope.add['ddlZipcodes'] = response.data;
			})
			.catch(function(err) {
				console.log('addSelectedDistricts err =', err)
			});
	};

	// -----------------------------------------------------------------------------------------
	// 新增一筆資料
	$scope.toAdd = function(add) {
		var data = {};
		angular.copy(add, data)

		$http.post('/Hospitals', data)
			.then(function() {
				$scope.tableParams.reload();
			})
			.then(function() {
				AddModel.$promise.then(AddModel.hide);
			})
			.catch(function(err) {
				console.log('toAdd err =', err);
				AlertService.failAlertToModal('錯誤!', '無法新增醫院', null);
			});
	};

	// ===============================================================================================

	var EditModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/hospitalEdit.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------

	$scope.showEditModal = function(index) {
		$http.get('/Hospitals', {
				params: {
					uuid: $scope.tableParams.data[index].uuid
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
			.then(function(hospitalResult) {
				if (hospitalResult && !_.isEmpty(hospitalResult.data)) {
					$http.get('/zipcodes', {
							params: {
								disabled: false,
								DistrictId: hospitalResult.data[0].ZipCode.DistrictId
							},
							paramSerializer: '$httpParamSerializerJQLike'
						})
						.then(function(zipCodeResult) {
							$scope.edit = {
								uuid: hospitalResult.data[0].uuid,
								name: hospitalResult.data[0].name,
								telephone: hospitalResult.data[0].telephone,
								fax: hospitalResult.data[0].fax,
								address: hospitalResult.data[0].address,
								districtId: hospitalResult.data[0].ZipCode.DistrictId,
								ZipCodeId: hospitalResult.data[0].ZipCodeId,
								longitude: hospitalResult.data[0].longitude,
								latitude: hospitalResult.data[0].latitude,
								message: hospitalResult.data[0].message,
								isFirstAidResponsibilityHospital: hospitalResult.data[0].isFirstAidResponsibilityHospital,
								isEvacuationAccepted: hospitalResult.data[0].isEvacuationAccepted,
								ddlDistricts: $scope.ddlDistricts,
								ddlZipcodes: zipCodeResult.data,
								testMode: hospitalResult.data[0].testMode,
								consoleInstalled: hospitalResult.data[0].consoleInstalled
							};
							EditModel.$promise.then(EditModel.show);
						});
				} // if
				else {
					AlertService.failAlert('錯誤!', '資料錯誤!', null)
					$scope.tableParams.reload();
				} // else
			})
			.catch(function(err) {
				console.log('showEditModal err =', err)
			});
	};

	// ----------------------------------------------------------------------------------------------
	// 發生於縣市選擇時, 要帶入其所屬的鄉鎮市資料
	$scope.editSelectedDistricts = function(districtId) {
		console.log('districtId',districtId)
		if (districtId == '' || _.isNil(districtId)) {
			return $scope.edit['ddlZipcodes'] = [];
		} // if

		$http.get('/zipcodes', {
				params: {
					disabled: false,
					DistrictId: districtId
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
			.then(function(response) {
				$scope.edit['ddlZipcodes'] = response.data;
			})
			.catch(function(err) {
				console.log('editSelectedDistricts err =', err)
			});
	};

	// ----------------------------------------------------------------------------------------------

	$scope.toEdit = function(edit) {
		var data = {};
		angular.copy(edit, data);
		angular.forEach(data, function(value, key){
			if(value===''){
				data[key] = null;
			}
		});

		console.log('data', data);
		$http.put('/Hospitals/' + edit.uuid, data)
			.then(function() {
				$scope.tableParams.reload();
			})
			.then(function() {
				EditModel.$promise.then(EditModel.hide);
			})
			.catch(function(err) {
				console.log('toEdit err =', err);
				AlertService.failAlertToModal('錯誤!', '資料有誤', null);
			});
	};

	// ===============================================================================================

	var DelModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/hospitalDel.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// ----------------------------------------------------------------------------------------------

	$scope.showDelModal = function(index) {
		$scope.del = {
			name: $scope.tableParams.data[index].name,
			uuid: $scope.tableParams.data[index].uuid
		};
		DelModel.$promise.then(DelModel.show);
	};

	// ----------------------------------------------------------------------------------------------

	$scope.toDel = function(del) {
		console.log('dellllllllll',del);
		$http.put('/Hospitals/' + del.uuid, {
				disabled: true
			})
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				DelModel.$promise.then(DelModel.hide);
			})
			.catch(function(err) {
				console.log('toDel err =', err)
				AlertService.failAlertToModal('錯誤!', '刪除失敗!', null);
			});
	};

});
