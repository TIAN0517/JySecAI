CONTROLLERS.controller('Stat13Ctrl',
    function($q, $modal, $scope, $state,
        NgTableParams, $http, $element, EPCRServices) {
        $scope.search = {};
        $scope.dateEnd = {};
        $scope.title = '疑似腦中風案件評估指標';

        function getStat(search) {
            return $http.get('/Stat/stat13', {
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
            var subNumerator = 0;
            var tmp = { 'name': '本局' };

            getStat(search)
                .then(function(results) {
                    $scope.fields = results.fields;

                    angular.forEach(results.data, function(row) {
                        if (row.Total == 0) {
                            row.Numerator = '-';
                            row.Total = '-';
                            row.Rate = '-';
                        } // if
                        else {
                            row.Numerator = row.Numerator;
                            row.Total = row.Total;
                            row.Rate = Math.round((row.Numerator / row.Total * 100) * 100) / 100 + '%';
                            subNumerator += row.Numerator;
                            subTotal += row.Total;
                        } // else
                    });

                    if (subTotal == 0) {
                        tmp['Numerator'] = '-';
                        tmp['Total'] = '-';
                        tmp['Rate'] = '-';
                    } else {
                        tmp['Numerator'] = subNumerator;
                        tmp['Total'] = subTotal;
                        tmp['Rate'] = Math.round((subNumerator / subTotal * 100) * 100) / 100 + '%';
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
