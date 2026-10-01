var SERVICES = angular.module('services', ['LocalStorageModule'])
.factory('EPCRServices', function(localStorageService, $http, $alert){
	var successAlert = function(title, content, time, onHideCB){
		var alert = $alert({
			title: title,
			content: content,
			container: '#body-alerts-tag',
			placement: 'alert-floater-modal alert-center btn-blue-alt font-size-20',
			duration: !_.isNil(time) ? time:3,
			type: 'info',
			show: true,
			onHide:onHideCB
		})
		return alert.$promise;
	}
	var failAlert = function(title, content, time, onHideCB){
		var alert = $alert({
			title: title,
			content: content,
			container: '#body-alerts-tag',
			placement: 'alert-floater-modal alert-center font-size-20',
			duration: !_.isNil(time) ? time:3,
			type: 'danger',
			show: true,
			onHide:onHideCB
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
.factory('PrintFormatSvc', function(){
	function findInQAMAP(code,qamap){
		if ( qamap[code] ){
			var q = qamap[code].displayLabel ;
			var a = [];
			qamap[code].PcrAnswers.forEach(function(ans){
				a.push(ans.displayLabel);
			})
				return {q:q,a:a} ;
		}

	};
	function findInQARecord(code,qarecord){
		for ( var i = 0 ; i < qarecord.length ; i++ ){
			var blocks = qarecord[i];
			var blocksAry = Object.keys(blocks) ;
			for ( var j = 0 ; j < blocksAry.length ; j++ ){
				var block = blocks[blocksAry[j]] ;
				for ( var k = 0 ; k < block.questions.length ; k++ ){
					if ( block.questions[k].code == code ){
						return block.questions[k] ;
					}
				}
			}
		}
		return null ;
	};

	function convertBundles2Map(bundles){
		var qaRecordMap = {} ;
		bundles.forEach(function(bundle){
			if (bundle.PcrCategoryId != 805) {
				for (var i = 0 ; i < bundle.PcrRecords.length ; i++){
					var record = bundle.PcrRecords[i] ;
					qaRecordMap[record.PcrQuestion.code] = record ;
				}
			}else{
				return ;
			}
		})

		return qaRecordMap ;
	}



	return {
		findInQAMAP:findInQAMAP,
		findInQARecord:findInQARecord,
		convertBundles2Map:convertBundles2Map
	}
})
.factory('Util',function(){
	function guid() {
		function s4() {
		  return Math.floor((1 + Math.random()) * 0x10000)
			.toString(16)
			.substring(1);
		}
		return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
		  s4() + '-' + s4() + s4() + s4();
	  } // guid
	return {
		guid:guid
	}
})
;
