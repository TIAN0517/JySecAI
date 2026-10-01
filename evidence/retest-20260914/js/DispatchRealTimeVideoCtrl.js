CONTROLLERS.controller('DispatchRealTimeVideoCtrl', function ($q, $scope, $rootScope, $http) {
    console.log('DISPATCH REAL TIME VIDEO CTRL');

    $scope.init = init;
    var PUBLIC_CONFIG = {};
    // ========================================================================
    function init(uuid) {
        $scope.vm = {};
        $scope.uuid = uuid;

        var deferred = $q.defer();
        $scope.anyPageBusy = deferred.promise;

        return getConfig()
            .then(function () {
                return setEPCRInfoByPcrUuid($scope.uuid);
            })
            .then(function () {
                setVideoUrl();
                deferred.resolve();
            })
            .catch(function (error) {
                deferred.resolve();
                console.error(error);
            });
    } // init()

    function setVideoUrl() {
        var realTimeVideoSets = [];
        if ($scope.vm.pcrInfo.DispatchRecordUuid) {
            for (var key in PUBLIC_CONFIG.RealTimeVideoPath) {
                realTimeVideoSets.push({
                    name: key,
                    url: PUBLIC_CONFIG.RealTimeVideoPath[key].path.replace('${dispatchRecordUuid}', $scope.vm.pcrInfo.DispatchRecordUuid),
                    type: PUBLIC_CONFIG.RealTimeVideoPath[key].type,
                    isLive: PUBLIC_CONFIG.RealTimeVideoPath[key].isLive
                })
            } // for
        } // if

        $scope.vm.realTimeVideoSets = realTimeVideoSets;
    } // setVideoUrl()
    // ========================================================================
    function setEPCRInfoByPcrUuid(pcrUuid) {
        return getEPCRInfoByPcrUuid(pcrUuid)
            .then(function (pcrInfo) {
                $scope.vm.pcrInfo = pcrInfo;
            });
    } // setEPCRInfoByPcrUuid()

    function getEPCRInfoByPcrUuid(pcrUuid) {
        return $http.get('/pcrOnly/' + pcrUuid)
            .then(function (response) {
                return response.data;
            });
    } // getEPCRInfoByPcrUuid()

    function getConfig() {
        return $http.get('/config')
            .then(function (response) {
                PUBLIC_CONFIG = response.data;
                return response.data;
            });
    } // getConfig()

});

app.directive('dispatchRealTimeVideo', function () {
    return {
        replace: true,
        restrict: 'E',
        scope: {
            uuid: '='
        },
        templateUrl: '/templates/dispatchRealTimeVideo.html',
        link: function (scope, element, attrs, ngModel) {
            scope.init(scope.uuid);
        },
        controller: 'DispatchRealTimeVideoCtrl'
    };
});