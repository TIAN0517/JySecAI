app.controller('epcr106SuppliesStatBaseCtrl', function($scope, $controller) {

  // var statList = [];
  var statList = [
    { name: '耗材入庫統計', state: 'statBase2.suppliesStat01'},
    { name: '耗材出庫統計', state: 'statBase2.suppliesStat02'}
  ]

  $scope.base = {
    statList: statList
  }

  $controller('statBase2Ctrl', {
    $scope: $scope
  });
});
