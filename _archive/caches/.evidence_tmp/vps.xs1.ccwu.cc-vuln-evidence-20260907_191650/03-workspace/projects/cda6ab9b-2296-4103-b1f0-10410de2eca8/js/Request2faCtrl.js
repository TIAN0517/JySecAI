CONTROLLERS.controller('Request2faCtrl', function($scope,
    $http, AlertServices) {

    function getOtp(){
        return $http.get('/tfa/requestOtp')
        .then(function(response){
            return response.data
        })
    }

    function setupOtp(){
        return getOtp()
        .then(function(otp){
            $scope.otpauthUrl = otp.otpauthUrl;
        })
    }

    function register(userToken){
        return $http.post('/tfa/register',{
            userToken: userToken
        })
        .then(function(response){
            var theModal = $scope.request2faData.theModal;
            AlertServices.successAlert('完成','已啟用雙因子認證')
            theModal.$promise.then(theModal.hide)
        })
        .catch(function(err){
            console.log(err);
            AlertServices.failAlert('錯誤', err.data.message)
        })
    }

    function init(){
        setupOtp()
        .catch(function(err){
            console.log(err);
            AlertServices.failAlert('錯誤', err.data.message)
            var theModal = $scope.request2faData.theModal;
            theModal.$promise.then(theModal.hide);

        })
    }

    $scope.data = {};
    $scope.setupOtp = setupOtp;
    $scope.register = register;

    init();
});