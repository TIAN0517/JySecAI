app.controller('epcr106StatBaseCtrl', function($scope, $controller, AuthService, $state) {

  // var statList = [];
  var statList = []

  // 根據權限給予不同報表清單
  if (AuthService.checkPerm('EPCR_PAGE_STAT_MANAGER')) {
    statList = [
    	{ name: '新北市消防緊急救護急救處置', state: 'statBase2.stat01' },
      { name: '新北市消防緊急救護服務', state: 'statBase2.stat02'},
      { name: '緊急救護各項時間統計表', state: 'statBase2.stat03'},
      { name: '各大隊施打靜脈輸液品質指標', state: 'statBase2.stat04'},
      { name: '各大隊施打5GW品質指標', state: 'statBase2.stat05'},
      { name: '未建立IV原因', state: 'statBase2.stat06'},
      // { name: '總表', state: 'statBase2.105Stat40'},
      { name: '匯總報表', state: 'statBase2.stat07'},
      { name: 'OHCA產出總表', state: 'statBase2.statFormBundle01'},
      { name: 'OHCA品管產出總表', state: 'statBase2.statFormBundle02'},
      { name: '到院未急救(不計入母數)', state: 'statBase2.statFormBundle03'},
      { name: 'OHCA人數資訊表', state: 'statBase2.statFormBundle04'},
      { name: 'OHCA分析報表', state: 'statBase2.statFormBundle05'},
      { name: 'UTSTEIN', state: 'statBase2.statFormBundle06'},
      { name: 'OHCA倒地場所', state: 'statBase2.statFormBundle07'},
      { name: '醫療院所康復出院', state: 'statBase2.statFormBundle08'}
    ];
  } // if
  else if (AuthService.checkPerm('EPCR_PAGE_STAT_BRANCHGROUP')){
    statList = [
      { name: '匯總報表', state: 'statBase2.stat07'},
    ];
  } // else if
  else if (AuthService.checkPerm('EPCR_PAGE_STAT_BRANCH')){
    statList = [
      { name: '匯總報表', state: 'statBase2.stat07'},
    ];
  } // else


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

  $controller('statBase2Ctrl', {
    $scope: $scope
  });
});
