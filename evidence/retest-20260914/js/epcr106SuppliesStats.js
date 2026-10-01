app.config(function($stateProvider) {
  $stateProvider
    // .state('base.statDetail', {
    //   url: '/statdetail?search&title&detailUrl&exportUrl',
    //   templateUrl: 'templates/stat/statDetail.html',
    //   controller: 'StatDetailCtrl'
    // })
    .state('statBase2.suppliesStat01', {
      url: '/suppliesStat01',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr106SuppliesStat01Ctrl'
    })
    .state('statBase2.suppliesStat02', {
      url: '/suppliesStat02',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr106SuppliesStat02Ctrl'
    })
});
