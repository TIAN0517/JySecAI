CONTROLLERS.controller('UploadPcrPictureCtrl', function ($scope, $state,
  $http, $q, EPCRServices, AuthService, Util) {

  var currentUser = AuthService.getCurrentUser();
  $scope.vm = {};
  var vm = $scope.vm;
  vm.optsDispatch = [];
  vm.optsPcr = [];
  vm.step = 1;
  vm.isUpdate = false;
  // vm.dispatchToAdd = {};
  vm.postImageParams = { ImageTypeId: 11 };

  function getCaseData(recordUuid) {
    return $http.get('/CaseRecords', {
      params: {
        recordUuid: recordUuid,
      },
      //  paramSerializer: '$httpParamSerializerJQLike'
    })
      .then(function (response) {
        return response.data
      });
  } // getCaseData()

  function getHospitalData() {
    return $http.get('/Hospitals', {
      params: {
        sort: 'name',
        disabled: false
      },
      // paramSerializer: '$httpParamSerializerJQLike'
    })
      .then(function (response) {
        return response.data
      })
  }

  function listDispatches(dispatchRecords, role, rolesid) {
    if (dispatchRecords.length > 0) {
      switch (role) {
        case "BRANCH":
          dispatchRecords.forEach(function (theDispatch) {
            if (theDispatch.BranchId == rolesid) {
              $scope.vm.optsDispatch.push(theDispatch);
              listManuallyPcrsFromDispatch(theDispatch, $scope.vm.optsDispatch.length-1);
            } // idx in $scope.vm.optsDispatch, not in dispatchRecords, so it uses $scope.vm.optsDispatch.length-1
          })
          break;
        case "BRANCHGROUP":
          dispatchRecords.forEach(function (theDispatch) {
            if (theDispatch.BranchGroupId == rolesid) {
              $scope.vm.optsDispatch.push(theDispatch);
              listManuallyPcrsFromDispatch(theDispatch, $scope.vm.optsDispatch.length-1);
            }
          })
          break;
        case "ADMIN":
        case "MANAGER":
          dispatchRecords.forEach(function (theDispatch, idx) {
            $scope.vm.optsDispatch.push(theDispatch);
            listManuallyPcrsFromDispatch(theDispatch, idx);
          })
          break;
        default:
          break;
      }

      
    }
  }

  function listManuallyPcrsFromDispatch(dispatch, dispatchIdx) {
    dispatch.Pcrs.forEach(function (pcr, pcrIdx) {
      if (pcr.pcrPictureId) {
        vm.optsPcr.push({
          fullCaseId: vm.searchCaseId + "-" + dispatch.serialNumber + "-" + pcr.serialNumber,
          dispatchIdx: dispatchIdx,
          pcrIdx: pcrIdx, // pcr index in dispatchRecord, so use foreach's idx is ok
          ambulanceCode: dispatch.ambulanceCode
        })
      }
    })
  }

  function getRole(currentUser) {
    return currentUser.role;
  }

  function getAmbulanceList() {
    var searchParams = {
      count: 1000,
      disabled: false
    }
    // if (branchId) {
    //   searchParams['BranchId'] = branchId;
    // }
    return $http.get('/Ambulances', {
      params: searchParams,
      // paramSerializer: '$httpParamSerializerJQLike'
    })
      .then(function (response) {
        return response.data
      })
  }

  function concatCaseId(pcrCaseData) {
    var _caseid = pcrCaseData.DispatchRecord.CaseRecord.recordUuid
      + "-" + pcrCaseData.DispatchRecord.serialNumber
      + "-" + pcrCaseData.serialNumber;
    return _caseid;
  }

  function checkCaseId(str) {
    if (str.match(/(test.*)|(^\d{12}$)/i) && !str.includes('-')) {
      return true;
    } else {
      return false;
    }
  }

  vm.searchCase = function (recordUuid) {
    if (!checkCaseId(recordUuid)) {
      EPCRServices.failAlert('案件號格式不正確！', null);
      return;
    }
    vm.lockCaseInput = true;
    var currentrolesId = null ;
    var role = getRole(currentUser);
    if ( role == "BRANCH" ){
      currentrolesId = currentUser.customData ;
    }else if(role == "BRANCHGROUP"){
      currentrolesId = currentUser.customData ;
    }else{
      currentrolesId = null ;
    }
    vm.msg = {};

    vm.optsDispatch = [];
    getCaseData(recordUuid)
      .then(function (data) {
        vm.step = 1.5;
        vm.caseData = data;
        if (vm.caseData && vm.caseData.length > 0) {
          vm.newCase = false;
          if (vm.caseData && vm.caseData[0]) {
            listDispatches(vm.caseData[0].DispatchRecords, role, currentrolesId);
          }

        } else {
          vm.newCase = true;
        }
        return getAmbulanceList();
      })
      .then(function (ambulanceList) {
        vm.ambulanceList = _.pullAllWith(ambulanceList, vm.optsDispatch, function (a, b) { return a.id == b.AmbulanceId });
        return getHospitalData();
      })
      .then(function (hospitalData) {
        vm.hospitalData = hospitalData;
      })
      .catch(function (err) {
        var failmsg = err.data ? err.status + JSON.stringify(err.data) : err.status;
        EPCRServices.failAlert('通知！', '搜尋失敗，請檢查連線！' + JSON.stringify(failmsg), null);
      })
  }

  vm.toStep2 = function () {
    if (vm.caseData && vm.caseData[0]) {
      vm.dispatchToAdd.address = vm.caseData[0].address;
    }
    var option1 = _.cloneDeep(options);
    var option2 = _.cloneDeep(options);
    var option3 = _.cloneDeep(options);
    if (vm.dispatchToAdd.dispatchedAt) {
      option1["startDate"] = vm.dispatchToAdd.dispatchedAt;
      $("[name='dispatchedAt']").daterangepicker(option1, datepCB);
      vm.disable_dispatchedAt = true; // 可能是中心來的 不該改
    } else {
      $("[name='dispatchedAt']").daterangepicker(option1, datepCB);
      vm.dispatchToAdd.dispatchedAt = null;
    }

    if (vm.dispatchToAdd.returnedBaseAt) {
      option2["startDate"] = vm.dispatchToAdd.returnedBaseAt;
      $("[name='returnedBaseAt']").daterangepicker(option2, datepCB);
    } else {
      $("[name='returnedBaseAt']").daterangepicker(option2, datepCB);
      vm.dispatchToAdd.returnedBaseAt = null;
    }

    if (vm.dispatchToAdd.arrivedHospitalAt) {
      option2["startDate"] = vm.dispatchToAdd.arrivedHospitalAt;
      $("[name='arrivedHospitalAt']").daterangepicker(option3, datepCB);
    } else {
      $("[name='arrivedHospitalAt']").daterangepicker(option3, datepCB);
      vm.dispatchToAdd.arrivedHospitalAt = null;
    }

    if (!vm.dispatchToAdd.ambulanceCode) {
      vm.dispatchToAdd.ambulanceCode = _.find(vm.ambulanceList, { id: vm.dispatchToAdd.AmbulanceId }).code
    } // step2要show的出勤單位

    vm.disable_address = vm.dispatchToAdd.address ? true : false;
    // vm.clearHos();
    vm.step = 2;
    
  }

  vm.toStep2Update = function(){
    vm.dispatchToAdd = vm.optsDispatch[vm.selectedPcr.dispatchIdx] ;
    vm.pcrToAdd = vm.dispatchToAdd.Pcrs[vm.selectedPcr.pcrIdx] ;
    vm.dispatchToAdd['name'] = vm.pcrToAdd.name ;
    vm.dispatchToAdd['HospitalUuid'] = vm.pcrToAdd.HospitalUuid ;
    vm.dispatchToAdd['arrivedHospitalAt'] = vm.pcrToAdd.arrivedHospitalAt ;
    if ( vm.pcrToAdd.HospitalUuid == null ) {
      vm.noHos = true ;
    }
    vm.toStep2();
  }

  vm.clearHos = function () {
    vm.dispatchToAdd.HospitalUuid = null;
    vm.dispatchToAdd.arrivedHospitalAt = null ;
  }


  vm.uploadSuccess = function (response) {
    vm.authToken = AuthService.getToken();
    if (response && response.data && response.data.id) {
      vm.dispatchToAdd.ImgMimeType = response.data.mimeType;
      vm.dispatchToAdd.ImgFileName = response.data.fileName;
      vm.dispatchToAdd.ImageDataId = response.data.id;
      EPCRServices.successAlert('通知！', '照片新增成功！', null);
    } else {
      var failmsg = response.data ? response.status + JSON.stringify(response.data) : response.status;
      EPCRServices.failAlert('通知！', '照片新增失敗！' + JSON.stringify(failmsg), null);
    }

  }
  vm.uploadError = function (response) {
    var failmsg = response.data ? response.status + response.data : response.status;
    EPCRServices.failAlert('通知！', '照片新增失敗！' + JSON.stringify(failmsg), null);
  }

  vm.send = function () {
    var deferred = $q.defer();
    $scope.anyPageBusy = deferred.promise;
    if (vm.newCase || vm.dispatchToAdd.uuid == 'new') { // new case or new dispatch
      create(deferred);
    } else if (vm.isUpdate) { 
      updatePcr(deferred) ;
    }else{
      addPcr(deferred);
    }
  }

  vm.reset = function () {
    vm.optsDispatch = [];
    vm.optsPcr = [];
    vm.step = 1;
    vm.caseData = null;
    vm.dispatchToAdd = null;
    vm.postImageParams = { ImageTypeId: 11 };
    vm.disable_address = false;
    vm.disable_dispatchedAt = false;
    vm.authToken = null;
    vm.newCase = false;
    vm.searchCaseId = "";
    vm.lockCaseInput = false;
    vm.isUpdate = false;
    vm.pcrToAdd = null;
    vm.selectedPcr = null ;
    vm.noHos = false ;
  }


  var options = {
    "singleDatePicker": true,
    "showDropdowns": true,
    "minYear": 2020,
    "maxYear": 2050,
    "timePicker": true,
    "timePicker24Hour": true,
    "locale": {
      "format": "YYYY-MM-DD HH:mm:ss",
      "separator": " - ",
      "applyLabel": "確定",
      "cancelLabel": "取消",
      "fromLabel": "From",
      "toLabel": "To",
      "customRangeLabel": "Custom",
      "weekLabel": "W",
      "daysOfWeek": ["日", "一", "二", "三", "四", "五", "六"],
      "monthNames": ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
      "firstDay": 1
    },
    "linkedCalendars": false,
    "showCustomRangeLabel": false,
    "drops": "atuo"
  };

  var datepCB = function (start, end, label) {
    console.log('New date range selected: ' + start.format() + label);
  }

  function create(deferred) {
    var caseRecord;
    var dispatch;
    var pcr;
    return $http.post('/CaseRecords/create', {
      "recordUuid": vm.searchCaseId,
      "dispatchedAt": vm.dispatchToAdd.dispatchedAt,
      "address": vm.dispatchToAdd.address,
      "isSimulation": false,
      "ambulanceCode": vm.dispatchToAdd.ambulanceCode,
      "ambs": [],
      "isManuallyUploadPcr": true
    })
      .then(function (response) {
        if (response.data && response.data.id) {
          return $http.get('/CaseRecords/' + response.data.id)
        } else {
          throw { data: '建立失敗' };
        }
      })
      .then(function (response) {
        if (response.data) {
          caseRecord = response.data;
          if (vm.newCase) {
            dispatch = response.data.DispatchRecords[0];
          } else {
            dispatch = _.find(response.data.DispatchRecords, { ambulanceCode: vm.dispatchToAdd.ambulanceCode });
          } // else same case ,new dispatch
          pcr = dispatch.Pcrs[0];
          return $http.put('/CaseRecords/' + caseRecord.id, { endedAt: vm.dispatchToAdd.returnedBaseAt })
        } else {
          throw { data: '建立失敗' };
        }
      })
      .then(function () {
        return $http.put('/DispatchRecords/' + dispatch.uuid, { returnedBaseAt: vm.dispatchToAdd.returnedBaseAt })
      })
      .then(function () {
        var pcrObj = {
          HospitalUuid: vm.dispatchToAdd.HospitalUuid,
          pcrPictureId: vm.dispatchToAdd.ImageDataId
        };
        if (vm.dispatchToAdd.arrivedHospitalAt) {
          pcrObj['arrivedHospitalAt'] = vm.dispatchToAdd.arrivedHospitalAt;
        }
        if (vm.dispatchToAdd.name) {
          pcrObj['name'] = vm.dispatchToAdd.name;
        }
        return $http.put('/Pcrs/' + pcr.uuid, pcrObj)
      })
      .then(function () {
        return $http.post('/Pcrs/updatePicturePdf/' + pcr.uuid, {
          "imageDataId": vm.dispatchToAdd.ImageDataId
        })
      })
      .then(function () {
        deferred.resolve();
        EPCRServices.successAlert('通知！', '建立成功！', null, vm.reset);
      })
      .catch(function (err) {
        deferred.resolve();
        var failmsg = err.data ? err.status + JSON.stringify(err.data) : err.status;
        EPCRServices.failAlert('通知！', '建立失敗！' + JSON.stringify(failmsg), null, vm.reset);
      })
  }


  function addPcr(deferred) {
    var newPcrUuid = Util.guid();
    var pcrObj = {
      "uuid": newPcrUuid,
      "DispatchRecordUuid": vm.dispatchToAdd.uuid,
      "age": 11988,
      "StatusId": 22, //已建立
      "HospitalUuid": vm.dispatchToAdd.HospitalUuid
    }
    if (vm.dispatchToAdd.arrivedHospitalAt) {
      pcrObj['arrivedHospitalAt'] = vm.dispatchToAdd.arrivedHospitalAt;
    }
    if (vm.dispatchToAdd.name) {
      pcrObj['name'] = vm.dispatchToAdd.name;
    }
    $http.post('/Pcrs/upsert/', pcrObj)
      .then(function () {
        return $http.post('/Pcrs/updatePicturePdf/' + newPcrUuid, {
          "imageDataId": vm.dispatchToAdd.ImageDataId
        })
      })
      .then(function () {
        var casedata2update = {}
        // if (vm.dispatchToAdd.address) {
        //   casedata2update['address'] = vm.dispatchToAdd.address;
        // }
        if (moment(vm.dispatchToAdd.returnedBaseAt).isAfter(vm.caseData[0].endedAt)) {
          casedata2update['endedAt'] = vm.dispatchToAdd.returnedBaseAt;
        }
        return $http.put('/CaseRecords/' + vm.caseData[0].id, casedata2update)
      })
      .then(function () {
        return $http.put('/DispatchRecords/' + vm.dispatchToAdd.uuid, { returnedBaseAt: vm.dispatchToAdd.returnedBaseAt })
      })
      .then(function () {
        deferred.resolve();
        EPCRServices.successAlert('通知！', '建立成功！', null, vm.reset)

      })
      .catch(function (err) {
        deferred.resolve();
        var failmsg = err.data ? err.status + JSON.stringify(err.data) : err.status;
        EPCRServices.failAlert('通知！', '建立失敗！' + JSON.stringify(failmsg), null, vm.reset)

      })
  }

  function updatePcr(deferred){
    var pcrObj = vm.pcrToAdd ;
    pcrObj['HospitalUuid'] = vm.dispatchToAdd.HospitalUuid ;

    if (vm.dispatchToAdd.arrivedHospitalAt) {
      pcrObj['arrivedHospitalAt'] = vm.dispatchToAdd.arrivedHospitalAt;
    }
    if (vm.dispatchToAdd.name) {
      pcrObj['name'] = vm.dispatchToAdd.name;
    }
    $http.post('/Pcrs/upsert/', pcrObj)
      .then(function () {
        return $http.post('/Pcrs/updatePicturePdf/' + vm.pcrToAdd.uuid, {
          "imageDataId": vm.dispatchToAdd.ImageDataId
        })
      })
      .then(function () {
        var casedata2update = {}
        if (moment(vm.dispatchToAdd.returnedBaseAt).isAfter(vm.caseData[0].endedAt)) {
          casedata2update['endedAt'] = vm.dispatchToAdd.returnedBaseAt;
        }
        return $http.put('/CaseRecords/' + vm.caseData[0].id, casedata2update)
      })
      .then(function () {
        return $http.put('/DispatchRecords/' + vm.dispatchToAdd.uuid, { returnedBaseAt: vm.dispatchToAdd.returnedBaseAt })
      })
      .then(function () {
        deferred.resolve();
        EPCRServices.successAlert('通知！', '更新成功！', null, vm.reset)

      })
      .catch(function (err) {
        deferred.resolve();
        var failmsg = err.data ? err.status + JSON.stringify(err.data) : err.status;
        EPCRServices.failAlert('通知！', '更新失敗！' + JSON.stringify(failmsg), null, vm.reset)

      })
  }
});
