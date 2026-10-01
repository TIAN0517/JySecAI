CONTROLLERS.controller('CaseListCtrl', function($q, $scope, $rootScope, $state, NgTableParams,
    $http, AlertService, AuthService, $stateParams, $window, $document) {

    var NEED_BACK_TRACKING_TYPE = -1;

    var search = {
        hasBacktracking: false,
        arrivedHospitalAt: { startDate: null, endDate: null },
        isSimulation: false
    }

    var hospitalUuid;
    var currentUser = AuthService.getCurrentUser();
    $scope.currentUser = currentUser;
    console.log('CURRENT USER:', currentUser);
    if(_.isNil(currentUser)){
        return;
    }
    if(currentUser.role=='HOSPITAL'){
        hospitalUuid = currentUser.customData;
    }else{
        hospitalUuid = null;
    }

    function getConfig(){
        return $http.get('/config')
        .then(function(response){
            return response.data;
        })
        .then(function(result){
            $scope.PUBLIC_CONFIG = result;
            return result;
        });
    }

    var configPromise = getConfig();

    function getCaseUrl(recordUuid, SourceTypeId){
        switch(SourceTypeId){
            case 1:
                return $scope.EPCRServerUrl+'/#/caseDetail/'+recordUuid+'?token='+$scope.TOKEN;
            case 2:
                var caseId = recordUuid.split('-')[0]; // 轉換成MER案件號
                var url = encodeURIComponent($scope.MerServer+'/Views/CaseDetailView.aspx?ID='+caseId);
                var currentUser = encodeURIComponent( AuthService.getCurrentUser().account );
                return $scope.Redir+'?url='+url+'&authorization_people_name='+currentUser+'&token='+$scope.TOKEN;

            default:
                return null;
        }
    }
    $scope.getCaseUrl = getCaseUrl;

    function getCasePrintUrl(recordUuid, SourceTypeId){
        switch(SourceTypeId){
            case 1:
                return $scope.EPCRServerUrl+'/#/caseDetailPrint/'+recordUuid+'/1?token='+$scope.TOKEN;
            case 2:
                var url = encodeURIComponent($scope.MerServer+'/Views/CaseDetailView.aspx?ID='+recordUuid);
                var currentUser = encodeURIComponent(AuthService.getCurrentUser().account);
                return $scope.Redir+'?url='+url+'&authorization_people_name='+currentUser+'&token='+$scope.TOKEN;

            default:
                return null;
        }
    }
    $scope.getCasePrintUrl = getCasePrintUrl;

    function getHospital(){
        return $http.get('/Hospitals',{
            params: {
                disabled: false
            },
            paramSerializer: '$httpParamSerializerJQLike'
        })
        .then(function(response){
            return response.data;
        });
    }

    function setupHospital(){
        return getHospital()
        .then(function(results){
            $scope.HospitalList = results;
        })
    }

    function checkHasMer(recordUuids){
        return configPromise
        .then(function(config){
            return $http.post(config.EPCRServer+'/Pcrs/ckeckHasMer', recordUuids)
        })
        .then(function(response){
            return response.data;
        })
    }


    $scope.hasMerMap = {};
    function setupHasMer(recordUuids){
        return checkHasMer(recordUuids)
        .then(function(results){
            var hasMerMap = {};
            for(var i in results){
                var result = results[i];
                hasMerMap[result.uuid] = result.hasMer;
            }
            $scope.hasMerMap = hasMerMap;
        })
    }

    function dataInit() {
        clear();
        return $http.get('/DispatchTypes')
            .then(function(response) {
                //派遣案類
                $scope.showDispatchTypes = _.keyBy(response.data, 'id')
                $scope.showDispatchTypes[NEED_BACK_TRACKING_TYPE] = {
                    id: NEED_BACK_TRACKING_TYPE,
                    name: '--- 所有需回溯案類 ---'
                }
                return $http.get('/Statuses')
            })
            .then(function(response) {
                //案件狀態
                $scope.showStatuses = _.keyBy(response.data, 'id')
                return $http.get('/config')
            })
            .then(function(response){
                if(response.data){
                    $scope.EPCRServerUrl = response.data.EPCRServer;
                    $scope.MerBridge = response.data.MerBridge;
                    $scope.MerServer = response.data.MerServer;
                    $scope.TOKEN = AuthService.getToken();
                    $scope.Redir = response.data.Redir;
                }
            })
            .then(function(){
                return setupHospital();
            });
    }
    dataInit();

    function clear() {
        search = {
            hasBacktracking: false,
            arrivedHospitalAt: { startDate: null, endDate: null },
            isSimulation: false
        };
        $scope.search = search;
    }
    $scope.clear = clear;

    $scope.searchCase = function(search) {
        if (_.isEmpty(search)) {
            return AlertService.failAlert('錯誤！', '沒有輸入查詢條件！', null)
        }

        $scope.tableParams = tableInit();
    }

    //接收案件回朔完成後的通知事件並且重新載入資料
    var receiveMessage = function(event) {
        if (event.data == 'BacktrackingCtrl.updated') {
            $scope.tableParams = tableInit();
            console.log('QQ')
        }
    }
    $document.ready(function() {
        $window.addEventListener("message", receiveMessage, false);
    });
    //接收案件回朔完成後的通知事件並且重新載入資料

    // $scope.showDetail = function(index) {
    //     var pcrBundleUuid = responseList[index].PcrBundleUuid;
    //     var dispatchId = responseList[index].id;
    //     var hospitalUuid= responseList[index].HospitalUuid;
    //     if(pcrBundleUuid){
    //         $window.open('/#/editbacktracking/'+pcrBundleUuid,'_blank');
    //     }else{
    //         var questionWindow = $window.open('/#/backtracking/' + dispatchId, '_blank');
    //     }
    // }

    $scope.showDetail = function(index) {
        var dispatchId = responseList[index].id;
        $window.open('/#/backtrackingeditor/'+dispatchId, '_blank');
    }

    function refreshList() {
        $scope.checkboxes = {
            checked: false,
            items: {}
        }
        $scope.tableParams = tableInit();
        $scope.caseNumberMap = {};
    }

    refreshList();

    var responseList = [];

    $scope.caseNumberMap = {};

    function tableInit() {
        return new NgTableParams({
            page: 1, // show first page
            count: 20, // count per page,
            sorting: {
                createdAt: 'desc'
            }
        }, {
            counts: [20, 40, 60, 100],
            filterDelay: 300,
            getData: function(params) {
                var deferred = $q.defer();
                $scope.anyPageBusy = deferred.promise;
                var url = params.url();
                var limit = url.count,
                    skip = url.count * (url.page - 1);
                var sortString = null;
                // 如果使用 epilogue 免費 api sort需要做調整
                // 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
                // sortString = params.sorting();
                console.log(params.sorting());
                for (var key in params.sorting()) {
                    if (params.sorting()[key] == 'desc') {
                        sortString = '-' + key;
                    } else {
                        sortString = key;
                    }
                }

                var query = {
                    offset: skip,
                    count: limit,
                    time: new Date().getTime()
                }
                if(sortString){
                    query['sort'] = sortString;
                }

                for (var key in search) {
                    if (search[key] !== '') {
                        if(key == 'hasBacktracking'){
                            switch(search[key]){
                                case false:
                                    query["withBundle"] = false;
                                    break;
                                case true:
                                    query["withBundle"] = true;
                                    break;
                            }
                        }else if(key=='selectedHospitalUuid' && search.selectedHospitalUuid){
                            query['HospitalUuid'] = search.selectedHospitalUuid;
                        }else if(key=='arrivedHospitalAt'){
                            if(search[key].startDate && search[key].endDate){
                                query['begin'] = search[key].startDate.toDate();
                                query['end'] = search[key].endDate.toDate();
                            }
                        }else{
                            if(_.isNil(search[key])==false){
                                query[key] = search[key];
                            }
                        }
                    }
                }

                // if(_.isNil(search['DispatchTypeId'])){
                if(search['DispatchTypeId']==NEED_BACK_TRACKING_TYPE){
                    delete query['DispatchTypeId'];
                    query['needBackTracking'] = true;
                }
                query['StatusId'] = 2;

                console.log("query", query)
                return $http.get('/Dispatches/list', {
                        params: query,
                        paramSerializer: '$httpParamSerializerJQLike'
                    })
                    .then(function(response) {
                        var range = contentRange.parse(response.headers('Content-Range'));
                        var count = range.length;
                        params.total(count);
                        responseList = response.data;
                        // 把來自EPCR的Dispatch收集起來，查詢該案件是否有對應的MER案件
                        var uuids = []
                        for(var i in responseList){
                            if(responseList[i].SourceTypeId==1){
                                uuids.push(responseList[i].recordUuid)
                            }
                        }
                        return setupHasMer(uuids)
                        .then(function(){
                            deferred.resolve()
                            return responseList;
                        });
                    })
                    .catch(function(err) {
                        deferred.resolve();
                        console.log('tableInit err =', err)
                    })

            }
        })
    }

});
