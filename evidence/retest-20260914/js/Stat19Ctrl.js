CONTROLLERS.controller('Stat19Ctrl',
    function($q, $modal, $scope, $state,
        NgTableParams, $http, $element, EPCRServices) {
        $scope.search = {};
        $scope.dateEnd = {};
        $scope.title = '正壓給氧患者給予NPA(經鼻導管)或OPA(經口咽導管)指標報表';

        function getStat(search) {
            return $http.get('/Stat/stat19', {
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
                            row.NPA = '-';
                            row.OPA = '-';
                            row.Rate = '-';
                        } // if
                        else {
                            var tmpNPA=Math.round((row.NPA / row.Total * 100) * 100) / 100;
                            var tmpOPA=Math.round((row.OPA / row.Total * 100) * 100) / 100;
                            row.NPA = tmpNPA + '%';
                            row.OPA = tmpOPA + '%';
                            row.Rate = (tmpNPA+tmpOPA)+ '%';
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
