CONTROLLERS.controller('MonitorCtrl', function($q, $scope, $state, $modal,
 $http, AlertService, AuthService,NgTableParams) {

var defaultSorting = 'id';
	var responseList = []

	var defaultParams = {
		disabled: false
	};
	var customParams = angular.copy(defaultParams); // 前端輸入的查詢條件放這

	$scope.search = {
		HospitalId: null
	};

	$scope.tableParams = tableInit();

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
				return $http.get('/Monitors', {
						params: conditions,
						paramSerializer: '$httpParamSerializerJQLike'
					})
					.then(function(response) {
						var range = contentRange.parse(response.headers('Content-Range'));
						var count = range.length;
						params.total(count);

						deferred.resolve()
						return response.data
					})
					.catch(function(err) {
						deferred.resolve();
						console.log('tableInit err =', err)
					})
			}
		})
	}

	// ===============================================================================================
	function getDevices(){
		var params = {
			disabled: false,
			MonitorId: 'null'
		}

		return $http.get('/Devices',{
			params: params,
			paramSerializer: '$httpParamSerializerJQLike'
		})
		.then(function(response){
			return response.data;
		});
	}

    function getConfig() {
        return $http.get('/config')
            .then(function(response) {
                return response.data;
            });
    }

	function setupDeviceList(){
		return getDevices()
		.then(function(devices){
			$scope.DeviceList = devices;
		});
	}
	// ===============================================================================================

	$scope.doSearch = function(searchParams) {
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

		$scope.tableParams.reload();
	};

	// -----------------------------------------------------------------------------------------------

	$scope.clear = function() {
		$scope.search = {};
		$scope.ddlZipcodes = {};
		customParams = angular.copy(defaultParams);
		$scope.tableParams = tableInit();
	};

	// ===============================================================================================

	var AddModal = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/monitorAdd.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------
	// 顯示新增視窗
	$scope.showAddModal = function() {
		$scope.add = {}

		return setupDeviceList()
		.then(function(){
			AddModal.$promise.then(AddModal.show)
		});

	};

	// -----------------------------------------------------------------------------------------
	// 新增一筆資料
	$scope.toAdd = function(add) {
		return $http.post('/Monitors', add)
		.then(function(response){
			$scope.tableParams.reload();
			AddModal.$promise.then(AddModal.hide);
		})
		.catch(function(err) {
			console.log('showEditModal err =', err)
			AlertService.failAlert('錯誤!', '資料錯誤!')
		});
	};

	// ===============================================================================================

	function createEditModal(){
		return $modal({
			scope: $scope,
			templateUrl: 'templates/modal/monitorEdit.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static',
			show: false
		});
	}

	var EditModal = createEditModal();

	// -----------------------------------------------------------------------------------------------

	$scope.showEditModal = function(index) {
		var id = $scope.tableParams.data[index].id;
		$http.get('/Monitors/'+id)
			.then(function(response) {
				$scope.edit = response.data;
				return setupDeviceList();
			})
			.then(function(){
				EditModal.$promise.then(EditModal.show);
			})
			.catch(function(err) {
				console.log('showEditModal err =', err)
				AlertService.failAlert('錯誤!', '資料錯誤!', null)
				$scope.tableParams.reload();
			});
	};

	// ----------------------------------------------------------------------------------------------

	$scope.toEdit = function(edit) {
		var id = edit.id;
		if(edit.Device){
			edit.DeviceId = edit.Device.id;
		}
		return $http.put('/Monitors/'+id, edit)
		.then(function(){
			$scope.tableParams.reload();
			EditModal.$promise.then(EditModal.hide());
		})
		.catch(function(error){
			console.log(error);
			AlertService.failAlert('錯誤!','無法更新醫師');
		});
	};

	// ===============================================================================================

	var DelModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/monitorDel.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// ----------------------------------------------------------------------------------------------

	$scope.showDelModal = function(index) {
		$scope.del = {
			name: $scope.tableParams.data[index].name,
			id: $scope.tableParams.data[index].id
		};
		DelModel.$promise.then(DelModel.show);
	};

	// ----------------------------------------------------------------------------------------------

	$scope.toDel = function(del) {
		console.log('dellllllllll',del);
		$http.put('/Monitors/' + del.id, {
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

	// ----------------------------------------------------------------------------------------------
	$scope.enableMonitor = function(index){
		var id = $scope.tableParams.data[index].id;
		return $http.put('/Monitors/'+id, {
			disabled: false
		})
		.then(function(){
			$scope.tableParams.reload();
		});
	}

	$scope.unbindDevice = function(DeviceId){
		return $http.put('/Devices/'+DeviceId,{
			MonitorId: null
		})
		.then(function(response){
			EditModal.$promise.then(EditModal.hide);
			return $scope.tableParams.reload();
		})
		.catch(function(error){
			console.log(error, error.stack);
			AlertService.failAlertToModal('錯誤','解除綁定時發生錯誤')
		});
	}


});
