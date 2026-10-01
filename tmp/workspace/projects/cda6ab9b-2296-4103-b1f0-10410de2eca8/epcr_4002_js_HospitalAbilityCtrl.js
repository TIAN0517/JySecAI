CONTROLLERS.controller('HospitalAbilityCtrl', function($q,$scope, $state,
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
   var ability;
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
       ability = response.data[0].Abilities;
       $scope.selectedAbility = ability;

       var abilityIds = []
       angular.forEach(ability, function(data){
         abilityIds.push(data.id)
       })

       return getAbility(abilityIds)
       .then(function(theAbilitys){
        console.log('@@@ability',ability)
       	console.log('@@@theAbilitys',theAbilitys)
         $scope.AbilityList = {
           selected: null,
           lists: {
             "醫院收治能力清單": ability,
             "收治能力清單": theAbilitys
           }
         }
       })
     }else{
       AlertService.failAlert('錯誤！', '收治能力已被刪除！', null);
     }
   })
 }

 $scope.addToAbility = function(){
   var insertAbilityDatas = [];
   angular.forEach($scope.selectedAbility, function(data){
      var theCapacity;
      if(!_.isEmpty(data.HospitalAbilityMap)){
        theCapacity = data.HospitalAbilityMap.capacity;
      }

      insertAbilityDatas.push({
        AbilityId: data.id,
        capacity: theCapacity
      })

   })

   var deferred = $q.defer()
   $scope.myPromise = deferred.promise

   $http.post('/Hospitals/setAbilityOf/'+ hospitalUuid, {
     insertAbilityDatas: insertAbilityDatas
   })
   .then(function(response){
   	 AlertService.successAlert('通知！', '存檔成功！', null)
     deferred.resolve()
   })
   .catch(function(err){
     deferred.resolve()
     console.log('addToAbility err=', err)
   })
}

 var getAbility = function(abilityIds){
   return $http.get('/Abilities', {
     params: {
       notIn: abilityIds,
       sort: 'id'
     },
     paramSerializer: '$httpParamSerializerJQLike'
   })
   .then(function(response){
     return response.data
   })
 }


});
