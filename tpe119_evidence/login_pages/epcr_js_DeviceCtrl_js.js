CONTROLLERS.controller('DeviceCtrl',
	function($q, $modal, $scope, $state, $http, $element,
		NgTableParams, EPCRServices) {

		var defaultSorting = {};
		var responseList = []

		var defaultParams = {};
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

					// if ($scope.notlock) conditions['lock'] = false;
					// ------------------------------------------------------------------------

					// console.log(conditions);
					return $http.get('/devices/search', {
							params: conditions,
							// paramSerializer: '$httpParamSerializerJQLike'
						})
						.then(function(response) {
							var range = contentRange.parse(response.headers('Content-Range'));
							var count = range.length;
							params.total(count);

							// console.log(response.data);
							deferred.resolve()
							return response.data
						})
						.catch(function(err) {
							deferred.resolve();
							console.log('tableInit err =', err)
						})
				}
			})
		} // tableInit()

		// =============================================================================================

		// $scope.checkboxes = {
		// 	checked: false,
		// 	items: {}
		// };
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

		// =============================================================================================

		$scope.Init = function() {
			// 分隊名稱
			$http.get('/branches', {
					params: {
						disabled: false
					},
					paramSerializer: '$httpParamSerializerJQLike'
				})
				.then(function(response) {
					$scope.ddlBranches = response.data;
					return $http.get('/devicetypes', {});
				})
				.then(function(response) {
					$scope.ddlDeviceTypes = response.data;
				})
				.catch(function(err) {
					console.log('Init err =', err)
				});

			$scope.tableParams = tableInit();
		};

		$scope.Init();

		// =============================================================================================

		$scope.selectedBranches = function(branceId) {
			if (branceId == '' || _.isNil(branceId)) {
				return $scope.ddlAmbulances = [];
			} // if

			// console.log(branceId);
			$http.get('/ambulances', {
					params: {
						disabled: false,
						BranchId: branceId
					},
					paramSerializer: '$httpParamSerializerJQLike'
				})
				.then(function(response) {
					// console.log(response.data);
					$scope.ddlAmbulances = response.data;
				})
				.catch(function(err) {
					console.log('selectedBranches err =', err)
				});
		};

		// =============================================================================================

		$scope.searchDevice = function(searchParams) {
			if (!_.isNil(searchParams)) {
				customParams = angular.copy(defaultParams);
				for (var key in searchParams) {
					if (searchParams[key] != '' && !_.isNil(searchParams[key]))
						customParams[key] = searchParams[key];
				} // for
			} // if

			$scope.tableParams = tableInit();
		};

		// ---------------------------------------------------------------------------------------------

		$scope.clear = function() {
			$scope.search = {};
			$scope.ddlAmbulances = {};
			customParams = angular.copy(defaultParams);
			$scope.tableParams = tableInit();
		};

		// =============================================================================================

		var EditModel = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/deviceEdit.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static',
			show: false
		});

		// ---------------------------------------------------------------------------------------------

		$scope.showEditModal = function(index) {
			// console.log($scope.tableParams.data[index].Ambulance.id);
			$http.get('/devices/search', {
					params: {
						id: $scope.tableParams.data[index].id,
						lock: !$scope.notlock
					},
					paramSerializer: '$httpParamSerializerJQLike'
				})
				.then(function(deviceResult) {
					console.log(deviceResult);
					if (deviceResult && !_.isEmpty(deviceResult.data)) {
						$scope.edit = {};
						var edit = deviceResult.data[0];
						edit['ddlBranchs'] = $scope.ddlBranches;
						edit['ddlDeviceTypes'] = $scope.ddlDeviceTypes;
						edit['ddlAmbulances'] = [];

						if (!_.isNil(edit.Ambulance)) {
							return $http.get('/ambulances', {
									params: {
										BranchId: deviceResult.data[0].Ambulance.BranchId
									}
								})
								.then(function(ambulanceResult) {
									edit['branchId'] = deviceResult.data[0].Ambulance.BranchId;
									edit['ddlAmbulances'] = ambulanceResult.data;
									return edit;
								});
						} // if
						else {
							return edit;
						} // else
					} // if
					else {
						EPCRServices.failAlert('錯誤!', '資料錯誤!', null);
						$scope.tableParams.reload();
						throw '資料錯誤!';
					} // else
				})
				.then(function(edit) {
					$scope.edit = edit;
					EditModel.$promise.then(EditModel.show);
				})
				.catch(function(err) {
					console.log('showEditModal err =', err);
				});
		};

		// ---------------------------------------------------------------------------------------------
		// 發生於分隊選擇時, 要帶入其所屬的車輛資料
		$scope.selectedEditBranches = function(branchId) {
			// console.log(branchId);
			if (branchId == '' || _.isNil(branchId)) {
				return $scope.edit['ddlAmbulances'] = [];
			} // if

			$http.get('/ambulances', {
					params: {
						disabled: false,
						BranchId: branchId
					},
					paramSerializer: '$httpParamSerializerJQLike'
				})
				.then(function(response) {
					$scope.edit['ddlAmbulances'] = response.data;
				})
				.catch(function(err) {
					console.log('selectedBranches err =', err)
				});
		};

		// ---------------------------------------------------------------------------------------------

		$scope.toEdit = function(valid, edit) {
			// console.log(edit);
			var data = {};
			data['AmbulanceId'] = edit.AmbulanceId;
			data['DeviceTypeId'] = edit.DeviceTypeId;
			data['deviceId'] = edit.deviceId;
			data['pushToken'] = edit.pushToken;
			data['appId'] = edit.appId ? (edit.appId.length==0 ? null : edit.appId) : null;
			data['appVersionNo'] = edit.appVersionNo ? (edit.appVersionNo.length==0 ? null : edit.appVersionNo) : null;
			data['currentlongitude'] = edit.currentlongitude ? (edit.currentlongitude.length==0 ? null : edit.currentlongitude ) : null;
			data['currentlatitude'] = edit.currentlatitude ? (edit.currentlatitude.length==0 ? null : edit.currentlatitude ) : null;

			$http.put('/devices/' + edit.id, data)
				.then(function() {
					$scope.tableParams.reload();
				})
				.then(function() {
					EditModel.$promise.then(EditModel.hide);
				})
				.catch(function(err) {
					console.log('toEdit err =', err);
					if (!_.isNil(err.data) && !_.isEmpty(err.data.errors)) {
						EPCRServices.failAlertToModal('錯誤!', err.data.errors[0], null);
					} // if
					else {
						EPCRServices.failAlertToModal('錯誤!', "修改資料失敗", null);
					} // else
				});
		};

		// =============================================================================================

		var DelModel = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/deviceDel.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static',
			show: false
		});

		// ---------------------------------------------------------------------------------------------

		$scope.showDelModal = function(index) {
			$scope.del = {
				name: $scope.tableParams.data[index].deviceId,
				id: $scope.tableParams.data[index].id
			};
			DelModel.$promise.then(DelModel.show);
		};

		// ----------------------------------------------------------------------------------------------

		$scope.toDel = function(del) {
			// console.log(del);
			$http.delete('/devices/' + del.id)
				.then(function() {
					return $scope.tableParams.reload();
				})
				.then(function() {
					DelModel.$promise.then(DelModel.hide);
				})
				.catch(function(err) {
					console.log('toDel err =', err)
					EPCRServices.failAlertToModal('錯誤!', '請檢查此裝置是否仍在值勤中!', null);
				});
		};

		// =============================================================================================

		var AddModel = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/deviceAdd.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static',
			show: false
		});

		// ---------------------------------------------------------------------------------------------

		$scope.showAddModal = function() {
			$scope.add = {}
			$scope.add['ddlBranches'] = $scope.ddlBranches;
			$scope.add['ddlDeviceTypes'] = $scope.ddlDeviceTypes;
			console.log($scope.add);


			AddModel.$promise.then(AddModel.show);
		};

		$scope.selectedaddBranches = function(branchId) {
			$scope.add['ddlAmbulances'] = [];
			return $http.get('/ambulances', {
					params: {
						disabled: false,
						BranchId: branchId
					},
					paramSerializer: '$httpParamSerializerJQLike'
				})
				.then(function(response) {
					$scope.add['ddlAmbulances'] = response.data;
				})
				.catch(function(err) {
					console.log('selectedBranches err =', err)
				});
		};

		// ---------------------------------------------------------------------------------------------

		$scope.toAdd = function(add) {
			$http.post('/devices', {
				deviceId: add.deviceId,
				pushToken: add.pushToken,
				appId: add.appId ? (add.appId.length==0 ? null: add.appId) : null,
				appVersionNo: add.appVersionNo ? (add.appVersionNo.length==0 ? null : add.appVersionNo) : null,
				currentlongitude: add.currentlongitude ? (add.currentlongitude.length==0 ? null: add.currentlongitude) : null,
				currentlatitude: add.currentlatitude ? (add.currentlatitude.length==0 ? null: add.currentlatitude) : null,
				AmbulanceId: add.AmbulanceId,
				DeviceTypeId: add.DeviceTypeId
			})
				.then(function(result) {
					return $scope.tableParams.reload();
				})
				.then(function(result) {
					AddModel.$promise.then(AddModel.hide);
				})
				.catch(function(err) {
					console.log('add branchgroup err = ', err)
					EPCRServices.failAlertToModal('錯誤!', '新增裝置失敗!', null);
				});



			// $http.post('/branchgroups', add)
			// 	.then(function() {
			// 		return $scope.tableParams.reload();
			// 	})
			// 	.then(function() {
			// 		AddModel.$promise.then(AddModel.hide);
			//
			// 	})
			// 	.catch(function(err) {
			// 		console.log('add branchgroup err =', err)
			// 		EPCRServices.failAlertToModal('錯誤!', '請檢查大隊名稱是否已存在!', null);
			// 	});
		};
	});
