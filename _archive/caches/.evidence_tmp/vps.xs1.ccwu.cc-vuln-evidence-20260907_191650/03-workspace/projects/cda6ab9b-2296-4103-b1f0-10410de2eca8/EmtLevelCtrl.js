CONTROLLERS.controller('EmtLevelCtrl', function($q, $modal, $scope, $state,
	NgTableParams, $http, $element, EPCRServices) {

	var defaultSorting = {};
	var responseList = []

	var defaultParams = {
		//disabled: false
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

				// console.log(conditions);
				return $http.get('/emtlevels', {
						params: conditions,
						// paramSerializer: '$httpParamSerializerJQLike'
					})
					.then(function(response) {
						var range = contentRange.parse(response.headers('Content-Range'));
						var count = range.length;
						params.total(count);

						deferred.resolve()
						// console.log(response.data);
						return response.data
					})
					.catch(function(err) {
						deferred.resolve();
						console.log('tableInit err =', err)
					});
			}
		})
	}

	// ===============================================================================================

	// $scope.checkboxes = {
	// 	checked: false,
	// 	items: {}
	// }
	// // watch for check all checkbox
	// $scope.$watch(function() {
	// 	return $scope.checkboxes.checked;
	// }, function(value) {
	// 	angular.forEach(responseList, function(item) {
	// 		$scope.checkboxes.items[item.id] = value;
	// 	});
	// });
	// // watch for data checkboxes
	// $scope.$watch(function() {
	// 	return $scope.checkboxes.items;
	// }, function(values) {
	// 	var checked = 0,
	// 		unchecked = 0,
	// 		total = responseList.length;
	// 	angular.forEach(responseList, function(item) {
	// 		checked += ($scope.checkboxes.items[item.id]) || 0;
	// 		unchecked += (!$scope.checkboxes.items[item.id]) || 0;
	// 	});
	// 	if (total > 0 && ((unchecked == 0) || (checked == 0))) {
	// 		console.log('checked=', checked, 'total=', total);
	// 		$scope.checkboxes.checked = (checked == total);
	// 	}
	// 	// grayed checkbox
	// 	angular.element($element[0].getElementsByClassName("select-all")).prop("indeterminate", (checked != 0 && unchecked != 0));
	// }, true);

	// ===============================================================================================

	$scope.tableParams = tableInit();

	$scope.searchEmtLevel = function(searchParams) {
		customParams = angular.copy(defaultParams);

		if (!_.isNil(searchParams) && !_.isNil(searchParams.name)) {
			customParams['name'] = {
				$like: searchParams.name + '%'
			};
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

	var AddModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/emtLevelAdd.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------

	$scope.showAddModal = function() {
		AddModel.$promise.then(AddModel.show);
	};

	// -----------------------------------------------------------------------------------------------

	$scope.toAdd = function(valid, add) {
		// console.log(add);
		if (!valid) {
			return EPCRServices.failAlertToModal('錯誤!', '請輸入EMT證照名稱', null)
		} // if

		$http.post('/emtlevels', add)
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				AddModel.$promise.then(AddModel.hide);
			})
			.catch(function(err) {
				console.log('toAdd err =', err)
				EPCRServices.failAlertToModal('錯誤!', '請檢查EMT證照名稱是否已存在!', null);
			});
	};

	// ===============================================================================================

	var EditModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/emtLevelEdit.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------

	$scope.showEditModal = function(index) {
		$http.get('/emtlevels', {
				params: {
					id: $scope.tableParams.data[index].id
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
		.then(function(result) {
			if (result && !_.isEmpty(result.data))
			{
				$scope.edit = {
					newName: result.data[0].name,
					id: result.data[0].id
				};
				EditModel.$promise.then(EditModel.show);
			} // if
			else {
				EPCRServices.failAlert('錯誤!', '資料錯誤!', null);
				$scope.tableParams.reload();
			} // else
		})
		.catch(function(err) {
			console.log('showEditModel err =', err);
		});
	};

	// -----------------------------------------------------------------------------------------------

	$scope.toEdit = function(valid, edit) {
		if (!valid) {
			return EPCRServices.failAlertToModal('錯誤!', '請輸入EMT證照名稱', null)
		} // if

		$http.put('/emtlevels/' + edit.id, {
				name: edit.newName
			})
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				EditModel.$promise.then(EditModel.hide);
			})
			.catch(function(err) {
				console.log('toEdit err =', err)
				EPCRServices.failAlertToModal('錯誤!', '請檢查EMT證照名稱是否已存在!', null);
			});
	};

	// ===============================================================================================

	var DelModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/emtLevelDel.html',
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
		DelModel.$promise.then(DelModel.show);
	};

	// -----------------------------------------------------------------------------------------------

	$scope.toDel = function(del) {
		// console.log(del);
		$http.delete('/emtlevels/' + del.id)
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				DelModel.$promise.then(DelModel.hide);
			})
			.catch(function(err) {
				console.log('del branchgroup err =', err)
				EPCRServices.failAlertToModal('錯誤!', "刪除EMT證照資料失敗", null);
			});
	};

});
