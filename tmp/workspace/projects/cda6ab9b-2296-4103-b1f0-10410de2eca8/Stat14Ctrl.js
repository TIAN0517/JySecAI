CONTROLLERS.controller('Stat14Ctrl',
    function($q, $modal, $scope, $state,
        NgTableParams, $http, $element, EPCRServices) {
        $scope.search = {};
        $scope.dateEnd = {};
        $scope.title = '疑似高能量撞擊或墜落傷案件創傷處置執行狀況';

        function getStat(search) {
            return $http.get('/Stat/stat14', {
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
            var subCount=0;
            var tmp = { 'name': '本局' };

            getStat(search)
                .then(function(results) {
                    $scope.fields = results.fields;

                    angular.forEach(results.data, function(row) {
                        if (row.Total == 0) {
                            row.Numerator = '-';
                        } // if
                        else {
                           var tmpValue = Math.round((row.Numerator / row.Total * 100) * 100) / 100
                            row.Numerator = tmpValue + '%';
                            subTotal += tmpValue;
                            subCount++;
                        } // else
                    });
                    if (subTotal == 0) {
                        tmp['Numerator'] = '-';
                        tmp['Total'] = 0;
                    } else {
                        tmp['Numerator'] = Math.round(( subTotal/subCount ) * 100) / 100 + '%';
                    }
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
