CONTROLLERS.controller('Stat49Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 49.	每日OHCA追蹤紀錄報表
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = '每日OHCA追蹤紀錄報表';

		function getStat(search) {
			return $http.get('/Stat/stat49', {
					params: {
						dateBegin: moment(search.dateBegin).startOf('day').format(),
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
							row.haveBundle = '-';
						} // if
						else {
							row.haveBundle = Math.round((row.haveBundle / row.Total * 100) * 100) / 100 + '%';
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
