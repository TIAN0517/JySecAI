app.config(function($stateProvider) {
  $stateProvider
    // .state('base.statDetail', {
    //   url: '/statdetail?search&title&detailUrl&exportUrl',
    //   templateUrl: 'templates/stat/statDetail.html',
    //   controller: 'StatDetailCtrl'
    // })
    .state('statBase2.stat01', {
      url: '/stat01',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr106Stat01Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.stat02', {
      url: '/stat02',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr106Stat02Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.stat03', {
      url: '/stat03',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr106Stat03Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.stat04', {
      url: '/stat04',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr106Stat04Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.stat05', {
      url: '/stat05',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr106Stat05Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.stat06', {
      url: '/stat06',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr106Stat06Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.105Stat40', {
      url: '/105Stat40',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr105Stat40Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.stat07', {
      url: '/stat07',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcr106Stat07Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER', 'EPCR_PAGE_STAT_BRANCHGROUP', 'EPCR_PAGE_STAT_BRANCH'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.statFormBundle01', {
      url: '/statFormBundle01',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcrStatFormBundle01Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER', 'EPCR_PAGE_STAT_BRANCHGROUP', 'EPCR_PAGE_STAT_BRANCH'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.statFormBundle02', {
      url: '/statFormBundle02',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcrStatFormBundle02Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER', 'EPCR_PAGE_STAT_BRANCHGROUP', 'EPCR_PAGE_STAT_BRANCH'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.statFormBundle03', {
      url: '/statFormBundle03',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcrStatFormBundle03Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER', 'EPCR_PAGE_STAT_BRANCHGROUP', 'EPCR_PAGE_STAT_BRANCH'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.statFormBundle04', {
      url: '/statFormBundle04',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcrStatFormBundle04Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER', 'EPCR_PAGE_STAT_BRANCHGROUP', 'EPCR_PAGE_STAT_BRANCH'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.statFormBundle05', {
      url: '/statFormBundle05',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcrStatFormBundle05Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER', 'EPCR_PAGE_STAT_BRANCHGROUP', 'EPCR_PAGE_STAT_BRANCH'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.statFormBundle06', {
      url: '/statFormBundle06',
      templateUrl: 'templates/stat106/statBase02.html',
      controller: 'epcrStatFormBundle06Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER', 'EPCR_PAGE_STAT_BRANCHGROUP', 'EPCR_PAGE_STAT_BRANCH'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.statFormBundle07', {
      url: '/statFormBundle07',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcrStatFormBundle07Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER', 'EPCR_PAGE_STAT_BRANCHGROUP', 'EPCR_PAGE_STAT_BRANCH'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase2.statFormBundle08', {
      url: '/statFormBundle08',
      templateUrl: 'templates/stat106/statBase.html',
      controller: 'epcrStatFormBundle08Ctrl',
      data: {
        permissions: {
          only: ['EPCR_PAGE_STAT_MANAGER', 'EPCR_PAGE_STAT_BRANCHGROUP', 'EPCR_PAGE_STAT_BRANCH'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
});
