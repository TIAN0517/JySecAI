CONTROLLERS.controller('BranchGroupCtrl', function($q, $modal, $scope, $state,
	NgTableParams, $http, $element, EPCRServices) {

	// var exampleModal = $modal({
	// 	scope: $scope,
	// 	templateUrl: 'templates/modal/exampleModal.html',
	// 	animation: 'no-animation',
	// 	placement: 'center',
	// 	backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
	// 	show: false,
	// 	//  onHide: refreshList
	// });

	$scope.showSelectModal = function(idx) {
		// $scope.edit = responseList[idx]
	};

	$scope.showDeleteModal = function(id) {
		// return $http.delete('/BranchGroups/' + id)
		// 	.then(function(response) {
		// 		console.log('delete result=', response.data)
		// 	})
		// 	.catch(function(err) {
		// 		console.log('delete err=', err)
		//
		// 	})
		// var chain = $q.when();
		// for(var key in $scope.checkboxes.items){
		//   if($scope.checkboxes.items[key]){
		//     chain = chain.then(function(id){
		//       return $http.delete('/BranchGroups/' + id)
		//     }.bind(null, key))
		//   }
		// }
		// return chain;
	};

	// $scope.checkboxes = {
	// 	checked: false,
	// 	items: {}
	// }

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
				$scope.SEQ = skip;
				if (!_.isEmpty(customParams)) {
					for (var key in customParams)
						conditions[key] = customParams[key];
				} // if
				// ------------------------------------------------------------------------

				return $http.get('/branchgroups', {
						params: conditions,
						// paramSerializer: '$httpParamSerializerJQLike'
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

	$scope.searchBranchGroup = function(searchParams) {
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

	var AddModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/branchGroupAdd.html',
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
		if (!valid) {
			return EPCRServices.failAlertToModal('錯誤!', '請輸入大隊名稱', null)
		} // if

		$http.post('/branchgroups', add)
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				AddModel.$promise.then(AddModel.hide);

			})
			.catch(function(err) {
				console.log('add branchgroup err =', err)
				EPCRServices.failAlertToModal('錯誤!', '請檢查大隊名稱是否已存在!', null);
			});
	};

	// ===============================================================================================

	var EditModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/branchGroupEdit.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------

	$scope.showEditModal = function(index) {
		$http.get('/branchgroups', {
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
					EditModel.$promise.then(EditModel.show);
				} // if
				else {
				 EPCRServices.failAlert('錯誤!', '資料錯誤!', null);
				 $scope.tableParams.reload();
				} // else
			})
			.catch(function(err) {
				console.log('showEditModel err =', err);
			})
		// EditModel.$promise.then(EditModel.show);
	};

	// -----------------------------------------------------------------------------------------------

	$scope.toEdit = function(valid, edit) {
		if (!valid) {
			return EPCRServices.failAlertToModal('錯誤!', '請輸入大隊名稱', null)
		} // if

		$http.put('/branchgroups/' + edit.id, {
				name: edit.newName
			})
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				EditModel.$promise.then(EditModel.hide);
			})
			.catch(function(err) {
				console.log('edit branchgroup err =', err)
				EPCRServices.failAlertToModal('錯誤!', '請檢查大隊名稱是否已存在!', null);
			});
	};

	// ===============================================================================================

	var DelModel = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/branchGroupDel.html',
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
		$http.delete('/branchgroups/' + del.id)
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				DelModel.$promise.then(DelModel.hide);
			})
			.catch(function(err) {
				console.log('del branchgroup err =', err)
				EPCRServices.failAlertToModal('錯誤!', '請檢查是否仍有分隊屬於此大隊!', null);
			});
	};
});
