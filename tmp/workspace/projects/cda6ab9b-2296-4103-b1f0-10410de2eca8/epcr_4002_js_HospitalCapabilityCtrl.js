CONTROLLERS.controller('HospitalCapabilityCtrl', function($q,$scope, $state,
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
		console.log('hospitalUuid',hospitalUuid)
		$scope.tableAbility = tableAbilityInit();
		$scope.tableChiefComplaint = tableChiefComplaintInit();
		dataInit();
	}
	$scope.addCapacityAvailable ={}

	$scope.checkboxes = {
		checked: false,
		items: {}
	}

	$scope.ChiefComplaintCheckboxes = {
		checked: false,
		items: {}
	}

	function getHospitals(){
		return $http.get('/Hospitals')
		.then(function(response){
			return response.data;
		})
	}

	function changeHospital(uuid){
		hospitalUuid = uuid;
		$scope.tableAbility = tableAbilityInit();
		$scope.tableChiefComplaint = tableChiefComplaintInit();
		dataInit();
	}
	$scope.changeHospital = changeHospital;

 	$scope.selectedItem = function(id, boolean,type){
 		if(boolean){
 			if(type=='Ability'){
 				$scope.checkboxes.items[id] = false;
 				// $scope.addCapacityAvailable[id]=0
 			}else{
 				$scope.ChiefComplaintCheckboxes.items[id] = false;
 			}
 		}else{
 			if(type=='Ability'){
 				$scope.checkboxes.items[id] = true;
 				// $scope.addCapacityAvailable[id]=null
 			}else{
 				$scope.ChiefComplaintCheckboxes.items[id] = true;
 			}
 		}

 	}

 	$scope.checkedItem = function(id){
 		if($scope.checkboxes.items[id]){
 			$scope.addCapacityAvailable[id]=null
 		}else{
 			$scope.addCapacityAvailable[id]=0
 		}

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
	       	console.log('Abilities',response.data.Abilities)

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
	       	console.log('ChiefComplaints',response.data.ChiefComplaints)

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




function dataInit(){

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




$scope.toAdd = function(bool) {
	console.log('bool',bool)
if(!bool){
    AlertService.failAlert('警告！', '收治量能未填寫！', null)
	return
}

	return	setAbility()
	.then(function(){
	return setChiefComplaint()

	})
	.then(function(){
		AlertService.successAlert('通知！', '存檔成功！', null)
	})
   .catch(function(err){
         AlertService.failAlert('錯誤！', '收治量能無法存檔！', null)
         console.log('tableAbilityInit err =', err)
	})
}

var setAbility = function(){
	var insertAbilityDatas = []

	for (var key in $scope.checkboxes.items) {
		var insertabilityData = {}
		// var available=false
	    var capacity = 0;
	    if ($scope.checkboxes.items[key]) {
	    	// available=true

	    	if($scope.addCapacityAvailable[key]){
	    		capacity = $scope.addCapacityAvailable[key];
	    	}
	    	else{
	    		capacity = -1;
	    	}

	    	insertabilityData['AbilityId']=key
	    	insertabilityData['capacity']=capacity
	    	// insertabilityData['available']= false
	    	console.log('=====insertabilityData',insertabilityData)

	    }
	    else{
	    	insertabilityData['AbilityId']=key
	    	insertabilityData['capacity']=capacity
	    	insertabilityData['available']=false
	    }
	    insertAbilityDatas.push(insertabilityData)

    }

    console.log('@@@@@insertAbilityDatas',insertAbilityDatas)
	return $http.put('/Hospitals/setAbilityOf/' + hospitalUuid, {
		insertAbilityDatas: insertAbilityDatas
	})
}

var setChiefComplaint = function(){
	var insertData = []
		var available = false
	    for (var key in $scope.ChiefComplaintCheckboxes.items) {

		    if ($scope.ChiefComplaintCheckboxes.items[key]) {
		    	available=true

		    }else{
		    	available=false
		    }
        insertData.push({'ChiefComplaintId':key,'available':available})
    	}
	return $http.put('/Hospitals/setChiefComplaintOf/' + hospitalUuid, {
		insertData: insertData
	})
}


function getHospitalAbilityChiefComplaint(){
	return $http.get('/Hospitals/HospitalAbilityChiefComplaint/'+ hospitalUuid)
	.then(function(result){
		return result.data
	})
}


    // AbilityDataList watch
    $scope.$watch(function() {
        return $scope.checkboxes.checked;
    }, function(value) {

        angular.forEach(AbilityDataList, function(item) {
        	// console.log('AbilityDataList',$scope.checkboxes.items)
        	// console.log('value',value)
            $scope.checkboxes.items[item.id] = value;
        });
    });

    // AbilityDataList watch for data checkboxes
    $scope.$watch(function() {
        return $scope.checkboxes.items;
    }, function(values) {

        var checked = 0,
            unchecked = 0,
            total = AbilityDataList.length;
        angular.forEach(AbilityDataList, function(item) {
        	// console.log('dataList',AbilityDataList)
            checked += ($scope.checkboxes.items[item.id]) || 0;
            unchecked += (!$scope.checkboxes.items[item.id]) || 0;
        });
        if (total > 0 && ((unchecked == 0) || (checked == 0))) {
            console.log('checked=', checked, 'total=', total);
            $scope.checkboxes.checked = (checked == total);
        }
        // grayed checkbox
        angular.element($element[0].getElementsByClassName("select-all")).prop("indeterminate", (checked != 0 && unchecked != 0));
    }, true);


    // ChiefComplaintDataList watch
    $scope.$watch(function() {
        return $scope.ChiefComplaintCheckboxes.checked;
        // console.log('return ChiefComplaintDataList',$scope.ChiefComplaintCheckboxes)
    }, function(value) {

        angular.forEach(ChiefComplaintDataList, function(item) {
        	// console.log('value',value)
            $scope.ChiefComplaintCheckboxes.items[item.id] = value;
            // console.log('ChiefComplaintDataList',$scope.ChiefComplaintCheckboxes.items)
        });
    });

    // ChiefComplaintDataList watch for data checkboxes
    $scope.$watch(function() {
        return $scope.ChiefComplaintCheckboxes.items;
    }, function(values) {

        var checked = 0,
            unchecked = 0,
            total = ChiefComplaintDataList.length;
        angular.forEach(ChiefComplaintDataList, function(item) {
        	// console.log('dataList',ChiefComplaintDataList)
            checked += ($scope.ChiefComplaintCheckboxes.items[item.id]) || 0;
            unchecked += (!$scope.ChiefComplaintCheckboxes.items[item.id]) || 0;
        });
        if (total > 0 && ((unchecked == 0) || (checked == 0))) {
            console.log('checked=', checked, 'total=', total);
            $scope.ChiefComplaintCheckboxes.checked = (checked == total);
        }
        // grayed checkbox
        angular.element($element[0].getElementsByClassName("select-all-2")).prop("indeterminate", (checked != 0 && unchecked != 0));
    }, true);



});
