CONTROLLERS.controller('Stat48Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 48.	本局OHCA康復出院率
		$scope.search = {};
		$scope.title = '本局OHCA康復出院率';

		function getStat(search) {
			return $http.get('/Stat/stat48', {
					params: {
						dateBegin: search.dateBegin
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
							row.Rate = '-';
						} // if
						else {
							row.Total =row.Total; 
							row.Rate = Math.round((row.OutTotal / row.Total * 100) * 100) / 100 + '%';
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
