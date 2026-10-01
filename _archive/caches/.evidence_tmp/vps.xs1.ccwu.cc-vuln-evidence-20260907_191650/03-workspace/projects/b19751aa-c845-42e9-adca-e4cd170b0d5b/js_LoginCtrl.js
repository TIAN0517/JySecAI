CONTROLLERS.controller('LoginCtrl', function($scope, $state,
    $http, EPCRServices, AuthService, PUBLIC_CONFIG) {

    var captchaConfig = PUBLIC_CONFIG.captcha;
    $scope.captchaEnabled = captchaConfig.enable;

    function setCaptcha() {
        $scope.captchaImg = PUBLIC_CONFIG.authServer+captchaConfig.captchaImg+'?t=' + new Date().getTime();
    }
    setCaptcha();
    $scope.setCaptcha = setCaptcha;
    $scope.credentials = {
    	username: null,
    	password: null,
    	captcha: null
    }
    $scope.login = function(credentials) {
        AuthService.login(credentials)
            .catch(function(error) {
                console.log(error);
                EPCRServices.failAlert('登入錯誤', error.data.message)
                setCaptcha();
                // clear text
                $scope.credentials.captcha = null;
            });

    }

    function getVersion() {
        return $http.get('/version')
        .then(function(response) {
            $scope.version = response.data;
        })
    }
    getVersion();
    
    $scope.changePasswordUrl = PUBLIC_CONFIG.authServer + '/#/changepassword';
});