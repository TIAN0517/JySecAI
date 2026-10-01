CONTROLLERS.controller('Stat25Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 25.	TP Aspirin(藥物)使用指標報表
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = 'TP Aspirin(藥物)使用指標報表';

		function getStat(search) {
			return $http.get('/Stat/stat25', {
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
							row.CHPT2 = '-';
						} // if
						else {
							row.CHPT2 = Math.round((row.CHPT2 / row.Total * 100) * 100) / 100 + '%';
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
