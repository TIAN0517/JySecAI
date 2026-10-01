app.factory('serviceApplicationService', function (baseHttp) {
    return {
        saveServiceApplication: function (params, callback) {
            return baseHttp.service('api_backend/saveServiceApplication', params, callback);
        },
        queryDictionaryList: function (params, callback) {
			return baseHttp.service('api_backend/queryDictionaryList', params, callback);
		},
    }
})
app.controller('serviceApplicationController', function ($rootScope, $scope, $window, $location, $http, $filter, $state, $modal, homeService, util, $sce, serviceApplicationService) {
   
    $scope.saveServiceApplication = function (valid) {
        if (valid) {

            serviceApplicationService.saveServiceApplication($scope.serviceApplication, function (data, status, headers, config) {

                if (data.result) {
                    //$scope.uploadImage();
                    $state.reload();
                    alert("送出成功!");
                } else {
                    alert("送出失敗!");
                }

            });
        } else {
            alert("有必填資料未填!");
        }

    };

    $scope.regionList = {};

    //-- Query 地點列表
    var queryRegionList = function () {
        let searchRegionCondition = {
            dictionaryType: 3
        }
        serviceApplicationService.queryDictionaryList(searchRegionCondition, function (data, status, headers, config) {
            if (data.result) {
                $scope.regionList = data.data;
            } else {
                util.alert("失敗!");
            }
        })
    }

    queryRegionList();

});