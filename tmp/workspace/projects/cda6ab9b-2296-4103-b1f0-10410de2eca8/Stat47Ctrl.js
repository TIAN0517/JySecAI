CONTROLLERS.controller('Stat47Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 47.	每日OHCA患者AED審查報表
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = '每日OHCA患者AED審查報表';

		function getStat(search) {
			return $http.get('/Stat/stat47', {
					params: {
						dateBegin: moment(search.dateBegin).startOf('day').format(),
						dateEnd: moment(search.dateBegin).endOf('day').format()
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

					if (results.data.length == 0) {
						var row = {
							Date: moment(search.dateBegin).format('YYYY-MM-DD'),
							Total: 0
						};

						results.data.push(row);
					} // if

					angular.forEach(results.data, function(row) {
						if (row.Total == 0) {
							row.RATING1_1 = '-';
							row.RATING1_2 = '-';
						} // if
						else {
							row.RATING1_1 = Math.round((row.RATING1_1 / row.Total * 100) * 100) / 100 + '%';
							row.RATING1_2 = Math.round((row.RATING1_2 / row.Total * 100) * 100) / 100 + '%';
						} // else
					});

					$scope.tableData = results.data;
				})
				.catch(function(error) {
					EPCRServices.failAlert('錯誤', '取得統計結果時發生錯誤');
				});
		}

		$scope.showStat = showStat;

	});
