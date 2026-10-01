app.controller('registerController', function ($scope, $rootScope, $location, $window, $state, $http, AuthenticationService) {

	$scope.userInfo = {
		userCode: null,
		userPw: null,
		userName: null,
		type: 0,
		device: 3
	}

	$scope.password = {
		userPwConfirmation: null
	}

	$scope.callRegister = function (valid) {
		if (valid) {
			$scope.userInfo.birthday = $('#birthday').val();
			if ($scope.password.userPwConfirmation == $scope.userInfo.userPw) {
				AuthenticationService.Register($scope.userInfo, function (data, status, headers, config) {
					if (data.res == 1) {
						alert("註冊成功");
						$state.go('login');
					} else {
						if (data.msg != null) {
							alert(data.msg);
						} else {
							alert("註冊失敗");
						}
					}
				})
			} else {
				alert("密碼不同");
			}
		}
	}

	$scope.goHome = function () {
		$state.go('home');
	}
})