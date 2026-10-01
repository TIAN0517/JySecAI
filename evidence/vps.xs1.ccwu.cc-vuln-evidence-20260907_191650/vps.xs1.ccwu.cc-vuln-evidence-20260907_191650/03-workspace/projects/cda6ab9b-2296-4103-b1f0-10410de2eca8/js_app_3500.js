var app = angular.module('MonitorServer', ['controllers',
    'services', 'ui.router', 'mgcrea.ngStrap', 'ngAnimate',
    'LocalStorageModule', 'cgBusy', 'ngTable',
    /****************** PERMISSION + JWT ******************/
    'angular-jwt', 'permission', 'permission.ui',
    /****************** PERMISSION + JWT ******************/
    'formly', 'formlyBootstrap', 'dndLists', 'mwl.calendar'
]);

app.config(function($modalProvider) {
    angular.extend($modalProvider.defaults, {
        html: true
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
            unauthenticatedRedirector: ['$state', function($state) {
                $state.go('login');
            }],
            whiteListedDomains: ['localhost','47.97.114.73','118.163.107.93', 'epcr.tpf.gov.tw','35.234.50.28']
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
            .state('monitor', {
                url: '/monitor',
                templateUrl: 'templates/monitor.html',
                controller: 'MonitorCtrl',
                data: {
                    permissions: {
                        only: 'MONITOR_ALL',
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
        authManager, $window, $document) {

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
        var PERMISSIONS = [
            "MONITOR_ALL",
        ]
        for (var idx in PERMISSIONS) {
            PermPermissionStore
                .definePermission(PERMISSIONS[idx], permissionfunc);
        }

        /****************** PERMISSION + JWT ******************/
        //TODO: Only temp settings for now. Need to apply REAL permission settings.
        PermRoleStore
            .defineRole('ADMIN', PERMISSIONS)

        authManager.redirectWhenUnauthenticated();
        authManager.checkAuthOnRefresh();

        $rootScope.$on('tokenHasExpired', function() {
            console.log('tokenHasExpired');
            AuthService.logout('login');
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
    .directive('toggleCheckbox', function() {

        /**
         * Directive
         */
        return {
            restrict: 'A',
            transclude: true,
            replace: false,
            require: 'ngModel',
            link: function($scope, $element, $attr, require) {

                var ngModel = require;

                // update model from Element
                var updateModelFromElement = function() {
                    // If modified
                    var checked = $element.prop('checked');
                    if (checked != ngModel.$viewValue) {
                        // Update ngModel
                        ngModel.$setViewValue(checked);
                        $scope.$apply();
                    }
                };

                // Update input from Model
                var updateElementFromModel = function() {
                    // Update button state to match model
                    $element.trigger('change');
                };

                // Observe: Element changes affect Model
                $element.on('change', function() {
                    updateModelFromElement();
                });

                // Observe: ngModel for changes
                $scope.$watch(function() {
                    return ngModel.$viewValue;
                }, function() {
                    updateElementFromModel();
                });

                // Initialise BootstrapToggle
                $element.bootstrapToggle();
            }
        };
    })
    .directive('ngReallyClick', [function() {
        return {
            restrict: 'A',
            link: function(scope, element, attrs) {
                element.bind('click', function() {
                    var message = attrs.ngReallyMessage;
                    if (message && confirm(message)) {
                        scope.$apply(attrs.ngReallyClick);
                    }
                });
            }
        }
    }]);
