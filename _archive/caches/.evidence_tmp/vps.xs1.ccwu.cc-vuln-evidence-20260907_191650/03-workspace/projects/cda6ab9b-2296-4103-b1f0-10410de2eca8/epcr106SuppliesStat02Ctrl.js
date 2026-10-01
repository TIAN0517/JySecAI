app.controller('epcr106SuppliesStat02Ctrl', function($scope, $state, $http, $controller, $q) {
  $scope.search = {
    mode: 'DAY'
  };
  $scope.dateEnd = {};
  $scope.diagram = {
    threshold: 0,
    target: 0
  };
  $scope.title = '耗材出庫統計';
  $scope.getStat = getStat
  $scope.customParameter = {
    url: 'templates/stat106/epcr106StatParameters01.html'
  };
  $scope.exportUrl = '/stat/suppliesStat02ByDownload';

  init();

  function init() {
  } // init()

  function getStat(search) {
    return $http.get('/stat/epcr106SuppliesStats02', {
        params: {
          dateBegin: search.dateBegin,
          dateEnd: moment(search.dateEnd).endOf('day').format(),
          time : new Date().getTime()
        },
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(response) {
        return response.data;
      });
  } // getStat()

  $controller('epcr106SuppliesStatBaseCtrl', {
    $scope: $scope
  });

});
