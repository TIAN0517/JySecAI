app.factory('daytimecareService', function (baseHttp) {
    return {
        queryDaytimecare: function (params, callback) {
            return baseHttp.service('api_backend/queryDaytimecare', params, callback);
        },
    }
})
app.controller('daytimecareController', function ($rootScope, $scope, $window, $location, $http, $filter, $state, $modal, homeService, util, $sce,daytimecareService) {

    $scope.queryDaytimecare = function () {

        var param = {
            "daytimecareId": 1
        };
        daytimecareService.queryDaytimecare(param, function (data, status, headers, config) {
            if (data.result) {
                $scope.daytimecare = data.data;

                let regexp = /.*\/(.*)/;
                $scope.file = $scope.daytimecare.fileMain.replace(regexp, '$1');

            }
        })
    };
    $scope.queryDaytimecare();
   
    
})