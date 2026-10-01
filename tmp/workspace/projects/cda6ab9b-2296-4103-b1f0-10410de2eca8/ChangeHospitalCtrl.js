CONTROLLERS.controller('ChangeHospitalCtrl', function($scope, $state,
 $http, EPCRServices, AuthService) {

 $scope.vm = {} ;
 var vm = $scope.vm ;

 vm.checkDisabled = function(){
   if (vm.noHos){
     return false ;
   }else if (!vm.hospitalUuid) {
     return true ;
   }else if (vm.editDate) {
     return !(vm.arriveHos && vm.leftHos) ;
   }else {
     return false ;
   }
 }

 vm.clearHos = function(){
   vm.hospitalUuid = null ;
   vm.editDate = false ;
 }

 function getCaseData(recordUuid,dispatchRecordSerialNumber,pcrSerialNumber) {
   return $http.get('/Pcrs/pcrCaseList', {
       params: {
         recordUuid: recordUuid,
         DispatchRecordSerialNumber:dispatchRecordSerialNumber,
         PcrSerialNumber:pcrSerialNumber
       },
       paramSerializer: '$httpParamSerializerJQLike'
     })
     .then(function(response) {
       return response.data
     });
 } // getCaseData()

 function getHospitalData(){
   return $http.get('/Hospitals', {
     params: {
       sort: 'name',
       disabled: false
     },
     paramSerializer: '$httpParamSerializerJQLike'
   })
   .then(function(response){
     return response.data
   })
 }

 function updateHospitalData(body){
   return $http.post('/ChangeHospital', body)
   .then(function(response){
     return response.data
   })
 }

 function concatCaseId(pcrCaseData){
   var _caseid = pcrCaseData.DispatchRecord.CaseRecord.recordUuid
   + "-" + pcrCaseData.DispatchRecord.serialNumber
   + "-" + pcrCaseData.serialNumber ;
   return _caseid ;
 }

 $scope.vm.searchCase = function(caseId){
   vm.msg = {};
   vm.hospitalUuid = null ;
   vm.editDate = false ;
   vm.showHospital = false ;
   vm.arriveHos = null ;
   vm.leftHos = null ;

   var array = caseId.split('-');
   if(array.length!=3){
     vm.msg =  {"錯誤":"案件號格式錯誤"} ;
     return ;
   }
   var recordUuid = array[0];
   var dispatchSerial = array[1];
   var pcrSerial = array[2];
   getCaseData(recordUuid,dispatchSerial,pcrSerial)
   .then(function(data){
     vm.caseData = data ;
     if ( vm.caseData && vm.caseData.length >0 ){
       
      var pcrCaseData = _.find(vm.caseData, {serialNumber:Number(pcrSerial)})
      if (!pcrCaseData){
        throw new Error("找不到該案件") ;
      }
       vm.msg =
       {
         "案件編號":concatCaseId(pcrCaseData),
         "出勤單位":pcrCaseData.DispatchRecord.Ambulance.name,
         "派遣時間":moment(pcrCaseData.DispatchRecord.CaseRecord.dispatchedAt).format("YYYY-MM-DD HH:mm:ss"),
         "患者姓名":pcrCaseData.name,
         "發生地點":pcrCaseData.DispatchRecord.CaseRecord.address
       }

       if (!(pcrCaseData.Hospital)){
         throw new Error("該案件無設定醫院，無法修改") ;
       }else{
          vm.msg["後送醫院"] = pcrCaseData.Hospital.name;
          vm.msg["到院時間"] = moment(pcrCaseData.arrivedHospitalAt).format("YYYY-MM-DD HH:mm:ss");
          vm.msg["離院時間"] = moment(pcrCaseData.leftHospitalAt).format("YYYY-MM-DD HH:mm:ss");
       }
       vm.showHospital = true ;
       return getHospitalData();

     }else{
       throw new Error("找不到該案件") ;
     }
   })
   .then(function(hospitalData){
     vm.hospitalData = hospitalData ;
   })
   .catch(function(e){
     vm.msg["錯誤"] = e.message;
   })
 }

 $scope.vm.edit = function(vm){
   var body = {};
   if ( vm.editDate && vm.arriveHos && vm.leftHos ){
     body["arriveHos"] = vm.arriveHos ;
     body["leftHos"] = vm.leftHos ;
     body["editDate"] = vm.editDate ;
   }
   body["hospitalUuid"] = vm.hospitalUuid ;
   body["caseRecordSerial"] = vm.searchCaseId ;
   updateHospitalData(body)
   .then(function(result){
     $scope.vm.searchCase(vm.searchCaseId);
   })

 }

 var options = {
    "singleDatePicker": true,
    "showDropdowns": true,
    "minYear": 1920,
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
        "daysOfWeek": ["日","一","二","三","四","五","六"],
        "monthNames": ["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"],
        "firstDay": 1
    },
    "linkedCalendars": false,
    "showCustomRangeLabel": false,
    "drops": "auto"
};
  var datepCB = function(start, end, label) {
    console.log('New date range selected: ' + start.format() + label );
  }
  $("#arriveHos").daterangepicker(options,datepCB);
  $("#leftHos").daterangepicker(options,datepCB);
});
