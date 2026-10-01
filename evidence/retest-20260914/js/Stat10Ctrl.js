CONTROLLERS.controller('Stat10Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices) {
		// 10.	到院前心肺功能停止案件使用AED(自動體外電擊器)之心律變化
		$scope.search = {};
		$scope.title = '到院前心肺功能停止案件使用AED(自動體外電擊器)之心律變化';


		function getStat(search) {
			return $http.get('/Stat/stat10', {
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
			var tmp = { 'name': '本局' };

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

	});
