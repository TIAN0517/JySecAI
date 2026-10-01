CONTROLLERS.controller('LogoutCtrl', function($scope, AuthService) {
	AuthService.logout();
})