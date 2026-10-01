app.controller('StatBaseCtrl', function($scope, $controller, AuthService, $state) {

  // var statList = [];
  var statList = []

  if (AuthService.checkPerm('HOSPITAL_PAGE_STAT')) {
    statList = [
      { name: '回溯報表', state: 'statBase.stat01'},
      { name: '送醫紀錄報表', state: 'statBase.stat02'},
      { name: '匯總報表', state: 'statBase.stat03'},
    ];
  } // if


  if(!_.isEmpty(statList)) {
    if (!_.find(statList, { state: $state.current.name})) $state.go(statList[0].state);
  } // if
  else {
    alert('沒有對應的權限進到此畫面:' + $state.current.name);
    $state.go('login');
  } // else

  $scope.base = {
    statList: statList
  }

});
