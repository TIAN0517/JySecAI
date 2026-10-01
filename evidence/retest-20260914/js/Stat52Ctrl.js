CONTROLLERS.controller('Stat52Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 52.	救護車交通事故統計報表
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = '救護車交通事故統計報表';

		function getStat(search) {
			return $http.get('/Stat/stat52', {
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
