CONTROLLERS.controller('Stat2Ctrl', function($q, $modal, $scope, $state,
  NgTableParams, $http, $element, EPCRServices) {

  $scope.search = {};
  $scope.dateEnd = {};
  $scope.title = '分隊出勤統計';

  function getStat(search) {
    return $http.get('/Stat/stat2', {
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
          if (row.total == 0) {
            row.canceled = '-';
            row.run = '-';
          } // if
          else {
            var canceled = Math.round((row.canceled / row.total * 100) * 100) / 100;
            row.canceled = canceled + '%';
            row.run = (100 - canceled) + '%';
          } // else
        });

        $scope.tableData = results.data;
      })
      .catch(function(error) {
        EPCRServices.failAlert('錯誤', '取得統計結果時發生錯誤');
      });
  }

  $scope.showStat = showStat;

});
