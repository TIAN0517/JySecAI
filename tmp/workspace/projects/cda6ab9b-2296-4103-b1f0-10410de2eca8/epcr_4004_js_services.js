var SERVICES = angular.module('services', ['LocalStorageModule'])
.factory('AlertServices', function(localStorageService, $http, $alert){
	var successAlert = function(title, content, time){
		var alert = $alert({
			title: title,
			content: content,
			container: '#body-alerts-tag',
			placement: 'alert-floater-modal alert-center btn-blue-alt font-size-20',
			duration: !_.isNil(time) ? time:3,
			type: 'info',
			show: true
		})
		return alert.$promise;
	}
	var failAlert = function(title, content, time){
		var alert = $alert({
			title: title,
			content: content,
			container: '#body-alerts-tag',
			placement: 'alert-floater-modal alert-center font-size-20',
			duration: !_.isNil(time) ? time:3,
			type: 'danger',
			show: true
		})
		return alert.$promise;
	}
	var successAlertToModal = function(title, content, time){
		var alert = $alert({
			title: title,
			content: content,
			container: '#alerts-tag',
			placement: 'alert-floater-modal alert-center-top font-size-18',
			duration: !_.isNil(time) ? time:3,
			type: 'info',
			show: true
		})
		return alert.$promise;
	}
	var failAlertToModal = function(title, content, time){
		var alert = $alert({
			title: title,
			content: content,
			container: '#alerts-tag',
			placement: 'alert-floater-modal alert-center-top font-size-18',
			duration: !_.isNil(time) ? time:3,
			type: 'danger',
			show: true
		})
		return alert.$promise;
	}



	var getDispatchRecords = function(dateBegin){
	   return $http.get('/DispatchRecords', {
         params: {
          dispatchedAT: {
            $gte: dateBegin
          },
          StatusId: {
            $notIn: [9,11,12]
          }
         },
         paramSerializer: '$httpParamSerializerJQLike'
       })
	}

	var getListBranchWithCaseRecordAndAmbulance = function(dateBegin){
	   return $http.get('/Branches/listBranchWithCaseRecordAndAmbulance                    ', {
         params: {
         },
         paramSerializer: '$httpParamSerializerJQLike'
       })
	}

	return {
		successAlert: successAlert,
		successAlertToModal: successAlertToModal,
		failAlert: failAlert,
		failAlertToModal: failAlertToModal,

		getDispatchRecords: getDispatchRecords,
		getListBranchWithCaseRecordAndAmbulance:getListBranchWithCaseRecordAndAmbulance,
	}
})


;
