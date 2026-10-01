app.factory('homeserviceService', function (baseHttp) {
    return {
        queryHomeservice: function (params, callback) {
            return baseHttp.service('api_backend/queryHomeservice', params, callback);
        },
    }
})
app.controller('homeserviceController', function ($rootScope, $scope, $window, $location, $http, $filter, $state, $modal, homeService, util, $sce,homeserviceService) {

    $scope.queryHomeservice = function () {

        var param = {
            "homeserviceId": 1
        };
        homeserviceService.queryHomeservice(param, function (data, status, headers, config) {
            if (data.result) {
                $scope.homeservice = data.data;

                let regexp = /.*\/(.*)/;
                $scope.file = $scope.homeservice.fileMain.replace(regexp, '$1');

            }
        })
    };
    $scope.queryHomeservice();
   
    
})