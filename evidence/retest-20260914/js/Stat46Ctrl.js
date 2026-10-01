CONTROLLERS.controller('Stat46Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 46.	每日OHCA患者AED使用及電擊率報表
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = '每日OHCA患者AED使用及電擊率報表';

		function getStat(search) {
			return $http.get('/Stat/stat46', {
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
							row.AED = '-';
							row.CRT10 = '-';
						} // if
						else {
							row.AED = Math.round((row.AED / row.Total * 100) * 100) / 100 + '%';
							row.CRT10 = Math.round((row.CRT10 / row.Total * 100) * 100) / 100 + '%';
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
