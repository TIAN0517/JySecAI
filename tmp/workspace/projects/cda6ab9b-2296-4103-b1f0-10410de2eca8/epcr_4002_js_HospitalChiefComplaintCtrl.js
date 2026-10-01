CONTROLLERS.controller('HospitalChiefComplaintCtrl', function($q,$scope, $state,
 $http, AlertService, AuthService, NgTableParams, $element) {

  $scope.editAllHospitals = false;
  var hospitalUuid;

  var currentUser = AuthService.getCurrentUser();
  console.log('CURRENT USER:',currentUser);
  if(currentUser.role!='HOSPITAL'){
    $scope.editAllHospitals = true;
    $scope.inputData = { }
    $scope.HospitalList = [];
    getHospitals()
    .then(function(hospitals){
      $scope.HospitalList = hospitals;
    });
  }else{
    hospitalUuid = AuthService.getCurrentUser().customData;
    $scope.hospitalUuid = hospitalUuid;
    console.log('hospitalUuid',hospitalUuid)
    dataInit();
  }

  function getHospitals(){
    return $http.get('/Hospitals')
    .then(function(response){
      return response.data;
    })
  }

  function changeHospital(uuid){
    hospitalUuid = uuid;
    $scope.hospitalUuid = hospitalUuid;
    dataInit();
  }
  $scope.changeHospital = changeHospital;


function dataInit(idx){
   var ChiefComplaint;
   $http.get('/Hospitals', {
     params: {
       uuid: hospitalUuid,
       disabled: false
     },
     paramSerializer: '$httpParamSerializerJQLike'
   })
   .then(function(response){
   	// console.log('@@@response',response.data)
     if(response.data.length > 0){
       ChiefComplaint = response.data[0].ChiefComplaints;
       $scope.selectedChiefComplaint = ChiefComplaint;

       var chiefComplaintIds = []
       angular.forEach(ChiefComplaint, function(data){
         chiefComplaintIds.push(data.id)
       })

       return getAbility(chiefComplaintIds)
       .then(function(theChiefComplaints){
       	console.log('@@@theChiefComplaints',theChiefComplaints)
         $scope.ChiefComplaintList = {
           selected: null,
           lists: {
             "醫院收治量能清單": ChiefComplaint,
             "收治量能清單": theChiefComplaints
           }
         }
       })
     }else{
       AlertService.failAlert('錯誤！', '無法取得醫院資料', null);
     }
   })
 }


 $scope.addToChiefComplaint = function(){
   var insertData = [];
   angular.forEach($scope.selectedChiefComplaint, function(data){
     insertData.push({ChiefComplaintId:data.id,available:true});
   })

   var deferred = $q.defer()
   $scope.myPromise = deferred.promise

   $http.post('/Hospitals/setChiefComplaintOf/'+ hospitalUuid, {insertData:insertData})
   .then(function(response){
   	 AlertService.successAlert('通知！', '存檔成功！', null)
     deferred.resolve()
   })
   .catch(function(err){
     deferred.resolve()
     console.log('addToChiefComplaint err=', err)
   })
}

 var getAbility = function(chiefComplaintIds){
   return $http.get('/ChiefComplaints', {
     params: {
       notIn: chiefComplaintIds,
       sort: 'id'
     },
     paramSerializer: '$httpParamSerializerJQLike'
   })
   .then(function(response){
     return response.data
   })
 }


});
