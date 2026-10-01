app.factory('userAccountDetailService', function(baseHttp) {
	return {
		queryUserInfo: function(params, callback) {
			return baseHttp.service('api_app/queryUserInfo', params, callback);
		},
		saveUserInfo: function(params, callback) {
			return baseHttp.service('api_app/saveUserInfo', params, callback);
		},
		queryIDNumber: function(params, callback) {
			return baseHttp.service('api_backend/queryIDNumber', params, callback);
		}
	}
})
app.controller('userAccountDetailController', function($rootScope, $scope, $window, $location, $http, $filter, $state, $modal, userAccountDetailService, util, $sce) {

	$scope.rule = 0;
	idValid = true;

	if ($rootScope.isLogin == undefined) {
		$state.go('login');
	}



	$scope.userInfo = {
		userName: null,
		email: null,
		gender: null,
		cphoneNo: null,
		tphoneNo: null,
		birthday: null,
		addressCode: null,
		address: null,
		isNewspaper: null,
		userEnable: null,
	}

	$scope.queryAccountDetail = function() {
		let param = {
			userId: $rootScope.currentUser.usi
		};
		userAccountDetailService.queryUserInfo(param, function(data, status, headers, config) {
			if (data.result) {
				$scope.userInfo = data.data;

				$rootScope.currentUser.userName = data.data.userName;
				$rootScope.currentUser.userEnable = data.data.userEnable;
				$rootScope.currentUser.cphoneNo = data.data.cphoneNo;
				$rootScope.currentUser.tphoneNo = data.data.tphoneNo;
				$rootScope.currentUser.addressCode = data.data.addressCode;
				$rootScope.currentUser.address = data.data.address;

				if ($scope.userInfo.userEnable == 99) {
					$scope.checked = true;
				}

				$('#birthday').val($scope.userInfo.birthday);
			} else {
				$state.go('login');
			}
		})
	}
	$scope.queryAccountDetail();

	$scope.saveUserInfo = function(valid) {
		if ($scope.checked) {
			if (idValid) {
				if (valid) {

					$scope.userInfo.birthday = $('#birthday').val();
					$scope.userInfo.updatedBy = $rootScope.currentUser.usi;

					if ($rootScope.currentUser.userEnable == 0) {
						$scope.userInfo.userEnable = 99; //直接啟用
					}
					userAccountDetailService.saveUserInfo($scope.userInfo, function(data, status, headers, config) {
						if (data.result) {
							$scope.queryAccountDetail();
							$state.go('home');
							alert("儲存成功");

						}
					})

				} else {
					alert("有必填資料未填寫!");

				}
			} else {
				alert("此身分證已被註冊!");
			}
		} else {
			alert("會員條款須同意!");
		}
	}

	//查詢身分證
	$scope.queryIDNumber = function() {

		let param = {
			"idCard": $scope.userInfo.idCard
		};
		userAccountDetailService.queryIDNumber(param, function(data, status, headers, config) {
			
			if (data.result) {
				if (data.data.length > 0) {
					alert("此身分證已被註冊!");
					idValid = false;
				} else {
					idValid = true;
				}
			}
		})
	}

	$scope.goHome = function() {
		$state.go('home');
	}
	$scope.openRule = function() {
		$scope.rule = 1;
	}
	$scope.closeRule = function() {
		$scope.rule = 0;
	}

})