CONTROLLERS.controller('MenuCtrl', function($http, $scope, AuthService) {
    function getConfig(){
        return $http.get('/config')
        .then(function(response){
            return response.data;
        });
    }

    $scope.menuTop = {};

    getConfig()
    .then(function(config){
        var token = AuthService.getToken();
        $scope.menuTop['hospitalCapabilityListUrl'] =
            config.HospitalServer+'/#/hospitalCapabilityList?token='+token;
        // $scope.menuTop['authServer'] = config.authServer+'/#/user?token='+token;
        $scope.menuTop['authServer'] = config.authServer+'/#/changepassword';
        if(config.statUrl){
            $scope.menuTop['statUrl'] = config.statUrl+'?token='+AuthService.getToken();
        }else{
            $scope.menuTop['statUrl'] = '/statIndex.html';
        }
        var home = config.hostname+':'+config.port+'/#/';
        $scope.menuTop['homeUrl'] = home + '?token='+AuthService.getToken();
        if(config.mciServer){
            $scope.menuTop['mciServer'] = config.mciServer + '?token=' + AuthService.getToken();
        }
    });

    var currentUser = AuthService.getCurrentUser();
    if(currentUser.role == 'HOSPITAL'){
        $scope.currentHospital = currentUser.customData;
    }else{
        $scope.currentHospital = null;
    }

});
