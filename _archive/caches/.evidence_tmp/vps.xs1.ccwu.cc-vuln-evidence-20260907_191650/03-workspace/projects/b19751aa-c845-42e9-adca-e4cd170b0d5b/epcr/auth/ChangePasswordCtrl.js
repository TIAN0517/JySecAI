CONTROLLERS.controller('ChangePasswordCtrl', function($scope, $state, PUBLIC_CONFIG,
 $http, AlertServices, $window){
	$scope.PASSWORD_MIN_AGE = moment.duration(PUBLIC_CONFIG.PASSWORD_MIN_AGE).format('d');
	$scope.PASSWORD_MAX_AGE = moment.duration(PUBLIC_CONFIG.PASSWORD_MAX_AGE).format('d');
	$scope.MAX_PASSWORD_HISTORY = PUBLIC_CONFIG.MAX_PASSWORD_HISTORY;

	$scope.data = {}

	$scope.changePassword = changePassword;
	$scope.goBack = goBack;

	function changePassword(data){
		return $http.put('/Users/changePassword',{
			account: data.account,
			oldPassword: data.oldPassword,
			newPassword: data.newPassword,
			newPasswordConfirmation: data.newPasswordConfirmation
		})
		.then(function(response){
			console.log(response.data)
			AlertServices.successAlert('完成','密碼已修改')
			$scope.data = {};
		})
		.catch(function(err){
			var message = err.data.message ? err.data.message : err.data
			AlertServices.failAlert('錯誤',message,5)
		})
	}

	function goBack(){
		$window.history.back();
	}
});