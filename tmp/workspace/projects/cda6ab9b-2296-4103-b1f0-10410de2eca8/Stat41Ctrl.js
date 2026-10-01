CONTROLLERS.controller('Stat41Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 41.	每日OHCA患者件數
		$scope.search = {};
		// $scope.dateEnd = {};
		$scope.title = '每日OHCA患者件數';

		function getStat(search) {
			return $http.get('/Stat/stat41', {
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
					$scope.tableData = results.data;

					if ($scope.tableData.length == 0) {
						var row = {
							Date: moment(search.dateBegin).format('YYYY-MM-DD'),
							Total: 0
						};

						$scope.tableData.push(row);
					} // if
				})
				.catch(function(error) {
					EPCRServices.failAlert('錯誤', '取得統計結果時發生錯誤');
				});
		}

		$scope.showStat = showStat;

	});
