CONTROLLERS.controller('Stat15Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = '各大隊TP 施打Amiodarone(藥物)品質指標';

		function getStat(search) {
			return $http.get('/Stat/stat15', {
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
						if (row.Total == 0) {
							row.Numerator = '-';
						} // if
						else {
							row.Numerator = Math.round((row.Numerator / row.Total * 100) * 100) / 100 + '%';
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
