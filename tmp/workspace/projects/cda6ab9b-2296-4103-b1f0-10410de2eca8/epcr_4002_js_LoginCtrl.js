CONTROLLERS.controller('LoginCtrl', function($scope, $state,
    AuthService, PUBLIC_CONFIG) {

    var captchaConfig = PUBLIC_CONFIG.captcha;
    $scope.captchaEnabled = captchaConfig.enable;

    $scope.credentials = {
        username: null,
        password: null,
        captcha: null
    }
    function setCaptcha() {
        $scope.captchaImg = PUBLIC_CONFIG.authServer+captchaConfig.captchaImg+'?t=' + new Date().getTime();
    }
    setCaptcha();
    $scope.setCaptcha = setCaptcha;

    $scope.login = function(credentials) {
        AuthService.login(credentials)
            .catch(function(error) {
                console.log(error);
                alert('登入錯誤:'+error.data.message)
                setCaptcha();
            });

    }
});