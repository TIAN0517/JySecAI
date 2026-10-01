CONTROLLERS.controller('HospitalCapabilityListForHealthCtrl', function($q,$scope, $state,
 $http, AlertService, AuthService, NgTableParams, $element,$stateParams) {

var hospitalUuid = $stateParams.hospitalUuid
console.log('hospitalUuid',hospitalUuid)
	$scope.addCapacityAvailable ={}

	$scope.checkboxes = {
		checked: false,
		items: {}
	}

	$scope.ChiefComplaintCheckboxes = {
		checked: false,
		items: {}
	}


 var AbilityDataList = [];
 var ChiefComplaintDataList =[]
	function tableAbilityInit(){
	   return new NgTableParams({
	     sorting: {}
	   }, {
	    pages: [],
	    counts: [],
	     filterDelay: 300,
	     getData: function(params){
	       var deferred = $q.defer();
	       $scope.anyPageBusy = deferred.promise;
	       var sortString;
	       // 如果使用 epilogue 免費 api sort需要做調整
	       // 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
	       // sortString = params.sorting();
	       for(var key in params.sorting()){
	         if(params.sorting()[key] == 'desc'){
	           sortString = '-' + key;
	         }else{
	           sortString = key;
	         }
	       }

	        return $http.get('/Hospitals/'+ hospitalUuid, {
		         paramSerializer: '$httpParamSerializerJQLike'
		       })
	       .then(function(response){
	       	// console.log('Abilities',response.data)
	       	AbilityDataList = response.data.Abilities
	         deferred.resolve()
	         return response.data.Abilities
	       })
	       .catch(function(err){
	         deferred.resolve();
	         console.log('tableAbilityInit err =', err)
	       })

	     }
	   })
	 }

  $scope.tableAbility = tableAbilityInit();


  function tableChiefComplaintInit(){
	   return new NgTableParams({
	     sorting: {}
	   }, {
	    pages: [],
	    counts: [],
	     filterDelay: 300,
	     getData: function(params){
	       var deferred = $q.defer();
	       $scope.anyPageBusy = deferred.promise;
	       var sortString;
	       // 如果使用 epilogue 免費 api sort需要做調整
	       // 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
	       // sortString = params.sorting();
	       for(var key in params.sorting()){
	         if(params.sorting()[key] == 'desc'){
	           sortString = '-' + key;
	         }else{
	           sortString = key;
	         }
	       }

	        var dateBegin = moment().subtract(24, 'hours').toDate()
	        return $http.get('/Hospitals/'+ hospitalUuid, {
		         paramSerializer: '$httpParamSerializerJQLike'
		       })
	       .then(function(response){
	       	// console.log('ChiefComplaints',response.data)
	       	ChiefComplaintDataList = response.data.ChiefComplaints
	         deferred.resolve()
	         return response.data.ChiefComplaints
	       })
	       .catch(function(err){
	         deferred.resolve();
	         console.log('tableAbilityInit err =', err)
	       })

	     }
	   })
	 }

  $scope.tableChiefComplaint = tableChiefComplaintInit();


 var dataInit = function(){

 	return $http.get('/Abilities')
 	.then(function(result){
 		// console.log('Abilities result',result.data)
 		for(idx in result.data){
 			$scope.checkboxes.items[result.data[idx].id] = false;
 		}
	return $http.get('/ChiefComplaints')
 	})
 	.then(function(result){
 		// console.log('ChiefComplaints result',result.data)
 		for(idx in result.data){
 			$scope.ChiefComplaintCheckboxes.items[result.data[idx].id] = false;
 		}

 		return getHospitalAbilityChiefComplaint()
 	})
	.then(function(result){
		console.log('@@@result',result)
		for(var idx in result){
			for(var abilityIdx in result[idx].Abilities){
				var ability = result[idx].Abilities[abilityIdx]
				if(ability.HospitalAbilityMap.available){
					$scope.checkboxes.items[ability.id] = true;
				}
				else{
					$scope.checkboxes.items[ability.id] = false;
				}

				if(ability.isCapacityAvailable){
					$scope.addCapacityAvailable[ability.id] = ability.HospitalAbilityMap.capacity
				}
				$scope.abilityReportedAt = ability.HospitalAbilityMap.reportedAt
			}

			for(var ChiefComplaintIdx in result[idx].ChiefComplaints){
				var ChiefComplaint = result[idx].ChiefComplaints[ChiefComplaintIdx]
				if(ChiefComplaint.HospitalChiefComplaintMap.available){
					$scope.ChiefComplaintCheckboxes.items[ChiefComplaint.id] = true;
				}else{

					$scope.ChiefComplaintCheckboxes.items[ChiefComplaint.id] = false;
				}
				$scope.chiefComplaintreportedAt = ChiefComplaint.HospitalChiefComplaintMap.reportedAt
			}
		}
	})
 }

dataInit();

function getHospitalAbilityChiefComplaint(){
	return $http.get('/Hospitals/HospitalAbilityChiefComplaint/'+ hospitalUuid)
	.then(function(result){
		return result.data
	})
}

});
