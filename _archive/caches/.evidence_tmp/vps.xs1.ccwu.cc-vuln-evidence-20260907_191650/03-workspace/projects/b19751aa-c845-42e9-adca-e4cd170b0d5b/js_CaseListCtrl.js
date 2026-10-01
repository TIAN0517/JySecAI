CONTROLLERS.controller('CaseListCtrl',
	function($q, $modal, $scope, $state, $http, $element, $window,
		NgTableParams, EPCRServices, AuthService) {

		var hospitalUuid;
		var currentUser = AuthService.getCurrentUser();
		$scope.search = {};

		$scope.TOKEN = AuthService.getToken();

		function getBranchId(currentUser){
		    if(currentUser && currentUser.role){
		        if(currentUser.role=='BRANCH'){
		            return currentUser.customData;
		        }
		    }
		    return null;
		}

		function getPcrDoctorOrderStatus(){
			return $http.get('/PcrDoctorOrderStatus')
			.then(function(response){
				return response.data;
			})
		}

		function getAmbulanceList(branchId){
			return $http.get('/Ambulances/byUserRole',{
				params: {
					BranchId: branchId
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
			.then(function(response){
				return response.data;
			})
		}

		function setupAmbulanceList(branchId){
			return getAmbulanceList(branchId)
			.then(function(results){
				$scope.showAmbulances = _.keyBy(results, 'id');
			})
		}

		var currentBranchId = getBranchId(currentUser);
		$scope.currentBranchId = currentBranchId;
		if(currentBranchId){
			$scope.search.BranchId = currentBranchId;
		}



		console.log('CURRENT USER', currentUser);
		if (currentUser.role != 'HOSPITAL') {
			$scope.isHospital = false;
			hospitalUuid = null;
		} // if
		else {
			$scope.isHospital = true;
			hospitalUuid = currentUser.customData;
		} // else

		var searchParams = {
			isSimulation: false,
			isRealTime: false
		};

		$scope.hasTPList = {
			false: '否',
			true: '是'
		}

		$scope.clear = function() {
			$scope.search = {};
			searchParams = {
				isSimulation: false
			}
			refreshList();
		}

		$scope.searchCase = function(search) {
			searchParams = {};

			if ((search.dateBegin && _.isNil(search.dateEnd)) || (_.isNil(search.dateBegin) && search.dateEnd)) {
				return EPCRServices.failAlert('錯誤！', '請輸入起迄區間！', null)
			}
			if (search.dateBegin && search.dateEnd) {
				if (search.dateBegin > search.dateEnd) {
					return EPCRServices.failAlert('警告！', '起迄時間錯誤！', null)
				}

				var dateBegin = moment(search.dateBegin).startOf('day').toDate();
				var dateEnd = moment(search.dateEnd).endOf('day').toDate();
				search['dateBegin'] = dateBegin;
				search['dateEnd'] = dateEnd;
			}

			for (var key in search) {
				console.log("search[key]", search[key])
				if (!_.isNil(search[key])) {

					searchParams[key] = search[key];
					console.log("searchParams", searchParams)
				}
			}
			$scope.tableParams = tableInit();
		}


		function dataInit() {
			return $http.get('/Branches?disabled=false')
				.then(function(response) {
					//分隊清單
					$scope.showBranches = _.keyBy(response.data, 'id')
					return $http.get('/Hospitals')
				})
				.then(function(response) {
					//醫院清單
					$scope.showHospitals = _.keyBy(response.data, 'uuid')
					return $http.get('/')
				})
				.then(function(response) {
					//案件狀態
					$scope.showStatus = _.keyBy(response.data, 'id')
					return $http.get('/json/hasTP.json')
				})
				.then(function(response) {
					//TP狀態
					$scope.showTPStatus = _.keyBy(response.data, 'id')
					//只取用10000~19999 與CaseRecord 有關的狀態
					return $http.get('/Statuses?code[$between][0]=10000&code[$between][1]=19999')
				})
				.then(function(response) {
					$scope.showStatuses = _.keyBy(response.data, 'id');
					return $http.get('/json/isSimulation.json')
				})
				.then(function(response) {
					$scope.showSimulation = _.keyBy(response.data, 'id');
					return setupAmbulanceList()
				})
				.then(function(){
					return getPcrDoctorOrderStatus();
				})
				.then(function(results){
					$scope.PcrDoctorOrderStatusList = results;
				});
		}
		dataInit();

		$scope.showDetail = function(index) {
			var pcrUuid = responseList[index].uuid;
			$window.open('/#/caseDetail/' + pcrUuid, '_blank');
		}

		$scope.showPrint = function(index) {
			var pcrUuid = responseList[index].uuid;
			$window.open('/#/caseDetailPrint/' + pcrUuid + '/' + 1, '_blank');
		}

		$scope.showTemsis = function(index){
			var pcrUuid = responseList[index].uuid;
			window.open('/#/caseTemsis/' + pcrUuid, '_blank');
		}

		$scope.showuploadPicPdf = function(index) {
			var row = responseList[index] ;
			var fullCaseSN = row.DispatchRecord.CaseRecord.recordUuid +'-'+ 
			row.DispatchRecord.serialNumber +'-'+  
			row.serialNumber ;
			
			$window.open('/Pcrs/getPdfByCaseSN/' + fullCaseSN + '?token=' + $scope.TOKEN, '_blank');
		}

		$scope.branchChanged = function(branchId){
			setupAmbulanceList(branchId);
		}


		$scope.caseRuning = function() {
			$scope.search = {};
			searchParams = {
				StatusId: 4, //案件結束，執行中的案件不應該出現結束案件
				isRealTime: true
			};
			console.log("caseRuning", searchParams)
			refreshList();
		}

		function refreshList() {
			$scope.checkboxes = {
				checked: false,
				items: {}
			}
			var dateEnd = new Date();
			var dateBegin = moment(dateEnd).subtract(1, 'day').toDate();
			searchParams['dateBegin'] = dateBegin;
			searchParams['dateEnd'] = dateEnd;
			$scope.tableParams = tableInit();
		}

		refreshList();

		var responseList = []

		function tableInit() {
			return new NgTableParams({
				page: 1, // show first page
				count: 10, // count per page,
				sorting: {
					// createdAt: 'desc'
				}
			}, {
				filterDelay: 300,
				getData: function(params) {
					var deferred = $q.defer();
					$scope.anyPageBusy = deferred.promise;
					console.log(params.sorting())
					var url = params.url();
					var limit = url.count,
						skip = url.count * (url.page - 1);
					var sortString;
					// 如果使用 epilogue 免費 api sort需要做調整
					// 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
					sortString = params.sorting();
					// for (var key in params.sorting()) {
					//     if (params.sorting()[key] == 'desc') {
					//         sortString = '-' + key;
					//     } else {
					//         sortString = key;
					//     }
					// }

					var query = {
						sort: sortString,
						offset: skip,
						count: limit,
						time: new Date().getTime()
					}

					if (!_.isEmpty(searchParams)) {
						for (var key in searchParams) {
							query[key] = searchParams[key];
						}
					}

					if (hospitalUuid) {
						query['HospitalUuid'] = hospitalUuid;
					} // if

					console.log("query", query)

					return $http.get('/Pcrs/pcrCaseList', {
							params: query,
							paramSerializer: '$httpParamSerializerJQLike'
						})
						.then(function(response) {
							var range = contentRange.parse(response.headers('Content-Range'));
							var count = range.length;
							params.total(count);
							responseList = response.data;
							deferred.resolve()
							console.log('@@ list=', responseList)
							return responseList
						})
						.catch(function(err) {
							deferred.resolve();
							console.log('tableInit err =', err)
						})

				}
			})
		}

		// watch for check all checkbox
		$scope.$watch(function() {
			return $scope.checkboxes.checked;
		}, function(value) {
			angular.forEach(responseList, function(item) {
				$scope.checkboxes.items[item.id] = value;
			});
		});
		// watch for data checkboxes
		$scope.$watch(function() {
			return $scope.checkboxes.items;
		}, function(values) {
			var checked = 0,
				unchecked = 0,
				total = responseList.length;
			angular.forEach(responseList, function(item) {
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

		// 取得分隊id (若使用者屬於特定分隊，就只能查詢該分隊的案件

	});
