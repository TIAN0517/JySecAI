CONTROLLERS.controller('Login2FACtrl', function($scope, $state,
    $http, AlertServices, AuthService, PUBLIC_CONFIG) {

    $scope.data = {
        userToken: null
    }

    $scope.login = function(userToken) {
        AuthService.login2FA(userToken)
            .catch(function(error) {
                console.log(error);
                AlertServices.failAlert('登入錯誤', error.data.message)
            });

    }

});