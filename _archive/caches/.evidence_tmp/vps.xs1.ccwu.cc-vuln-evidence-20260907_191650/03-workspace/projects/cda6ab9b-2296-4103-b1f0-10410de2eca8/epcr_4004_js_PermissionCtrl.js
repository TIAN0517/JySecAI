CONTROLLERS.controller('PermissionCtrl', function($q, $modal, $scope, $state,
	NgTableParams, $http, $element, AlertServices) {

	var defaultSorting = {};
	var responseList = []

	var defaultParams = {
		disabled: false
	}; // 此網頁只有一個查詢, 預設查詢條件放這
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
				// sortString = params.sorting();
				for (var key in params.sorting()) {
					if (params.sorting()[key] == 'desc') {
						sortString = '-' + key;
					} else {
						sortString = key;
					}
				}

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

				return $http.get('/Permissions', {
						params: conditions,
						paramSerializer: '$httpParamSerializerJQLike'
					})
					.then(function(response) {
						var range = contentRange.parse(response.headers('Content-Range'));
						var count = range.length;
						params.total(count);

						deferred.resolve()
						responseList = response.data;
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

	$scope.tableParams = tableInit();

	$scope.searchPermission = function(searchParams) {
		if (!_.isNil(searchParams)) {
			customParams = angular.copy(defaultParams);
			for (var key in searchParams) {
				if (searchParams[key] != '' && !_.isNil(searchParams[key]))
					customParams[key] = searchParams[key];
			} // for
		} // if

		$scope.tableParams = tableInit();
	};

	// -----------------------------------------------------------------------------------------------

	$scope.clear = function() {
		$scope.search = {};
		customParams = angular.copy(defaultParams);
		$scope.tableParams = tableInit();
	};

	// ===============================================================================================

	var AddModal = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/permissionAdd.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------

	$scope.showAddModal = function() {
		AddModal.$promise.then(AddModal.show);
	};

	// -----------------------------------------------------------------------------------------------

	$scope.toAdd = function(valid, add) {
		if (!valid) {
			return AlertServices.failAlertToModal('錯誤!', '請輸入頁面權限名稱', null)
		} // if

		$http.post('/Permissions', add)
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				AddModal.$promise.then(AddModal.hide);

			})
			.catch(function(err) {
				console.log('add Permissions err =', err)
				AlertServices.failAlertToModal('錯誤!', '請檢查頁面權限名稱是否已存在!', null);
			});
	};

	// ===============================================================================================

	var EditModal = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/permissionEdit.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------

	$scope.showEditModal = function(index) {
		$http.get('/Permissions', {
				params: {
					id: $scope.tableParams.data[index].id,
					disabled: false
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
			.then(function(result) {
				if (result && !_.isEmpty(result.data)) {
					$scope.edit = {
						newName: result.data[0].name,
						id: result.data[0].id
					};
					EditModal.$promise.then(EditModal.show);
				} // if
				else {
				 AlertServices.failAlert('錯誤!', '資料錯誤!', null);
				 $scope.tableParams.reload();
				} // else
			})
			.catch(function(err) {
				console.log('showEditModel err =', err);
			})
		// EditModal.$promise.then(EditModal.show);
	};

	// -----------------------------------------------------------------------------------------------

	$scope.toEdit = function(valid, edit) {
		if (!valid) {
			return AlertServices.failAlertToModal('錯誤!', '請輸入頁面權限名稱', null)
		} // if

		$http.put('/Permissions/' + edit.id, {
				name: edit.newName
			})
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				EditModal.$promise.then(EditModal.hide);
			})
			.catch(function(err) {
				console.log('edit Permissions err =', err)
				AlertServices.failAlertToModal('錯誤!', '請檢查頁面權限名稱是否已存在!', null);
			});
	};

	// ===============================================================================================

	var DelModal = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/permissionDel.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------

	$scope.showDelModal = function(index) {
		$scope.del = {
			name: $scope.tableParams.data[index].name,
			id: $scope.tableParams.data[index].id
		};
		DelModal.$promise.then(DelModal.show);
	};

	// -----------------------------------------------------------------------------------------------

	$scope.toDel = function(del) {
		// console.log(del);
		$http.delete('/Permissions/' + del.id)
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				DelModal.$promise.then(DelModal.hide);
			})
			.catch(function(err) {
				console.log('del Permissions err =', err)
				AlertServices.failAlertToModal('錯誤!', '請檢查是否仍有角色屬於此頁面權限!', null);
			});
	};

    /* 離開時關閉 modal */
    $scope.$on('$destroy', function(){
        AddModal.$promise.then(AddModal.hide);
        EditModal.$promise.then(EditModal.hide);
        DelModal.$promise.then(DelModal.hide);
    });

});
