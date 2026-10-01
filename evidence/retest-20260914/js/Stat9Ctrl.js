CONTROLLERS.controller('Stat9Ctrl',
	function($q, $modal, $scope, $state, $http, $element,
		NgTableParams, EPCRServices) {
		$scope.search = {};
		$scope.dateEnd = {};
		$scope.title = '本局暨各大隊救護反應時間分析表';

		function getStat(search) {
			return $http.get('/Stat/stat9', {
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
			var subTotal = 0;
			var subSecond = 0;
			var tmp = {
				'name': '本局',
				'totalSecond': null,
				'count': 0
			};

			getStat(search)
				.then(function(results) {
					$scope.fields = results.fields;

					angular.forEach(results.data, function(row) {
						if (_.isNil(row['totalSecond']))
							row['totalSecond'] = '-'
						else {
							if (_.isNil(tmp['totalSecond']))
								tmp['totalSecond'] = row['totalSecond'];
							else
								tmp['totalSecond'] += row['totalSecond'];
							tmp['count']++;
						} // else
					});

					if (_.isNil(tmp['totalSecond']) || tmp['count'] <= 0)
						tmp['totalSecond'] = '-';
					else
						tmp['totalSecond'] = _.toNumber(tmp['totalSecond']) / tmp['count'];

					results.data.push(tmp);
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
