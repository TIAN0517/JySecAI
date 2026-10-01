CONTROLLERS.controller('MonitorCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices, $interval) {

    var exampleModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/exampleModal.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
        show: false,
        //  onHide: refreshList
    });

    $scope.checkboxes = {
        checked: false,
        items: {}
    }
    var defaultSorting = {};
    var responseList = []

    var hospitalDispatches = {};


    $scope.listNew = [{
        recordUuid: '1',
        video: "http://localhost:3000/sample.mp4"
    }, {
        recordUuid: '2',
        video: "https://www.w3schools.com/html/mov_bbb.mp4"
    }, {
        recordUuid: '3',
        video: "http://www.hdpvrcapture.com/hdpvrcapture/samples/20090228_085119-H.264.m2ts.mp4"
    }, {
        recordUuid: '4',
        video: "https://googlechrome.github.io/samples/muted-autoplay/chrome-clip.mp4"
    }]

    $scope.listOld = []

    function getConfig() {
        return $http.get('/config')
            .then(function(response) {
                return response.data;
            });
    }


    //rtmp://118.163.107.92/rtmp/live+Uuid
    function dataDispatchRecord() {
        return $http.get('/DispatchRecords', {
                params: {
                    StatusId: {
                        $in: [5,6,7,8]
                    }
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
            .then(function(response) {
                console.log('DispatchRecords response', response.data)
                return response
            })
            .catch(function(err) {
                console.log('err =', err)
            })
    }

    // function dataDispatchRecord(){

    //   return $http.get('http://60.250.126.139:3000/users?time=' + new Date().getTime())
    //   // return $q.when($scope.listNew);
    // }



    $scope.repeatList = []
    var videoIndex = 0
    var testIndex = 0;
    const MAX_LIST = 6;
    const REFRESH_PERIOD = 10000;
    getVideoList();

    var getVideoTimer = $interval(getVideoList, REFRESH_PERIOD)
    $scope.$on('$destroy', function() {
        $interval.cancel(getVideoTimer)
    })

    function getVideoList() {
        getConfig()
            .then(function(response) {
                $scope.videoPath = response.VideoPath;
                return dataDispatchRecord()
            })
            .then(function(response) {
                $scope.listNew = response.data;
                // console.log('get response',response.data)
                if (_.isEmpty($scope.repeatList)) {
                    $scope.listOld = angular.copy($scope.listNew);
                    if ($scope.listNew.length < MAX_LIST) {
                        $scope.repeatList = angular.copy($scope.listNew);
                    } else {
                        $scope.repeatList = $scope.listNew.slice(0, MAX_LIST);
                        videoIndex = MAX_LIST - 1;
                    }
                } else {
                    var differenList = _.differenceBy($scope.listNew, $scope.listOld, 'uuid');
                    // var differenList = _.differenceBy($scope.listNew, $scope.listOld,'recordUuid');
                    console.log('different', differenList)

                    if (_.isEmpty(differenList)) {
                        var sameArrayIndex = 0
                        console.log('same Array----videoIndex', videoIndex)
                        if (videoIndex + MAX_LIST < $scope.listNew.length) { // 沒爆
                            if (videoIndex == 0) {
                                sameArrayIndex = 0
                            } else {
                                sameArrayIndex = videoIndex + 1
                            }
                            $scope.repeatList = []
                            $scope.repeatList = $scope.listNew.slice(sameArrayIndex, sameArrayIndex + MAX_LIST);
                            videoIndex = videoIndex + MAX_LIST;
                            console.log('沒有爆----videoIndex', videoIndex)

                        } else { //爆了

                            if (videoIndex >= $scope.listNew.length - 1) {
                                // $scope.repeatList=[]
                                // $scope.repeatList = $scope.listNew.slice(0,MAX_LIST);
                                videoIndex = MAX_LIST - 1;
                                console.log('bump!!length', videoIndex);
                            } else {
                                console.log('bump!! 不是最後一個length', videoIndex);
                                $scope.repeatList = []
                                $scope.repeatList = $scope.listNew.slice(videoIndex + 1, videoIndex + 1 + MAX_LIST);
                                videoIndex = 0;
                            }

                        }
                    } else { //2個array不一樣
                        $scope.listOld = $scope.listNew
                        videoIndex = 0
                        console.log('differen Array----videoIndex', videoIndex)
                        if ($scope.listNew.length < MAX_LIST) {
                            $scope.repeatList = []
                            $scope.repeatList = angular.copy($scope.listNew);
                        } else {
                            $scope.repeatList = []
                            $scope.repeatList = $scope.listNew.slice(0, MAX_LIST);
                            videoIndex = MAX_LIST - 1;

                        }
                    }
                }
            })
}

function getHospitalDispatch(pcrUuid){
    return getConfig()
    .then(function(config){
        return $http.get(config.HospitalServer+'/Dispatches', {
                params: {
                    recordUuid: pcrUuid
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
    })
    .then(function(response){
        return response.data;
    })
}

function getHospitalDispatchFromPcrs(DispatchRecordUuid, Pcrs){
    function saveDispatch(PcrUuid){
        if(_.isNil(hospitalDispatches[DispatchRecordUuid])){
            hospitalDispatches[DispatchRecordUuid] = {};
        }
        return getHospitalDispatch(PcrUuid)
        .then(function(dispatch){
            if(!_.isEmpty(dispatch)){
                hospitalDispatches[DispatchRecordUuid][PcrUuid] = dispatch[0];
            }
        });
    }

    var tasks = [];
    for(var idx in Pcrs){
        var pcr = Pcrs[idx];
        tasks.push( saveDispatch( pcr.uuid) );
    }
    return $q.all(tasks);
}

function getHospitalDispatchFromDipatchRecord(DispatchRecords){

    var tasks = [];
    for(var idx in DispatchRecords){
        var DispatchRecord = DispatchRecords[idx];
        tasks.push( getHospitalDispatchFromPcrs(DispatchRecord.uuid, DispatchRecord.Pcrs ))
    }
    return $q.all(tasks)
}

//執行中車輛
function tableInit() {
    return new NgTableParams({
        sorting: defaultSorting
    }, {
        pages: [],
        counts: [],
        filterDelay: 300,
        getData: function(params) {
            var deferred = $q.defer();
            $scope.anyPageBusy = deferred.promise;
            var sortString;
            // 如果使用 epilogue 免費 api sort需要做調整
            // 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
            // sortString = params.sorting();
            for (var key in params.sorting()) {
                if (params.sorting()[key] == 'desc') {
                    sortString = '-' + key;
                } else {
                    sortString = key;
                }
            }

            var dateBegin = moment().subtract(24, 'hours').toDate()
            return EPCRServices.getDispatchRecords(dateBegin)
                .then(function(response) {

                    return getHospitalDispatchFromDipatchRecord(response.data)
                    .then(function(){
                        $scope.hospitalDispatches = hospitalDispatches;
                        deferred.resolve()
                        return response.data
                    });
                })
                .catch(function(err) {
                    deferred.resolve();
                    console.log('tableInit err =', err)
                })

        }
    })
}

$scope.tableParams = tableInit();

//各區域分隊車輛執行量
function tableExecuteParams() {
    return new NgTableParams({
        sorting: defaultSorting
    }, {
        pages: [],
        counts: [],
        filterDelay: 300,
        getData: function(params) {
            var deferred = $q.defer();
            $scope.anyPageBusy = deferred.promise;
            var sortString;
            // 如果使用 epilogue 免費 api sort需要做調整
            // 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
            // sortString = params.sorting();
            for (var key in params.sorting()) {
                if (params.sorting()[key] == 'desc') {
                    sortString = '-' + key;
                } else {
                    sortString = key;
                }
            }

            return EPCRServices.getListBranchWithCaseRecordAndAmbulance()
                .then(function(response) {
                    deferred.resolve()
                    return response.data
                })
                .catch(function(err) {
                    deferred.resolve();
                    console.log('tableExecuteParams err =', err)
                })

        }
    })
}

$scope.tableExecuteParams = tableExecuteParams();


// watch for check all checkbox
$scope.$watch(function() {
    return $scope.checkboxes.checked;
}, function(value) {
    angular.forEach(responseList, function(item) {
        $scope.checkboxes.items[item.id] = value;
    });
});
// watch for data checkboxes
$scope.$watch(function() {
    return $scope.checkboxes.items;
}, function(values) {
    var checked = 0,
        unchecked = 0,
        total = responseList.length;
    angular.forEach(responseList, function(item) {
        checked += ($scope.checkboxes.items[item.id]) || 0;
        unchecked += (!$scope.checkboxes.items[item.id]) || 0;
    });
    if (total > 0 && ((unchecked == 0) || (checked == 0))) {
        console.log('checked=', checked, 'total=', total);
        $scope.checkboxes.checked = (checked == total);
    }
    // grayed checkbox
    angular.element($element[0].getElementsByClassName("select-all")).prop("indeterminate", (checked != 0 && unchecked != 0));
}, true);

});
