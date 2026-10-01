CONTROLLERS.controller('Stat24Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 24.	創傷病患後送醫院品管指標
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = '創傷病患後送醫院品管指標';

		function getStat(search) {
			return $http.get('/Stat/stat24', {
					params: {
						dateBegin: moment(search.dateBegin).startOf('day').format(),
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
						if (row.Total == 0) {
							row.HOSPITAL = '-';
						} // if
						else {
							row.HOSPITAL = Math.round((row.HOSPITAL / row.Total * 100) * 100) / 100 + '%';
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
