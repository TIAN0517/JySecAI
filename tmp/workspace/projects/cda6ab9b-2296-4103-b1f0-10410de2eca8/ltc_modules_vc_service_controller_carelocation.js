app.factory('carelocationService', function (baseHttp) {
    return {
        queryCarelocation: function (params, callback) {
            return baseHttp.service('api_backend/queryCarelocation', params, callback);
        },
    }
})
app.controller('carelocationController', function ($rootScope, $scope, $window, $location, $http, $filter, $state, $modal, homeService, util, $sce,carelocationService) {
   
    $scope.queryCarelocation = function () {

        var param = {
            "carelocationId": 1
        };
        carelocationService.queryCarelocation(param, function (data, status, headers, config) {
            if (data.result) {
                $scope.carelocation = data.data;

                let regexp = /.*\/(.*)/;
                $scope.file = $scope.carelocation.fileMain.replace(regexp, '$1');

            }
        })
    };
    $scope.queryCarelocation();
   
})