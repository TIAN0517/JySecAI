CONTROLLERS.controller('CaseListForBranchGroupDoctorCtrl', function($q, $scope, $rootScope, $state,
    $http, AuthService, $stateParams, $window, $document, NgTableParams
    ,$alert, $sce) {

    var chiefComplaintMap = {};
    var chiefComplaintLoadingMap = {};
    var doctorOrderMap = {};
    var doctorOrderLoadingMap = {};

	var defaultSearchParams = {
		PcrDoctorOrderStatusId: 1,
		isSimulation: false,
		DispatchRecordStatusId: 9,
		// uuid: '0008e5d7-c3a3-42a6-b909-4b76de0ac2ad' // FOR TEST ONLY!!!
		// uuid: '993c420d-eda0-42d4-8f7f-c3a9e97f5d8d' // FOR TEST ONLY!!! 有imageData
		// uuid: '00168e79-61a1-42a0-bdc8-baf840834caf' // FOR TEST ONLY!!! 有vitalSignSet
	};
	var searchParams = {};
	angular.copy(defaultSearchParams, searchParams);
	$scope.searchParams = searchParams;

	var checked = {};
	$scope.checked = checked;

    var currentUser = AuthService.getCurrentUser();
    console.log('CURRENT USER:', currentUser);
    if(_.isNil(currentUser)){
        return;
    }
    $scope.currentUser = currentUser;

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

    function dateEndSet(date){
        $scope.searchParams.dateEnd = moment(date).endOf('day').toDate();
    }
    $scope.dateEndSet = dateEndSet;

/* 主訴 */
    function getEPCRchiefComplaint(recordUuid){
        return configPromise
        .then(function(config){
            return $http.get('/pcrRecords/lastOneByPcrAndQuestion',{
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

    function cheifComplaintTask(pcrUuid){
    	return getEPCRchiefComplaint(pcrUuid)
    	.then(function(results){
    		chiefComplaintMap[pcrUuid] = results;
            chiefComplaintLoadingMap[pcrUuid] = true;
    	})
    }

    function setUpChiefComplaint(pcrs){
    	chiefComplaintMap = {};
        chiefComplaintLoadingMap = {};
    	var tasks = [];
    	for(var i in pcrs){
    		var pcr = pcrs[i];
    		var fn = cheifComplaintTask.bind(null, pcr.uuid);
    		tasks.push(fn());
    	}
    	return $q.all(tasks)
    	.then(function(){
    		$scope.chiefComplaintMap = chiefComplaintMap;
            $scope.chiefComplaintLoadingMap = chiefComplaintLoadingMap;
    	});
    }
/* 主訴 */
/* 醫師簽核 */
	function getListRequireDoctorOrder(pcrUuid){
		return $http.get('/pcrs/pcrRecordRequireDoctorOrder/'+pcrUuid)
		.then(function(response){
			return response.data;
		})
	}

	function doctorOrderTask(pcrUuid){
		return getListRequireDoctorOrder(pcrUuid)
		.then(function(results){
			doctorOrderMap[pcrUuid] = results;
            doctorOrderLoadingMap[pcrUuid] = true;
		})
	}

	function setUpDoctorOrder(pcrs){
		doctorOrderMap = {};
        doctorOrderLoadingMap = {};
		var tasks = [];
		for(var i in pcrs){
			var pcr = pcrs[i];
			var fn = doctorOrderTask.bind(null, pcr.uuid);
			tasks.push(fn());
		}
		return $q.all(tasks)
		.then(function(){
			$scope.doctorOrderMap = doctorOrderMap;
            $scope.doctorOrderLoadingMap = doctorOrderLoadingMap;
		});
	}
/* 醫師簽核 */
/* 心電圖 */
    function getEcgList(DispatchRecordUuid){
        return configPromise
        .then(function(config){
            var serverUrl = config.vitalSignVideoServer;
            return $http.get(serverUrl+'/imageData',{
                params: {
                    recordUuid: DispatchRecordUuid,
                    ImageTypeId: [1,5]
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
            .then(function(response){
                // return response.data;
                var output = [];
                for(var i in response.data){
                  var data = response.data[i];
                  var url  = serverUrl+'/imageData/getFile/'+data.id
                  output.push({
                    url: $sce.trustAsResourceUrl(url),
                    mimeType: data.mimeType
                  })
                }
                return output;
            })
        })
    }

    function setupEcg(DispatchRecordUuid){
        return getEcgList(DispatchRecordUuid)
        .then(function(results){
            $scope.ecgList[DispatchRecordUuid] = results;
        });
    }
/* 心電圖 */
/* 生命徵象 */
    function getEPCRvital(pcrUuid){
        return configPromise
        .then(function(config){
            return $http.get('/VitalSignSets',{
                params: {
                    PcrUuid: pcrUuid
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
        })
        .then(function(response){
            return response.data;
        })
    }

    function setupVital(pcrUuid){
		return getEPCRvital(pcrUuid)
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

            $scope.vitalList[pcrUuid] = output;
        })
    }
/* 生命徵象 */
    function getEPCRpcrBundles(PcrCatgoryId, pcrUuid){
        return configPromise
        .then(function(config){
            return $http.get('/PcrBundles',{
                params: {
                    PcrUuid: pcrUuid,
                    PcrCategoryId: PcrCatgoryId
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
        })
        .then(function(response){
            return response.data;
        })

    }

    function setupAssement(pcrUuid){
    	return getEPCRpcrBundles(802, pcrUuid)
        .then(function(results){
            $scope.assessmentList[pcrUuid] = results;
        });

    }

    function setupTreatment(recordUuid){
        return getEPCRpcrBundles(803, recordUuid)
		.then(function(results){
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

    function getBranchGroup(){
    	return $http.get('/BranchGroups')
    	.then(function(response){
    		return response.data;
    	});
    }

    function setupBranchGroup(){
    	return getBranchGroup()
    	.then(function(results){
    		$scope.BranchGroupList = results;
    	})
    }

	function getPcrDoctorOrderStatus(){
		return $http.get('/PcrDoctorOrderStatus')
		.then(function(response){
			return response.data;
		})
	}

	function setupPcrDoctorOrderStatus(){
		return getPcrDoctorOrderStatus()
		.then(function(results){
			$scope.PcrDoctorOrderStatusList = results;
		})
	}

    function dataInit() {
    	return setupBranchGroup()
    	.then(function(){
    		return setupPcrDoctorOrderStatus();
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

    $scope.toggleEcg = function(uuid){
        toggleImpl($scope.ecgToggle, uuid, setupEcg);
    }

    $scope.toggleVital = function(uuid){
        toggleImpl($scope.vitalToggle, uuid, setupVital);
    }

    $scope.toggleAssessment = function(uuid){
        toggleImpl($scope.assessmentToggle, uuid, setupAssement);
    }

    $scope.toggleTreatment = function(uuid){
        toggleImpl($scope.treatmentToggle, uuid, setupTreatment);
    }


    function toggleImpl(target, uuid, func){
        if(_.isNil(target[uuid])){
            target[uuid] = true;
        }else{
            target[uuid] = !target[uuid];
        }

        if(target[uuid]){
            func(uuid);
        }
    }

/* 大隊醫師簽核 */
	function saveDoctorOrder(pcrUuid){
		return $http.put('/pcrs/doctorOrder/'+pcrUuid)
		.then(function(response){
			return response.data;
		})
	}
	$scope.saveDoctorOrder = function(pcrUuid, drSuggestion){
        var deferred = $q.defer();
        $scope.anyPageBusy = deferred.promise;

        // Jordan 2022-10-12 FeatureAdd 簽核時同時儲存 suggestion
        if (drSuggestion == '') drSuggestion = null;
        return $http.put('/Pcrs/drSuggestion/' + pcrUuid, { drSuggestion: drSuggestion })
        .then(function(){
            return saveDoctorOrder(pcrUuid)
        })
		.then(function(){

			var idx = _.findIndex(responseList, { uuid: pcrUuid });
			if(idx!=-1){
                responseList[idx].editDrSuggestion = false; // Jordan 2022-10-12 FeatureAdd 簽核時同時儲存 suggestion
				responseList[idx].PcrDoctorOrderStatusId = 2;
                responseList[idx].orderGivenBy = currentUser.name;
			}

            deferred.resolve();
		})
		.catch(function(error){
			console.log(error);
			alert('無法簽核!');
		});
	}

    async function batchSaveSuggestion(pcrUuids){
        for(var i in pcrUuids){
            var pcrUuid = pcrUuids[i];
            var idx = _.findIndex(responseList, { uuid: pcrUuid });
            var drSuggestion = (responseList[idx].drSuggestion == '')? null: responseList[idx].drSuggestion;

            await $http.put('/Pcrs/drSuggestion/' + pcrUuid, { drSuggestion: drSuggestion })
        }
    }

	function batchSaveDoctorOrder(pcrUuids){

        // 不想加開API，簡單寫
        // Jordan 2022-10-12 FeatureAdd 簽核時同時儲存 suggestion
        return batchSaveSuggestion(pcrUuids)
        .then(function(){
            return $http.put('/pcrs/doctorOrderByBatch',pcrUuids)
        })
		.then(function(response){
			return response.data;
		});
	}

	$scope.batchSaveDoctorOrder = function(pcrUuidMap){
		var pcrUuids = [];
		for(var uuid in pcrUuidMap){
			if(pcrUuidMap[uuid] == true){
				pcrUuids.push(uuid);
			}
		}
		if(pcrUuids.length==0){
			return;
		}else{
			var ret = confirm("確定簽核所選的案件?")
			if(ret){
                var deferred = $q.defer();
                $scope.anyPageBusy = deferred.promise;

				batchSaveDoctorOrder(pcrUuids)
				.then(function(){
					checked = {};
					$scope.checked = checked;
					for(var i in pcrUuids){
						var pcrUuid = pcrUuids[i];
						var idx = _.findIndex(responseList, { uuid: pcrUuid });
						if(idx!=-1){
                            responseList[idx].editDrSuggestion = false; // Jordan 2022-10-12 FeatureAdd 簽核時同時儲存 suggestion
							responseList[idx].PcrDoctorOrderStatusId = 2;
                            responseList[idx].orderGivenBy = currentUser.name;
						}
					}
                    deferred.resolve();
				})
				.catch(function(error){
					console.log(error);
					alert('無法簽核!');
				});
			}
		}
	}


/* 大隊醫師簽核 */

    function refreshList() {
    	$scope.tableParams = tableInit();
    }

    function resetSearch() {
    	angular.copy(defaultSearchParams, searchParams);
    	$scope.stateParams = searchParams;
    	checked = {};
    	$scope.checked = checked;
    }

    $scope.refreshList = refreshList;
    $scope.resetSearch = resetSearch;
    refreshList();

    var responseList = [];

	function tableInit() {
		return new NgTableParams({
			page: 1, // show first page
			count: 10, // count per page,
			sorting: {
				// createdAt: 'desc'
			}
		}, {
			filterDelay: 300,
			getData: function(params) {
				var deferred = $q.defer();
				$scope.anyPageBusy = deferred.promise;
				console.log(params.sorting())
				var url = params.url();
				var limit = url.count,
					skip = url.count * (url.page - 1);
				var sortString;
				// 如果使用 epilogue 免費 api sort需要做調整
				// 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
				sortString = params.sorting();
                //取消選取記錄
                checked = {};
                $scope.checked = checked;


				var query = {
					sort: sortString,
					offset: skip,
					count: limit,
					time: new Date().getTime()
				}

				if (!_.isEmpty(searchParams)) {
					for (var key in searchParams) {
						query[key] = searchParams[key];
					}
				}

				console.log("query", query)

				return $http.get('/Pcrs/pcrCaseList', {
						params: query,
						paramSerializer: '$httpParamSerializerJQLike'
					})
					.then(function(response) {
						var range = contentRange.parse(response.headers('Content-Range'));
						var count = range.length;
						params.total(count);
						responseList = response.data;

						var tasks = [];
						tasks.push(setUpChiefComplaint(responseList));
						tasks.push(setUpDoctorOrder(responseList));
                        $q.all(tasks);

						deferred.resolve()
						console.log('@@ list=', responseList)
						return responseList

					})
					.catch(function(err) {
						deferred.resolve();
						console.log('tableInit err =', err)
					})

			}
		})
	}

    // 醫師處置建議編輯
    function editDrSuggestion(uuid, drSuggestion) {
        return $http.put('/Pcrs/drSuggestion/' + uuid, { drSuggestion: drSuggestion })
            .then(function (response) {
                return response.data;
            });
    } // editDrSuggestion()

    $scope.editDrSuggestion = function (uuid, drSuggestion) {
        var deferred = $q.defer();
        $scope.anyPageBusy = deferred.promise;

        if (drSuggestion == '') drSuggestion = null;

        return editDrSuggestion(uuid, drSuggestion)
            .then(function () {
                deferred.resolve();
                refreshList();
            })
            .catch(function (error) {
                console.log(error);
                alert('無法編輯!');
                deferred.resolve();
            });
    };
});
