CONTROLLERS.controller('RoleCtrl', function($q, $modal, $scope, $state,
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

				return $http.get('/Roles', {
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

	$scope.searchRole = function(searchParams) {
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
		templateUrl: 'templates/modal/roleAdd.html',
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
			return AlertServices.failAlertToModal('錯誤!', '請輸入角色名稱', null)
		} // if

		$http.post('/Roles', add)
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				AddModal.$promise.then(AddModal.hide);

			})
			.catch(function(err) {
				console.log('add Roles err =', err)
				AlertServices.failAlertToModal('錯誤!', '請檢查角色名稱是否已存在!', null);
			});
	};

	// ===============================================================================================

	var EditModal = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/roleEdit.html',
		animation: 'no-animation',
		placement: 'center',
		backdrop: 'static',
		show: false
	});

	// -----------------------------------------------------------------------------------------------

	$scope.showEditModal = function(idx){
	   var Role;
	   console.log('responseList',responseList[idx]['id'])
	   $http.get('/Roles', {
	     params: {
	       id: responseList[idx]['id']
	     },
	     paramSerializer: '$httpParamSerializerJQLike'
	   })
	   .then(function(response){
	   	  console.log('#####response',response.data)
	  	   	$scope.edit = {
				newName: response.data[0].name,
				id: response.data[0].id
			};
	     if(response.data.length > 0){
	       Role = response.data[0].Permissions;
	       $scope.selectedRole = Role;

	       var permissionsIds = []
	       angular.forEach(Role, function(data){

	         permissionsIds.push(data.id)
	       })
		console.log('@@@@permissionsIds',permissionsIds)
	       return getPermission(permissionsIds)
	       .then(function(thePermissions){
	       	console.log('@@@@thePermissions',thePermissions)
	         $scope.permissionList = {
	           selected: null,
	           lists: {
	             "目前權限": Role,
	             "未啟用權限": thePermissions
	           }
	         }
	         EditModal.$promise.then(EditModal.show)
	       })
	     }else{
	       AlertServices.failAlert('錯誤！', '分隊已被刪除！', null);
	       refreshList()
	     }
	   })
	 }

	// -----------------------------------------------------------------------------------------------

	$scope.toEdit = function(valid, edit){
		if (!valid) {
			return AlertServices.failAlertToModal('錯誤!', '請輸入角色名稱', null)
		} // if
	   var insertData = [];
	   angular.forEach($scope.selectedRole, function(data){
	     insertData.push({PermissionId:data.id,RoleId: edit.id});
	   })

	   var deferred = $q.defer()
	   $scope.myPromise = deferred.promise

	   $http.post('/Roles/setRolePermissionMap/'+ edit.id, {
	   		insertData:insertData,
	   		name: edit.newName
	   })
	   .then(function(response){
	   	 $scope.tableParams.reload();
	     deferred.resolve()
	     EditModal.$promise.then(EditModal.hide)
	   })
	   .catch(function(err){
	     deferred.resolve()
	     console.log('setRolePermissionMap err=', err)
	   })
	 }

	// ===============================================================================================

	var DelModal = $modal({
		scope: $scope,
		templateUrl: 'templates/modal/roleDel.html',
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
		$http.delete('/Roles/' + del.id)
			.then(function() {
				return $scope.tableParams.reload();
			})
			.then(function() {
				DelModal.$promise.then(DelModal.hide);
			})
			.catch(function(err) {
				console.log('del Roles err =', err)
				AlertServices.failAlertToModal('錯誤!', '請檢查是否仍有角色屬於此頁面權限!', null);
			});
	};
	//-------------------------------------------------------------------------------------------------

	var getPermission = function(permissionsIds){
	   return $http.get('/Permissions', {
	     params: {
	       id: { $notIn: permissionsIds },
	       sort: 'name',
	       disabled: false
	     },
	     paramSerializer: '$httpParamSerializerJQLike'
	   })
	   .then(function(response){
	     return response.data
	   })
	 }
	 //-------------------------------------------------------------------------------------------------
    /* 離開時關閉 modal */
    $scope.$on('$destroy', function(){
        AddModal.$promise.then(AddModal.hide);
        EditModal.$promise.then(EditModal.hide);
        DelModal.$promise.then(DelModal.hide);
    });

});
