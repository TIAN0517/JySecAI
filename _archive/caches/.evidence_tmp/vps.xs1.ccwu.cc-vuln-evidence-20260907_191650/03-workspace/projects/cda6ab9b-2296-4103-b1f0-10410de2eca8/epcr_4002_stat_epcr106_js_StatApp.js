app.config(function($stateProvider) {
  $stateProvider
    .state('statBase', {
      url: '/statBase',
      abstract: true,
      template: '' +
        '<div>' +
        '  <div ng-include="\'templates/menu/menuTop.html\'"></div>' +
        '  <ui-view></ui-view>' +
        '</div>',
      controller: function() {},
      data: {
        requiresLogin: true
      }
    })
    .state('statBase.default', {
      url: '/default',
      template: '',
      controller: 'StatBaseCtrl',
      data: {
        requiresLogin: true
      }
    })
    .state('statBase.stat01', {
      url: '/stat01',
      templateUrl: 'stat/epcr106/templates/statBase.html',
      controller: 'Stat01Ctrl',
      data: {
        permissions: {
          only: ['HOSPITAL_PAGE_STAT'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase.stat02', {
      url: '/stat02',
      templateUrl: 'stat/epcr106/templates/statBase.html',
      controller: 'Stat02Ctrl',
      data: {
        permissions: {
          only: ['HOSPITAL_PAGE_STAT'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })
    .state('statBase.stat03', {
      url: '/stat03',
      templateUrl: 'stat/epcr106/templates/statBase.html',
      controller: 'Stat03Ctrl',
      data: {
        permissions: {
          only: ['HOSPITAL_PAGE_STAT'],
          redirectTo: 'login'
        },
        requiresLogin: true
      }
    })

});

