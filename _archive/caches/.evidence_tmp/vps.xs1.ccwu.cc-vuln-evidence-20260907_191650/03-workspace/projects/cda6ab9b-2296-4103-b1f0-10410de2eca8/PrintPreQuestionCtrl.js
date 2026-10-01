CONTROLLERS.controller('PrintPreQuestionCtrl', function($q,
$scope, $filter, $http, $state, $stateParams) {

  var params = $stateParams;

  $scope.views = [];

  $scope.colspanA = {
    "1":2,
    "2":1
  };




  return $http.get('/FormattedEPCR/byPcr/' + params['pcrUuid'])
  .then(function(response){
    $scope.views = response.data[1];
    return $http.get('/json/printFormat.json')
  })
  .then(function(result){
    $scope.printFormat = result.data ;
  })

})
