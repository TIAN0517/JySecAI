CONTROLLERS.controller('Stat1Ctrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices) {
    $scope.search = {};
    $scope.dateEnd = {};
    $scope.title = '分隊救護主訴統計';

    function getStat(search) {
        return $http.get('/Stat/stat1', {
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


                var total = {};

                angular.forEach(results.data, function(data) {
                    angular.forEach(Object.keys(data), function(key) {
                        if (_.isNumber(data[key])) {
                            if (_.isNil(total[key])) total[key] = 0;
                            total[key] += _.toNumber(data[key]);
                        } // if
                    });
                });

                total['name'] = '總計';
                results.data.push(total);
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
