var app = angular.module('HospitalServer', ['controllers',
    'services', 'ui.router', 'mgcrea.ngStrap', 'ngAnimate',
    'LocalStorageModule', 'cgBusy', 'ngTable',
    /****************** PERMISSION + JWT ******************/
    'angular-jwt', 'permission', 'permission.ui',
    /****************** PERMISSION + JWT ******************/
    'formly', /*'formlyBootstrap',*/ 'dndLists', 'ui.toggle',
    'daterangepicker',
    'formlyCustomText','formlyCustomCollapseBlock','formlyCustomRadio','formlyCustomCheckbox',
    'formlyCustomInt','formlyCustomDate','formlyCustomDateTime','formlyCustomSelect'
]);

app.config(function($modalProvider) {
    angular.extend($modalProvider.defaults, {
        html: true
    });

});

app.config(function($stateProvider, $urlRouterProvider, jwtOptionsProvider,
        $httpProvider, $locationProvider, formlyConfigProvider) {
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
            unauthenticatedRedirector: ['AuthService', function(AuthService) {
                AuthService.logout();
            }],
            whiteListedDomains: ['localhost','epcr.tpf.gov.tw','118.163.107.93','47.97.114.73','35.234.50.28']
        });
        /* Intercept HTTP request */
        $httpProvider.interceptors.push('jwtInterceptor');
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
            .state('hospital', {
                url: '/hospital',
                templateUrl: 'templates/hospital.html',
                controller: 'HospitalCtrl',
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_HOSPITAL',
                        redirectTo: 'login'
                    },
                    requiresLogin: true
                }
            })
            .state('hospitalCapability', {
                url: '/hospitalCapability',
                templateUrl: 'templates/hospitalCapability.html',
                controller: 'HospitalCapabilityCtrl',
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_HOSPITALCAPABILITY',
                        redirectTo: 'login'
                    },
                    requiresLogin: true
                }
            })
            // 回溯編輯畫面
            .state('backtrackingEditor', {
                url: '/backtrackingeditor/:dispatchId?debug',
                templateUrl: 'templates/backtrackingEditor.html',
                controller: 'BackTrackingEditorCtrl',
                params: {
                    dispatchId: null
                },
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_BACKTRACKING',
                        redirectTo: 'login'
                    },
                    requiresLogin: true
                }
            })

            //案件查詢
            .state('caseList', {
                url: '/caseList',
                templateUrl: 'templates/caseList.html',
                controller: 'CaseListCtrl',
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_CASELIST',
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
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_BACKTRACKING',
                        redirectTo: 'login'
                    },
                    requiresLogin: true
                }
            })
            //醫院收治能力與收治量能
            .state('hospitalCapabilityList', {
                url: '/hospitalCapabilityList',
                templateUrl: 'templates/hospitalCapabilityList.html',
                controller: 'HospitalCapabilityListCtrl',
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_HOSPITALCAPABILITYLIST',
                        redirectTo: 'login'
                    },
                    requiresLogin: true
                }

            })
            //衛生局查看醫院收治量能
            .state('hospitalCapabilityListForHealth', {
                url: '/hospitalCapabilityListForHealth',
                templateUrl: 'templates/hospitalCapabilityListForHealth.html',
                controller: 'HospitalCapabilityListForHealthCtrl',
                params: {
                    hospitalUuid: null
                },
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_HOSPITALCAPABILITYLIST',
                        redirectTo: 'login'
                    },
                    requiresLogin: true
                }

            })
            //醫院收治能力設定
            .state('hospitalAbility', {
                url: '/hospitalAbility',
                templateUrl: 'templates/hospitalAbility.html',
                controller: 'HospitalAbilityCtrl',
                params: {
                    hospitalUuid: null
                },
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_HOSPITALCAPABILITY',
                        redirectTo: 'login'
                    },
                    requiresLogin: true
                }

            })
            //醫院收治量能設定
            .state('hospitalChiefComplaint', {
                url: '/hospitalChiefComplaint',
                templateUrl: 'templates/hospitalChiefComplaint.html',
                controller: 'HospitalChiefComplaintCtrl',
                params: {
                    hospitalUuid: null
                },
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_HOSPITALCAPABILITY',
                        redirectTo: 'login'
                    },
                    requiresLogin: true
                }

            })
            .state('dispatch', {
                url: '/dispatch',
                templateUrl: 'templates/dispatch.html',
                controller: 'DispatchCtrl',
                data: {
                    permissions: {
                        only: 'HOSPITAL_PAGE_DISPATCH',
                        redirectTo: 'login'
                    },
                    requiresLogin: true
                }

            })

        // if none of the above states are matched, use this as the fallback
        // $urlRouterProvider.otherwise('/resourceManagement');
        $urlRouterProvider.otherwise(function($injector) {
            // var $state = $injector.get("$state");
            // $state.go('caseList');
            var $state = $injector.get("$state");
            var AuthService = $injector.get("AuthService");
            var targetState = AuthService.getDefaultState()
            console.log('targetState=', targetState)
            $state.go(targetState);
        });
        // $urlRouterProvider.when('/OpManagement', '/OpManagement/overviewOperatingRoom')





    })
    .run(function($rootScope, $state, AuthService, PermPermissionStore, PermRoleStore,
        authManager, $window, $document, formlyConfig, $parse) {

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

        function permissionfunc(permissionName, transitionProperties) {
            return AuthService.checkPerm(permissionName);
        }
        // __PERMISSION_MAP__ 來自 www/js/permissionlist.js
        for (var roleName in __PERMISSION_MAP__) {
            var permissionList = __PERMISSION_MAP__[roleName];
            for (var idx in permissionList) {
                var perm = permissionList[idx];
                PermPermissionStore.definePermission(perm, permissionfunc);
            }
            console.log('roleName=',roleName);
            PermRoleStore.defineRole(roleName, permissionList)
        }

        /****************** PERMISSION + JWT ******************/

        authManager.redirectWhenUnauthenticated();
        authManager.checkAuthOnRefresh();

        $rootScope.$on('tokenHasExpired', function() {
            console.log('tokenHasExpired');
            AuthService.logout();
        });

        $rootScope.$on('$stateChangePermissionStart', function(event, toState, toParams, options) {
            console.log('$stateChangePermissionStart to:', toState);
        });
        $rootScope.$on('$stateChangePermissionAccepted', function(event, toState, toParams, options) {
            console.log('$stateChangePermissionAccepted to:', toState);
        });
        $rootScope.$on('$stateChangePermissionDenied', function(event, toState, toParams, options) {
            console.log('$stateChangePermissionDenied to:', toState);
            alert('沒有對應的權限進到此畫面:'+toState.name);
        });

        $rootScope.$on('$stateChangeStart',
            function(event, toState, toParams, fromState, fromParams, options) {
                console.log('$stateChangeStart to', toState);
            })

        /****************** PERMISSION + JWT ******************/


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

.directive('ngEnter', function() {
        return function(scope, element, attrs) {
            element.bind("keydown keypress", function(event) {
                if (event.which === 13) {
                    scope.$apply(function() {
                        scope.$eval(attrs.ngEnter);
                    });
                    event.preventDefault();
                }
            });
        };
    })
    .directive('webBlank', function() {
        return {
            restrict: 'A',
            link: function(scop, element, attrs) {
                var href = element[0].href;
                if (href) {
                    element.attr('target', '_blank')
                }
            }
        }
    })
    .directive('authUser', function(AuthService) {
        return {
            restrict: 'A',
            link: function(scop, element, attrs) {
                var userData = AuthService.getCurrentUser();
                var name = userData ? userData['name'] : '';
                var displayLabel = name;

                element.text(displayLabel);
            }
        }
    })
// 顯示回溯資料
    .directive('formAnswerRecord', function(){
        function getAnswer(questionTypeId, answerRecord){
            var output = '';
            switch(questionTypeId){
                case 1://'DateTime'
                    output = _.isNil(answerRecord.freeTypingValue) ? '' : moment(answerRecord.freeTypingValue).format('YYYY/MM/DD HH:mm');
                break;
                case 6://'Date'
                    output = _.isNil(answerRecord.freeTypingValue) ? '' : moment(answerRecord.freeTypingValue).format('YYYY/MM/DD');
                break;
                case 4://'Text'
                case 3://'Int'
                    output = answerRecord.freeTypingValue;
                break;
                case 2://'Radio'
                case 5://'Checkbox'
                case 7://'Select'
                    output = answerRecord.FormAnswer.displayLabel;
                break;
                default:
                    output = answerRecord.FormAnswer.displayLabel;
                break;
            }

            return output;
        }

      return {
        restrict: 'A',
        scope:{
          record: '='
        },
        link: function(scope, element, attrs) {
          scope.$watch('record', function(newValue, oldValue) {
            if(!_.isNil(newValue)){
                var output = [];
                var record = newValue;
                var answerRecords = record.FormAnswerRecords;
                for(var idx in answerRecords){
                    var answerRecord = answerRecords[idx];
                    output.push(getAnswer(record.FormQuestion.FormQuestionTypeId, answerRecord));
                }

                element.text(output.join(','));
            }
          });
        }
      }

    })
// 顯示EPCR 或 MER 的評估處置
    .directive('answerRecord', function(){
        function getAnswer(questionTypeId, pcrAnswerRecord){
            var output = '';
            switch(questionTypeId){
                case 1://'DateTime':
                    output = _.isNil(pcrAnswerRecord.freeTypingValue) ? '' : moment(pcrAnswerRecord.freeTypingValue).format('YYYY/MM/DD HH:mm:ss');
                break;
                case 4://'Text':
                case 3://'Int':
                    output = pcrAnswerRecord.freeTypingValue;
                break;
                case 2://'Select':
                case 5://'Checkbox':
                    output = pcrAnswerRecord.PcrAnswer.displayLabel;
                break;
                default:
                    output = pcrAnswerRecord.PcrAnswer.displayLabel;
                break;
            }

            return output;
        }

      return {
        restrict: 'A',
        scope:{
          pcrRecord: '='
        },
        link: function(scope, element, attrs) {
          scope.$watch('pcrRecord', function(newValue, oldValue) {
            if(!_.isNil(newValue)){
                var output = [];
                var pcrRecord = newValue;
                var PcrAnswerRecords = pcrRecord.PcrAnswerRecords;
                for(var idx in PcrAnswerRecords){
                    var pcrAnswerRecord = PcrAnswerRecords[idx];
                    output.push(getAnswer(pcrRecord.PcrQuestion.PcrQuestionTypeId, pcrAnswerRecord));
                }

                element.text(output.join(','));
            }
          });
        }
      }
    })
    .directive('pcrAge', function(){

      return {
        restrict: 'A',
        scope:{
          age: '='
        },
        link: function(scope, element, attrs) {
          scope.$watch('age', function(newValue, oldValue) {
            if(!_.isNil(newValue)){
                var output = "";
                if(newValue==0){
                    output = '新生兒(0歲)'
                }else if(newValue>12){
                    output = Math.floor(newValue / 12) + '歲'
                }else{
                    output = newValue+'個月'
                }
                element.text(output);
            }
          });
        }
      }
    })
    .directive('vitalSign', function($http){
        var publicConfig = null;

        function getPublicConfig(){
            return $http.get('/config')
            .then(function(response){
                return response.data;
            })
        }

        function getMeasureStatuses(){
            var serverUrl = publicConfig.EPCRServer;
            return $http.get(serverUrl+'/MeasureStatuses')
            .then(function(response){
                return _.keyBy(response.data, 'id');
            })
        }

        function getAwarenesses(){
            var serverUrl = publicConfig.EPCRServer;
            return $http.get(serverUrl+'/Awarenesses')
            .then(function(response){
                return _.keyBy(response.data, 'code');
            })
        }

        function getContants(){
            return getPublicConfig()
            .then(function(result){
                publicConfig = result;
                return getMeasureStatuses()
            })
            .then(function(measureStatusList){
                return getAwarenesses()
                .then(function(awarenessesList){
                    return  {
                        measureStatusList: measureStatusList,
                        awarenessesList: awarenessesList
                    }
                });
            })
        }

        var contantPromise = getContants();

        function getAnswer(VitalSignTypeId, value, MeasureStatusId){
            return contantPromise
            .then(function(constants){

                var output = '';
                if(MeasureStatusId==1){
                    switch(VitalSignTypeId){
                        case 1:
                            output = constants.awarenessesList[value].name;
                        break;
                        case 2:
                        case 3:
                        case 4:
                        case 5:
                        case 6:
                        case 7:
                        case 11:
                        case 12:
                            output = value;
                        break;
                        case 8:
                            output = 'E'+value;
                        break;
                        case 9:
                            output = 'V'+value;
                        break;
                        case 10:
                            output = 'M'+value;
                        break;
                    }

                }else{
                    output = constants.measureStatusList[MeasureStatusId].name
                }

                return output;
            })
        }

      return {
        restrict: 'A',
        scope:{
          data: '=',
        },
        link: function(scope, element, attrs) {
          scope.$watch('data', function(newValue, oldValue) {
            if(!_.isNil(newValue)){
                var vitalSign = newValue;
                getAnswer(vitalSign.VitalSignTypeId, vitalSign.value, vitalSign.MeasureStatusId)
                .then(function(output){
                    element.text(output);
                });
            }
          });
        }
      }
    })
    .directive('imgOrientation', function(){
    return {
      restrict: 'A',
      link: function(scope, element/*, attrs*/) {
        function setTransform(transform) {
          element.css('-ms-transform', transform);
          element.css('-webkit-transform', transform);
          element.css('-moz-transform', transform);
          element.css('transform', transform);
        }

        var parent = element.parent();
        $(element).bind('load', function() {
          EXIF.getData(element[0], function() {
            var orientation = EXIF.getTag(element[0], 'Orientation');
            var height = element.height();
            var width = element.width();
            if (orientation && orientation !== 1) {
              switch (orientation) {
                case 2:
                  setTransform('rotateY(180deg)');
                  break;
                case 3:
                  setTransform('rotate(180deg)');
                  break;
                case 4:
                  setTransform('rotateX(180deg)');
                  break;
                case 5:
                  setTransform('rotateZ(90deg) rotateX(180deg)');
                  if (width > height) {
                    parent.css('height', width + 'px');
                    element.css('margin-top', ((width -height) / 2) + 'px');
                  }
                  break;
                case 6:
                  setTransform('rotate(90deg)');
                  if (width > height) {
                    parent.css('height', width + 'px');
                    element.css('margin-top', ((width -height) / 2) + 'px');
                  }
                  break;
                case 7:
                  setTransform('rotateZ(90deg) rotateY(180deg)');
                  if (width > height) {
                    parent.css('height', width + 'px');
                    element.css('margin-top', ((width -height) / 2) + 'px');
                  }
                  break;
                case 8:
                  setTransform('rotate(-90deg)');
                  if (width > height) {
                    parent.css('height', width + 'px');
                    element.css('margin-top', ((width -height) / 2) + 'px');
                  }
                  break;
              }
            }
          });
        });
      }
    };
  })

function camelize(string) {
    string = string.replace(/[\-_\s]+(.)?/g, function(match, chr) {
        return chr ? chr.toUpperCase() : '';
    });
    // Ensure 1st char is always lowercase
    return string.replace(/^([A-Z])/, function(match, chr) {
        return chr ? chr.toLowerCase() : '';
    });
}
