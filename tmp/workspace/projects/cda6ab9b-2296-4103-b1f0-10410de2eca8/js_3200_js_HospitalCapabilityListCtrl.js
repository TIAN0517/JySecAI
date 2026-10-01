CONTROLLERS.controller('HospitalCapabilityListCtrl', function($q,$scope, $state,
 $http, AlertService, AuthService, NgTableParams, $element) {



	$scope.checkCapabilityList = function(uuid){
		console.log('uuid',uuid)
        $state.go('hospitalCapabilityListForHealth', { hospitalUuid: uuid });
	}


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

	        return $http.get('/Hospitals/HospitalAbilityChiefComplaintList', {
		         paramSerializer: '$httpParamSerializerJQLike'
		       })
	       .then(function(response){
	       	console.log('Hospitals',response.data)

	       	angular.forEach(response.data, function(theHospital){
	       		theHospital.Abilities = _.keyBy(theHospital.Abilities, 'id')
	       		theHospital.ChiefComplaints = _.keyBy(theHospital.ChiefComplaints, 'id')
	       	});

	         deferred.resolve()
	         return response.data
	       })
	       .catch(function(err){
	         deferred.resolve();
	         console.log('tableAbilityInit err =', err)
	       })

	     }
	   })
	 }

  $scope.tableAbility = tableAbilityInit();




});
