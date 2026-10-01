CONTROLLERS.controller('Stat42Ctrl',
  function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices) {
    // 42.	每日OHCA 患者2小時存活率
    $scope.search = {};
    $scope.title = '每日OHCA 患者2小時存活率';

    function getStat(search) {
      return $http.get('/Stat/stat42To45', {
          params: {
            dateBegin: moment(search.dateBegin).startOf('day').format(),
            hour: 2
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
            if (row['Total'] == 0) row['Result'] = '-';
            else
              row['Result'] = Math.round((row['Alive'] / row['Total'] * 100) * 100) / 100 + '%';
          });

          $scope.tableData = results.data;
        })
        .catch(function(error) {
          EPCRServices.failAlert('錯誤', '取得統計結果時發生錯誤');
        });
    }

    $scope.showStat = showStat;

  });
