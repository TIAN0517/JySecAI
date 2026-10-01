CONTROLLERS.controller('Stat27Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 27.	氧氣治療品管指標
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = '氧氣治療品管指標';

		function getStat(search) {
			return $http.get('/Stat/stat27', {
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
						if (row.Total_BRT5OR6 == 0) {
							row.BRT5OR6 = '-';
						} // if
						else {
							row.BRT5OR6 = Math.round((row.BRT5OR6 / row.Total_BRT5OR6 * 100) * 100) / 100 + '%';
						} // else

						if (row.Total_BRT7 == 0) {
							row.BRT7 = '-';
						} // if
						else {
							row.BRT7 = Math.round((row.BRT7 / row.Total_BRT7 * 100) * 100) / 100 + '%';
						} // else

						if (row.Total_BRT8 == 0) {
							row.BRT8 = '-';
						} // if
						else {
							row.BRT8 = Math.round((row.BRT8 / row.Total_BRT8 * 100) * 100) / 100 + '%';
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
