CONTROLLERS.controller('Stat4Ctrl',
    function($q, $modal, $scope, $state,
        NgTableParams, $http, $element, EPCRServices) {
        $scope.search = {};
        $scope.dateEnd = {};
        $scope.title = '各大隊呼吸道及進階呼吸道氣管內管(ENDO)使用品質指標';

        function getStat(search) {
            return $http.get('/Stat/stat4', {
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
                            row.ENDO = '-';
                        } // if
                        else {
                            row.ENDO = Math.round((row.ENDO / row.Total * 100) * 100) / 100 + '%';
                            
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
