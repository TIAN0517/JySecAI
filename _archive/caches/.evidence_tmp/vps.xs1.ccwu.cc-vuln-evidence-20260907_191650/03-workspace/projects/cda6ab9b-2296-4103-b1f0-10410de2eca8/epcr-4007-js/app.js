var app = angular.module('EPCRServer', ['controllers',
  'services', 'directives', 'ui.router', 'mgcrea.ngStrap', 'ngAnimate',
  'LocalStorageModule', 'cgBusy', 'ngTable',
  'ngMap', 'nvd3','dndLists','swfobject', 'lr.upload',
/****************** PERMISSION + JWT ******************/
  'angular-jwt','permission', 'permission.ui',
/****************** PERMISSION + JWT ******************/
  'formly','formlyBootstrap','daterangepicker',
/** 新式 Formly OHCA 回溯問卷 **/
  'formlyCustomText','formlyCustomCollapseBlock','formlyCustomRadio','formlyCustomCheckbox',
  'formlyCustomInt','formlyCustomDate','formlyCustomDateTime','formlyCustomSelect',
  'formlyCustomRepeatSection','formlyCustomString','formlyCustomDisplay','formlyCustomTime'

]);

app.config(function($modalProvider, formlyConfigProvider) {
    angular.extend($modalProvider.defaults, {
        html: true
    });
    formlyConfigProvider.setWrapper({
      name: 'panel',
      templateUrl: 'templates/formly/panel.html'
    });
});

