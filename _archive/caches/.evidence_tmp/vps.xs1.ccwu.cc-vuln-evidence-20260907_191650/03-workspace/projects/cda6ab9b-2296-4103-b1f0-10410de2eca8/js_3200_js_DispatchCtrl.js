CONTROLLERS.controller('DispatchCtrl', function($q, $scope, $rootScope, $state,
    $http, AlertService, AuthService, $stateParams, $window, $document, SocketIoService
    ,$alert, $sce) {

    var searchParams = { PcrBundleUuid: 'null' };

    var hospitalUuid;
    var currentUser = AuthService.getCurrentUser();
    console.log('CURRENT USER:', currentUser);
    if(_.isNil(currentUser)){
        return;
    }
    if(currentUser.role=='HOSPITAL'){
        hospitalUuid = currentUser.customData;
    }else{
        hospitalUuid = null;
    }
    $scope.hospitalUuid = hospitalUuid;

    var socketio = null;

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

    function getEPCRchiefComplaint(recordUuid){
        return configPromise
        .then(function(config){
            var EPCRServerUrl = config.EPCRServer;
            return $http.get(EPCRServerUrl+'/pcrRecords/lastOneByPcrAndQuestion',{
                params: {
                    PcrQuestion: 'chief_complaint1',
                    PcrUuid: recordUuid
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
        })
        .then(function(response){
            return response.data;
        })
    }

    //MER目前無主訴
    function getMERchiefComplaint(recordUuid){
        return $q.when({});
    }

    function setupChiefComplaint(dispatch, recordUuid){
        var task = $q.when();
        switch(dispatch.SourceTypeId){
            case 1: // EPCR
                task = getEPCRchiefComplaint(recordUuid);
            break;
            case 2: // MER
                task = getMERchiefComplaint(recordUuid);
            break;
        }
        return task.then(function(result){
            dispatch.chiefComplaint = result;
        });
    }

    function getDispatchInfo(dispatchId){
        return $http.get('/Dispatches/informationOf/'+dispatchId+'?fields=["age","name"]')
        .then(function(response){
            return response.data;
        })
    }

    function setupDispatchInfo(dispatchId){
        return getDispatchInfo(dispatchId)
        .then(function(result){
            $scope.dispatchInfo[dispatchId] = result;
        })
        .catch(function(error){
            // 有些pcr 選定後送醫院後，pcr又被刪除
            // 因此不是每一筆Dispatch都會有對應的pcr, 就會收到404 錯誤
            console.log(error);
        })
    }

    function getEPCRpreparation(recordUuid){
        return configPromise
        .then(function(config){
            var EPCRServerUrl = config.EPCRServer;
            return $http.get(EPCRServerUrl+'/PcrBundles',{
                params: {
                    PcrUuid: recordUuid,
                    PcrCategoryId: 806
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
        })
        .then(function(response){
            return response.data;
        })
    }

    //MER目前無急救準備通知
    function getMERpreparation(recordUuid){
        return $q.when({});
    }

    function setupPreparation(dispatch, recordUuid){
        var task = $q.when();
        if (dispatch.hasPreparationNotice) {
            switch (dispatch.SourceTypeId) {
                case 1: // EPCR:
                    task = getEPCRpreparation(recordUuid);
                    break;
                case 2: // MER
                    task = getMERpreparation(recordUuid);
                    break;
            }
        } // if
        return task.then(function(result){
            dispatch.preparation = result;
        });
    }

    function getEcgList(recordUuid, sourceTypeId){
        return getPcrDispatchRecord(recordUuid,sourceTypeId)
        .then(function(result){
            var DispatchRecordUuid = result;
            return configPromise
            .then(function(config){
                var serverUrl = config.vitalSignVideoServer;
                return $http.get(serverUrl+'/imageData',{
                    params: {
                        recordUuid: {
                          $in: [DispatchRecordUuid,recordUuid]
                        },
                        ImageTypeId: {
                            $in: [1,5]
                        }
                    },
                    paramSerializer: '$httpParamSerializerJQLike'
                })
            })
            .then(function(response){
                return response.data;
            })
        });
    }

    function setupEcg(recordUuid,sourceTypeId){
        return getEcgList(recordUuid,sourceTypeId)
        .then(function(results){
            results.forEach(function(item){
              item.url = $sce.trustAsResourceUrl($scope.PUBLIC_CONFIG.vitalSignVideoServer+'/imageData/getFile/'+item.id)
            })
            $scope.ecgList[recordUuid] = results;
        });
    }

    function getEPCRvital(recordUuid){
        return configPromise
        .then(function(config){
            var serverUrl = config.EPCRServer;
            return $http.get(serverUrl+'/VitalSignSets',{
                params: {
                    PcrUuid: recordUuid
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
        })
        .then(function(response){
            return response.data;
        })
    }

    function getMERvital(recordUuid){
        return $q.when([]);
    }

    function setupVital(recordUuid, SourceTypeId){
        var task = $q.when();
        switch(SourceTypeId){
            case 1: // EPCR:
                task = getEPCRvital(recordUuid);
            break;
            case 2: // MER
                task = getMERvital(recordUuid);
            break;
        }
        return task
        .then(function(results){
            var output = [];

            for(var idx in results){
                var vitalSignSet = results[idx];
                var row = _.keyBy(vitalSignSet.VitalSigns, function(o){
                    return o.VitalSignType.name;
                });
                row.VitalSignSetType = vitalSignSet.VitalSignSetType.name;
                row.datetime = vitalSignSet.datetime;
                output.push(row);
            }

            $scope.vitalList[recordUuid] = output;
        })
    }

    function getEPCRpcrBundles(PcrCatgoryId, recordUuid){
        return configPromise
        .then(function(config){
            var serverUrl = config.EPCRServer;
            return $http.get(serverUrl+'/PcrBundles',{
                params: {
                    PcrUuid: recordUuid,
                    PcrCategoryId: PcrCatgoryId
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
        })
        .then(function(response){
            return response.data;
        })

    }

    function getMERpcrBundles(PcrCatgories, recordUuid){
        var categories = JSON.stringify(PcrCatgories)
        return configPromise
        .then(function(config){
            var serverUrl = config.MerBridge;
            return $http.get(serverUrl+'/PcrBundles',{
                params: {
                    PcrUuid: recordUuid,
                    PcrCategories: categories
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
        })
        .then(function(response){
            return response.data;
        })

    }

    function setupAssement(recordUuid, sourceTypeId){
        var task = $q.when({});
        switch(sourceTypeId){
            case 1: // EPCR:
                task = getEPCRpcrBundles(802, recordUuid);
            break;
            case 2: // MER
                task = getMERpcrBundles([1,2,3,4,5,6], recordUuid);
            break;
        }
        return task.then(function(results){
            $scope.assessmentList[recordUuid] = results;
        });

    }

    function setupTreatment(recordUuid, sourceTypeId){
        var task = $q.when({});
        switch(sourceTypeId){
            case 1: // EPCR:
                task = getEPCRpcrBundles(803, recordUuid);
            break;
            case 2: // MER
                task = getMERpcrBundles([7], recordUuid);
            break;
        }
        return task.then(function(results){
            $scope.treatmentList[recordUuid] = results;
        });
    }

    function getVitalSignTypes(){
        return configPromise
        .then(function(config){
            var serverUrl = config.EPCRServer;
            return $http.get(serverUrl+'/VitalSignTypes')
        })
        .then(function(response){
            return response.data;
        })
    }

    function getHospitalList(){
        return $http.get('/Hospitals')
        .then(function(response){
            return response.data;
        });
    }

    function getPcrDispatchRecord(pcrUuid, SourceTypeId){
        switch(SourceTypeId){
            case 1: // EPCR
                return configPromise
                .then(function(config){
                    var serverUrl = config.EPCRServer;
                    return $http.get(serverUrl+'/PcrDispatchRecords/'+pcrUuid)
                    .then(function(response){
                        var pcr =  response.data;
                        return pcr.DispatchRecord.uuid;
                    })
                })
            break;
            case 2:
                return $q.when(pcrUuid);
            break;
        }
    }

    function setupSocketIoRoom(socketio, hospitalUuid){
        if(hospitalUuid){
            SocketIoService.leaveAll();
            return SocketIoService.joinRoom(hospitalUuid)
            .then(function(){
                socketio.on('update', function(data){
                    switch(data.category){
                        case 'preparation.notice':
                            $alert({
                                title: '請注意',
                                container: 'body',
                                content: '急救準備通知 已更新',
                                placement: 'top-right',
                                type: 'danger',
                                show: true,
                                duration: 10
                            });
                        break;
                        case 'arrived':
                        case 'canceled':
                        case 'pcr.updated':
                            $alert({
                                title: '請注意',
                                container: 'body',
                                content: '清單已更新',
                                placement: 'top-right',
                                type: 'info',
                                show: true,
                                duration: 5
                            });
                        break;
                    }
                    refreshList();
                });
            });
        }else{
            return $q.when();
        }
    }


    function dataInit() {
        return $http.get('/DispatchTypes')
            .then(function(response) {
                //派遣案類
                $scope.showDispatchTypes = _.keyBy(response.data, 'id')
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
                    $scope.TOKEN = AuthService.getToken();
                }
            })
            .then(function(){
                return getVitalSignTypes()
                .then(function(results){
                    $scope.VitalSignTypeList = results;
                });
            })
            .then(function(){
                return SocketIoService.getSocket()
                .then(function(_socketio){
                    socketio = _socketio;
                    return setupSocketIoRoom(socketio, hospitalUuid)
                });

            })
            .then(function(){
                return getHospitalList()
                .then(function(results){
                    $scope.hospitalList = results;
                })
            });


    }
    dataInit();

    $scope.ecgToggle = {};
    $scope.vitalToggle ={};
    $scope.assessmentToggle = {};
    $scope.treatmentToggle = {};

    $scope.ecgList = {};
    $scope.vitalList = {};
    $scope.assessmentList = {};
    $scope.treatmentList = {};

    $scope.dispatchInfo = {};

    $scope.toggleEcg = function(recordUuid,sourceTypeId){
        toggleImpl($scope.ecgToggle, recordUuid, setupEcg, sourceTypeId);
    }

    $scope.toggleVital = function(recordUuid,sourceTypeId){
        toggleImpl($scope.vitalToggle, recordUuid, setupVital,sourceTypeId);
    }

    $scope.toggleAssessment = function(recordUuid, sourceTypeId){
        toggleImpl($scope.assessmentToggle, recordUuid, setupAssement, sourceTypeId);
    }

    $scope.toggleTreatment = function(recordUuid, sourceTypeId){
        toggleImpl($scope.treatmentToggle, recordUuid, setupTreatment, sourceTypeId);
    }


    function toggleImpl(target, recordUuid, func, sourceTypeId){
        if(_.isNil(target[recordUuid])){
            target[recordUuid] = true;
        }else{
            target[recordUuid] = !target[recordUuid];
        }

        if(target[recordUuid]){
            func(recordUuid, sourceTypeId);
        }
    }

    function refreshList() {
        return getData()
        .then(function(results){
            $scope.tableData = results;
        });
    }

    refreshList();

    var responseList = [];

    function getData() {
        var deferred = $q.defer();
        $scope.anyPageBusy = deferred.promise;

        var query = {
            StatusId: 1, // 僅列出前往中的
            time: new Date().getTime()
        }
        if($scope.hospitalUuid){
            query['HospitalUuid'] = $scope.hospitalUuid;
        }

        console.log("query", query)
        return $http.get('/Dispatches', {
                params: query,
                paramSerializer: '$httpParamSerializerJQLike'
            })
            .then(function(response) {
                responseList = response.data;

                var tasks = [];
                for(var idx in responseList){
                    var dispatch = responseList[idx];
                    tasks.push(setupChiefComplaint(dispatch, dispatch.recordUuid));
                    tasks.push(setupDispatchInfo(dispatch.id));
                    tasks.push(setupPreparation(dispatch, dispatch.recordUuid));
                }
                $q.all(tasks)

                deferred.resolve()
                return responseList;
            })
            .catch(function(err) {
                deferred.resolve();
                console.log('tableInit err =', err)
            })

    }

    $scope.hospitalSelected = function(hospitalUuid){
        return SocketIoService.getSocket()
            .then(function(_socketio){
                socketio = _socketio;
                return setupSocketIoRoom(socketio, hospitalUuid)
            })
            .then(function(){
                return refreshList();
            });
    }

});
