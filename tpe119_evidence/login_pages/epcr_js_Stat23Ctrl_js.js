CONTROLLERS.controller('Stat23Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = 'PCR正確率指標報表';

		function getStat(search) {
			return $http.get('/Stat/stat23', {
					params: {
						dateBegin: search.dateBegin,
						dateEnd: moment(search.dateEnd).endOf('day').format()
					},
					paramSerializer: '$httpParamSerializerJQLike'
				})
				.then(function(response) {
					return response.data;
				});
		}

		function showStat(search) {
			$scope.fields = [];
			$scope.tableData = [];

			getStat(search)
				.then(function(results) {
					$scope.fields = results.fields;

					angular.forEach(results.data, function(row) {
						if (row.totalNumber == 0) {
							row.Rate = '-';
						} // if
						else {
							row.Rate = Math.round((row.caseNumber / row.totalNumber * 100) * 100) / 100 + '%';
						} // else
					});

					$scope.tableData = results.data;
				})
				.catch(function(error) {
					EPCRServices.failAlert('錯誤', '取得統計結果時發生錯誤');
				});
		}

		$scope.showStat = showStat;

		$scope.datetimeCheck = function(search) {
			return !moment(search.dateBegin).isSameOrBefore(moment(search.dateEnd));
		};

	});
