CONTROLLERS.controller('svgInOpStatusCtrl', function($q, $scope, $filter, $http, $state, $modal, NgTableParams, $timeout, $window,
  $stateParams, $rootScope, $controller,
  $document
  ) {
  
  $scope.status = {
    getOpStatus: getOpStatus
  };
  $scope.opStatus = [];

  /*
    contactedAt
    arrivedHospitalAt
    handOverAt
    leftHospitalAt
    endforMciAt

    dispatchedAt
    departedAt
    arrivedAt
    leftAt
    returnedBaseAt
    canceledAt
    endforMciAt
    refusedAt
  */

  function getTimeFromDispatchRecord(id,code,title,colName){
    if(!_.isNil($scope.status.Pcr.DispatchRecord) && !_.isNil($scope.status.Pcr.DispatchRecord[colName])){
      $scope.opStatus.push({
        id: id,
        code: code,
        title: title,
        endshape: 1,
        time: moment($scope.status.Pcr.DispatchRecord[colName]).format('HH:mm'),
        isDefaultSeq: 1
      })
    }else{
      $scope.opStatus.push({
        id: id,
        code: code,
        title: title,
        endshape: 1,
        time: '',
        isDefaultSeq: 1   // 順序不對的話，字會變顏色，但這邊沒實作，所以預設正常
      })
    }
  }

  function getTimeFromPcr(id,code,title,colName){
    if(!_.isNil($scope.status.Pcr) && !_.isNil($scope.status.Pcr[colName])){
      $scope.opStatus.push({
        id: id,
        code: code,
        title: title,
        endshape: 1,
        time: moment($scope.status.Pcr[colName]).format('HH:mm'),
        isDefaultSeq: 1
      })
    }else{
      $scope.opStatus.push({
        id: id,
        code: code,
        title: title,
        endshape: 1,
        time: '',
        isDefaultSeq: 1   // 順序不對的話，字會變顏色，但這邊沒實作，所以預設正常
      })
    }
  }

  function fillCheckPoint(){
    if(_.isNil($scope.status.Pcr)) { return; }
    // id & code 是給 directive 識別用，隨便填不重覆即可
    getTimeFromDispatchRecord(1,100,'出勤','departedAt');
    getTimeFromDispatchRecord(2,200,'到場','arrivedAt');
    getTimeFromDispatchRecord(3,300,'離場','leftAt');

    getTimeFromPcr(4,400,'到院','arrivedHospitalAt');
    getTimeFromPcr(5,500,'離院','leftHospitalAt');
    
    getTimeFromDispatchRecord(6,600,'離場','returnedBaseAt');
  }

  function getOpStatus(){
    $scope.opStatus = [];
    fillCheckPoint();
    $scope.refreshStatus = moment().format('yyyyMMddHHmmssSSS');
  }

})