app.config(function($stateProvider, $urlRouterProvider, jwtOptionsProvider,
  $httpProvider, $locationProvider) {
  $locationProvider.hashPrefix('');
  /****************** PERMISSION + JWT ******************/
  /*  Where to get token */
  jwtOptionsProvider.config({
    tokenGetter: ['$location',function($location) {
      var tokenQs = $location.search().token;
      if(tokenQs){
        localStorage.setItem(AUTH_LOCALSTORAGE_KEY, tokenQs);
        return tokenQs;
      }else{
        return localStorage.getItem(AUTH_LOCALSTORAGE_KEY);
      }
    }],
    // unauthenticatedRedirector: ['$state','AuthService', function($state, AuthService) {
    //       $state.go('login');
    // }],
    whiteListedDomains: ['localhost','epcr.tpf.gov.tw','118.163.107.93','35.234.50.28']
  });
  /* Intercept HTTP request */
  // $httpProvider.interceptors.push('jwtInterceptor');
  /****************** PERMISSION + JWT ******************/

  $stateProvider
  .state('login', {
    url: '/login',
    templateUrl: 'templates/login.html',
    controller: 'LoginCtrl',
  })
  .state('logout', {
    url: '/logout',
    template: 'logout',
    controller: 'LogoutCtrl',
  })
  .state('resourceManagement', {
    url: '/resourceManagement',
    templateUrl: 'templates/resourceManagement.html',
    controller: 'ResourceManagementCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_RESOURCEMANAGEMENT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('monitor', {
    url: '/monitor',
    templateUrl: 'templates/monitor.html',
    controller: 'MonitorCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_MONITOR',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('caseList', {
    url: '/caseList',
    templateUrl: 'templates/caseList.html',
    controller: 'CaseListCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_CASELIST',
        redirectTo: 'login'
      },
      requiresLogin: true
    }

  })
  .state('caseListForBranchGroupDoctor', {
    url: '/caseListForBranchGroupDoctor',
    templateUrl: 'templates/caseListForBranchGroupDoctor.html',
    controller: 'CaseListForBranchGroupDoctorCtrl',
    data:{
      permissions: {
        only: 'EPCR_DOCTOR_ORDER',
        redirectTo: 'login'
      },
      requiresLogin: true
    }

  })
  .state('ohcaCaseList', {
    url: '/ohcaCaseList',
    templateUrl: 'templates/backtrack/main.html',
    controller: 'OhcaCaseListCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_OHCACASELIST',
        redirectTo: 'login'
      },
      requiresLogin: true
    }

  })
  .state('changeHospital', {
    url: '/changeHospital',
    templateUrl: 'templates/changeHospital.html',
    controller: 'ChangeHospitalCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_CHANGEHOS',
        redirectTo: 'login'
      },
      requiresLogin: true
    }

  })
  .state('uploadPcrPicture', {
    url: '/uploadPcrPicture',
    templateUrl: 'templates/uploadPcrPicture.html',
    controller: 'UploadPcrPictureCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_CASELIST',
        redirectTo: 'login'
      },
      requiresLogin: true
    }

  })
  .state('caseDetail', {
    url: '/caseDetail/:uuid',
    templateUrl: 'templates/caseDetail.html',
    controller: 'CaseDetailCtrl',
    params: {
      uuid: null,
    },
    data:{
      permissions: {
        only: 'EPCR_PAGE_CASEDETAIL',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('caseDetailPrint', {
    url: '/caseDetailPrint/:uuid/:isShow',
    templateUrl: 'templates/caseDetailPrint.html',
    controller: 'CaseDetailPrintCtrl',
    params: {
      uuid: null,
      isShow: null
    },
    data:{
      permissions: {
        only: 'EPCR_PAGE_CASEDETAILPRINT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('caseDetailPrintByCaseSN', {
    url: '/caseDetailPrintByCaseSN/:caseSN',
    templateUrl: 'templates/caseDetailPrint.html',
    controller: 'CaseDetailPrintCtrl',
    params: {
      caseSN: null,
      isShow: 0
    },
    data:{
      permissions: {
        only: 'EPCR_PAGE_CASEDETAILPRINT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('caseTemsis', {
    url: '/caseTemsis/:uuid',
    templateUrl: 'templates/caseTemsis.xml',
    // controller: 'CaseDetailCtrl',
    params: {
      uuid: null,
    },
    data:{
      permissions: {
        only: 'EPCR_PAGE_CASEDETAIL',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })

  .state('mciList', {
    url: '/mciList',
    templateUrl: 'templates/mciList.html',
    controller: 'MciListCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_MCILIST',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('mciDetail', {
    url: '/mciDetail/:CaseRecordId',
    templateUrl: 'templates/mciDetail.html',
    controller: 'MciDetailCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_MCIDETAIL',
        redirectTo: 'login'
      },
      requiresLogin: true
    },
    params: {
      CaseRecordId: null
    }
  })
  .state('branch', {
    url: '/branch',
    templateUrl: 'templates/branch.html',
    controller: 'BranchCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_BRANCH',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('branchGroup', {
    url: '/branchGroup',
    templateUrl: 'templates/branchGroup.html',
    controller: 'BranchGroupCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_BRANCHGROUP',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('hospital', {
    url: '/hospital',
    templateUrl: 'templates/hospital.html',
    controller: 'HospitalCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_HOSPITAL',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('device', {
    url: '/device',
    templateUrl: 'templates/device.html',
    controller: 'DeviceCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_DEVICE',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('ambulance', {
    url: '/ambulance',
    templateUrl: 'templates/ambulance.html',
    controller: 'AmbulanceCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_AMBULANCE',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('emt', {
    url: '/emt',
    templateUrl: 'templates/emt.html',
    controller: 'EmtCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_EMT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('emtLevel', {
    url: '/emtLevel',
    templateUrl: 'templates/emtLevel.html',
    controller: 'EmtLevelCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_EMTLEVEL',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('emtTraining', {
    url: '/emtTraining',
    templateUrl: 'templates/emtTraining.html',
    controller: 'EmtTrainingCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_EMTTRAINING',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('emtTrainingType', {
    url: '/emtTrainingType',
    templateUrl: 'templates/emtTrainingType.html',
    controller: 'EmtTrainingTypeCtrl',
    data:{
      permissions: {
        only: 'EPCR_PAGE_EMTTRAININGTYPE',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat1',{
    url: '/stat1',
    templateUrl: 'templates/stat/stat1.html',
    controller: 'Stat1Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat2',{
    url: '/stat2',
    templateUrl: 'templates/stat/stat2.html',
    controller: 'Stat2Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat3',{
    url: '/stat3',
    templateUrl: 'templates/stat/stat3.html',
    controller: 'Stat3Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat4',{
    url: '/stat4',
    templateUrl: 'templates/stat/stat4.html',
    controller: 'Stat4Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat5',{
    url: '/stat5',
    templateUrl: 'templates/stat/stat5.html',
    controller: 'Stat5Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat6',{
    url: '/stat6',
    templateUrl: 'templates/stat/stat6.html',
    controller: 'Stat6Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat7',{
    url: '/stat7',
    templateUrl: 'templates/stat/stat7.html',
    controller: 'Stat7Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat8',{
    url: '/stat8',
    templateUrl: 'templates/stat/stat8.html',
    controller: 'Stat8Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat9',{
    url: '/stat9',
    templateUrl: 'templates/stat/stat9.html',
    controller: 'Stat9Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat10',{
    url: '/stat10',
    templateUrl: 'templates/stat/stat10.html',
    controller: 'Stat10Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat11',{
    url: '/stat11',
    templateUrl: 'templates/stat/stat11.html',
    controller: 'Stat11Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat12',{
    url: '/stat12',
    templateUrl: 'templates/stat/stat12.html',
    controller: 'Stat12Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat13',{
    url: '/stat13',
    templateUrl: 'templates/stat/stat13.html',
    controller: 'Stat13Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat14',{
    url: '/stat14',
    templateUrl: 'templates/stat/stat14.html',
    controller: 'Stat14Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat15',{
    url: '/stat15',
    templateUrl: 'templates/stat/stat15.html',
    controller: 'Stat15Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat16',{
    url: '/stat16',
    templateUrl: 'templates/stat/stat16.html',
    controller: 'Stat16Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat17',{
    url: '/stat17',
    templateUrl: 'templates/stat/stat17.html',
    controller: 'Stat17Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat18',{
    url: '/stat18',
    templateUrl: 'templates/stat/stat18.html',
    controller: 'Stat18Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat19',{
    url: '/stat19',
    templateUrl: 'templates/stat/stat19.html',
    controller: 'Stat19Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat20',{
    url: '/stat20',
    templateUrl: 'templates/stat/stat20.html',
    controller: 'Stat20Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat21',{
    url: '/stat21',
    templateUrl: 'templates/stat/stat21.html',
    controller: 'Stat21Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat22',{
    url: '/stat22',
    templateUrl: 'templates/stat/stat22.html',
    controller: 'Stat22Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat23',{
    url: '/stat23',
    templateUrl: 'templates/stat/stat23.html',
    controller: 'Stat23Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat24',{
    url: '/stat24',
    templateUrl: 'templates/stat/stat24.html',
    controller: 'Stat24Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat25',{
    url: '/stat25',
    templateUrl: 'templates/stat/stat25.html',
    controller: 'Stat25Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat26',{
    url: '/stat26',
    templateUrl: 'templates/stat/stat26.html',
    controller: 'Stat26Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat27',{
    url: '/stat27',
    templateUrl: 'templates/stat/stat27.html',
    controller: 'Stat27Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat28',{
    url: '/stat28',
    templateUrl: 'templates/stat/stat28.html',
    controller: 'Stat28Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat29',{
    url: '/stat29',
    templateUrl: 'templates/stat/stat29.html',
    controller: 'Stat29Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat40',{
    url: '/stat40',
    templateUrl: 'templates/stat/stat40.html',
    controller: 'Stat40Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat41',{
    url: '/stat41',
    templateUrl: 'templates/stat/stat41.html',
    controller: 'Stat41Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat42',{
    url: '/stat42',
    templateUrl: 'templates/stat/stat42.html',
    controller: 'Stat42Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat43',{
    url: '/stat43',
    templateUrl: 'templates/stat/stat43.html',
    controller: 'Stat43Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat44',{
    url: '/stat44',
    templateUrl: 'templates/stat/stat44.html',
    controller: 'Stat44Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat45',{
    url: '/stat45',
    templateUrl: 'templates/stat/stat45.html',
    controller: 'Stat45Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat46',{
    url: '/stat46',
    templateUrl: 'templates/stat/stat46.html',
    controller: 'Stat46Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat47',{
    url: '/stat47',
    templateUrl: 'templates/stat/stat47.html',
    controller: 'Stat47Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat48',{
    url: '/stat48',
    templateUrl: 'templates/stat/stat48.html',
    controller: 'Stat48Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat49',{
    url: '/stat49',
    templateUrl: 'templates/stat/stat49.html',
    controller: 'Stat49Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat50',{
    url: '/stat50',
    templateUrl: 'templates/stat/stat50.html',
    controller: 'Stat50Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat51',{
    url: '/stat51',
    templateUrl: 'templates/stat/stat51.html',
    controller: 'Stat51Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('stat52',{
    url: '/stat52',
    templateUrl: 'templates/stat/stat52.html',
    controller: 'Stat52Ctrl',
    data: {
      permissions: {
        only: 'EPCR_PAGE_STAT',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })

  .state('test',{
    url: '/test',
    templateUrl: 'templates/test.html',
    controller: 'TestCtrl',
    data: {
      requiresLogin: true
    }
  })
  .state('suppliesConfig',{
    url: '/suppliesConfig',
    templateUrl: 'templates/suppliesConfig.html',
    controller: 'SuppliesConfigCtrl',
    data: {
      requiresLogin: true
    }
  })
  .state('suppliesQuery',{
    url: '/suppliesQuery',
    templateUrl: 'templates/suppliesQuery.html',
    controller: 'SuppliesQueryCtrl',
    data: {
      requiresLogin: true
    }
  })
  .state('suppliesInventory',{
    url: '/suppliesInventory',
    templateUrl: 'templates/suppliesInventory.html',
    controller: 'SuppliesInventoryCtrl',
    data: {
      requiresLogin: true
    }
  })
  .state('suppliesStockOut',{
    url: '/suppliesStockOut',
    templateUrl: 'templates/suppliesStockOut.html',
    controller: 'SuppliesStockOutCtrl',
    data: {
      requiresLogin: true
    }
  })
  .state('suppliesStockIn',{
    url: '/suppliesStockIn',
    templateUrl: 'templates/suppliesStockIn.html',
    controller: 'SuppliesStockInCtrl',
    data: {
      requiresLogin: true
    }
  })
  .state('suppliesRequest',{
    url: '/suppliesRequest',
    templateUrl: 'templates/suppliesRequest.html',
    controller: 'SuppliesRequestCtrl',
    data: {
      requiresLogin: true
    }
  })
  .state('suppliesIssuance',{
    url: '/suppliesIssuance',
    templateUrl: 'templates/suppliesIssuance.html',
    controller: 'SuppliesIssuanceCtrl',
    data: {
      requiresLogin: true
    }
  })
  .state('suppliesRequestDetailPrint',{
    url: '/suppliesRequestDetailPrint/:id',
    templateUrl: 'templates/print/suppliesRequestDetailPrint.html',
    controller: 'SuppliesRequestDetailPrintCtrl',
    data: {
      requiresLogin: true
    },
    params: {
      id: null
    }
  })
  .state('suppliesQueryPrint',{
    url: '/suppliesQueryPrint/:SuppliesUserId',
    templateUrl: 'templates/print/suppliesQueryPrint.html',
    controller: 'SuppliesQueryPrintCtrl',
    data: {
      requiresLogin: true
    },
    params: {
      SuppliesUserId: null
    }
  })

  .state('checkPERM',{
    url: '/checkperm',
    template: '<h1>PASS!!!</h1>',
    data: {
      requiresLogin: true,
      permissions: {
        only: ['BRANCHGROUPDOCTOR']
      }
    }
  })

  .state('print2',{
    url: '/print2/:pcrUuid',
    templateUrl: 'templates/print/printPreQuestion.html',
    controller: 'PrintPreQuestionCtrl',
    data: {
      requiresLogin: false
    },
    params: {

    }
  })

  .state('backtrackingEditor',{
    url: '/backtrackingEditor/:pcrUuid?categoryId&debugModel&debugFields',
    templateUrl: 'templates/backtrackingEditor.html',
    controller: 'BackTrackingEditorCtrl'
  })

  .state('centerBacktrack',{
    url: '/centerBacktrack/:mainData',
    templateUrl: 'templates/backtrack/center.html',
    controller: 'BackTrackingEditorCtrl',
    params: {
      uuids: [],
      categoryId: null
    }
  })
  .state('qcBacktrack',{
    url: '/qcBacktrack/:mainData',
    templateUrl: 'templates/backtrack/qc.html',
    controller: 'BackTrackingEditorCtrl',
    params: {
      uuids: [],
      categoryId: null
    }
  })

  // if none of the above states are matched, use this as the fallback
  $urlRouterProvider.otherwise( function($injector) {
    var $state = $injector.get("$state");
    var AuthService = $injector.get("AuthService");
    var targetState = AuthService.getDefaultState()
    $state.go(targetState);

  });

})
.run(function($rootScope, $state, AuthService, PermPermissionStore, PermRoleStore,
  /*authManager,*/ $window, $document, formlyConfig, $parse, jwtHelper, jwtOptions,
   $injector, $timeout, $interval, $location,PUBLIC_CONFIG) {

    // formlyConfig.setType({
    //   name: 'Select',
    //   templateUrl: 'templates/formly/Select.html'
    // });
    // formlyConfig.setType({
    //   name: 'String',
    //   templateUrl: 'templates/formly/String.html'
    // });
    // formlyConfig.setType({
    //   name: 'Checkbox',
    //   templateUrl: 'templates/formly/Checkbox.html'
    // });

  var modals = [];
  // auto track $modal windows
  $rootScope.$on('modal.show', function(e, $modal) {
      // if modal is not already in list
      if (modals.indexOf($modal) === -1) {
          modals.push($modal);
      }
      if (modals.length >= 0) {
          $document.find('body').addClass('modal-open');
      }
  });
  // un-track $modal windows on hide
  $rootScope.$on('modal.hide', function(e, $modal) {
      var modalIndex = modals.indexOf($modal);
      modals.splice(modalIndex, 1);
      if (modals.length === 0) {
          $document.find('body').removeClass('modal-open');
      }
  });

  /****************** PERMISSION + JWT ******************/
  function permissionfunc(permissionName, transitionProperties){
    return AuthService.checkPerm(permissionName);
  }
  // __PERMISSION_MAP__ 來自 www/js/permissionlist.js
  for(var roleName in __PERMISSION_MAP__){
    var permissionList = __PERMISSION_MAP__[roleName];
    for(var idx in permissionList){
      var perm = permissionList[idx];
      PermPermissionStore.definePermission(perm, permissionfunc);
    }
    PermRoleStore.defineRole(roleName, permissionList)
  }

/* 因為authManager 提供的方法不能在refresh token之後繼續前往原本的state
   因此不再使用authManager (也不要inject authManager 到 run()裡面) */
  // authManager.redirectWhenUnauthenticated();
  // authManager.checkAuthOnRefresh();
  // $rootScope.$on('tokenHasExpired', function() {
  //     console.log('tokenHasExpired');
  // });

/* 當state 轉移時，檢查token是否有效
   若無效就試著refresh
   refresh成功的話，就重新前往原本要去的state */
  $rootScope.$on('$stateChangeStart',
  function(event, toState, toParams, fromState, fromParams, options){
    console.log('$stateChangeStart to', toState.name);
    verifyRoute(event, toState, toParams, options)
  })

  var refreshPromise = null;

  function invokeToken(tokenGetter) {
    var token = null;
    if (Array.isArray(tokenGetter)) {
      token = $injector.invoke(tokenGetter, this, {options: null});
    } else {
      token = tokenGetter();
    }
    return token;
  }

  function verifyRoute(event, toState, toParams, options) {
    if (!toState) {
      return false;
    }

    var routeData = (toState.$$route) ? toState.$$route : toState.data;

    if (routeData && routeData.requiresLogin === true) {
      var config = jwtOptions.getConfig();
      var token = invokeToken(config.tokenGetter);

      try{
        if (!token || jwtHelper.isTokenExpired(token)) {
          event.preventDefault();
          if(refreshPromise==null){
            refreshPromise = AuthService.refreshToken()
              .then(function(){
                $state.go(toState.name, toParams, options)
              })
              .catch(function(err){
                console.log(err);
                AuthService.logout();
              })
              .finally(function(){
                refreshPromise = null;
              })
          }
        }
      }catch(err){
        console.log('verifyRoute error:',err);
        AuthService.logout();
      }
    }
  }


  $rootScope.$on('$stateChangePermissionStart', function(event, toState, toParams, options) {
      console.log('$stateChangePermissionStart to:', toState);
  });
  $rootScope.$on('$stateChangePermissionAccepted', function(event, toState, toParams, options) {
      console.log('$stateChangePermissionAccepted to:', toState);
  });
  $rootScope.$on('$stateChangePermissionDenied', function(event, toState, toParams, options) {
      console.log('$stateChangePermissionDenied to:', toState.name);
      alert('沒有對應的權限進到此畫面:'+toState.name);
  });
  /****************** PERMISSION + JWT ******************/

/**** 偵測使用者閒置 ****/
  if(PUBLIC_CONFIG.MAX_IDLE_DURATION){
    var countDownBegin = null;
    var countDownTimer = null;
    var idleTimer = null;
    startIdleTimer();

    $rootScope.$on('WholeBodyCtrl.userAlive', function(event){
        startIdleTimer();
    })

    function idleTimerHandler(){
      console.log('USER IDLE TIMEOUT.')
      $interval.cancel(countDownTimer);
      AuthService.logout();
    }

    function startCountDown(){
      var countDownBegin = new Date();
      countDownTimer = $interval(countDownHandler, 1000,0,true, countDownBegin);
    }

    function startIdleTimer(){
      if(idleTimer!=null){
        // 取消現有的
        $timeout.cancel(idleTimer);
      }
      if(countDownTimer!=null){
        $interval.cancel(countDownTimer);
      }
      if($state.current.name==""){
        return;
      }
      if(PUBLIC_CONFIG.NO_IDLE_DETECTION_STATES){
        if(PUBLIC_CONFIG.NO_IDLE_DETECTION_STATES.includes($state.current.name)){
          // console.log('skip timer. state=', $state.current.name)
          return;
        }
      }
      console.log('start new idle timer.', $state.current.name)
      idleTimer = $timeout(idleTimerHandler, PUBLIC_CONFIG.MAX_IDLE_DURATION)
      startCountDown();
    }


    function countDownHandler(countDownBegin){
      var message = moment.duration(moment(countDownBegin)
        .add(PUBLIC_CONFIG.MAX_IDLE_DURATION, 'ms').diff(moment())).format('HH:mm:ss');
      $rootScope.$emit('idleTimer.countDown',message)
    }

    $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams){
      console.log('$stateChangeSuccess', toState.name)
      startIdleTimer();
    })
  }
/**** 偵測使用者閒置 ****/


  formlyConfig.extras.fieldTransform = formlyConfig.extras.fieldTransform || [];
  formlyConfig.extras.fieldTransform.push(removeOnHideTransformer);

  var fieldsMap = [];

  function removeOnHideTransformer(fields) {
    return fields.map(function(field) {
      if(fieldsMap.includes(field)){
          return field;
      }else{
          fieldsMap.push(field);
      }
      field.data = field.data || {};

      if (field.key && !field.noFormControl && field.hideExpression && !field.data.dontRemoveOnHidden) {
        addFieldRemoveOnHideWatcher(field);
      } else if (field.fieldGroup) {
        field.fieldGroup = removeOnHideTransformer(field.fieldGroup);
      }
      if(field.templateOptions && field.templateOptions.options){
          for(var i in field.templateOptions.options){
              var option = field.templateOptions.options[i];
              if(option.nextQuestions){
                  option.nextQuestions = removeOnHideTransformer(option.nextQuestions);
              }
          }
      }
      return field;
    });
  }

  function addFieldRemoveOnHideWatcher(field) {


    var watcher = getWatcher();
    if (field.watcher) {
      if (!angular.isArray(field.watcher)) {
        field.watcher = [field.watcher];
      }
      field.watcher.push(watcher);
    } else {
      field.watcher = watcher;
    }
  }

  function removeModelOfNextQuestion(model, field){
      if(field.templateOptions && field.templateOptions.options){
          for(var i in field.templateOptions.options){
              var option = field.templateOptions.options[i];
              if(option.nextQuestions){
                  for(var j in option.nextQuestions){
                      var nq = option.nextQuestions[j];
                      var nGetter = $parse(nq.key);
                      nGetter.assign(model, undefined);
                      removeModelOfNextQuestion(model, nq);
                  }
              }
          }
      }
  }

  function getWatcher() {
    return {
      expression: function(field) {
        return field.hide;
      },
      listener: function(field, newHide, oldHide, scope) {
        var model = field.model || scope.model; // default to the field's model
        /* istanbul ignore else */
        if (field.hide) {
          var getter = $parse(field.key);
          // field.data.preHiddenValue = getter(model);
          getter.assign(model, undefined);
          removeModelOfNextQuestion(model, field);
        // } else if (field.data.preHiddenValue !== undefined) {
        //   $parse(field.key).assign(model, field.data.preHiddenValue);
        } else {
          // do nothing.
        }
      }
    };
  }


})
