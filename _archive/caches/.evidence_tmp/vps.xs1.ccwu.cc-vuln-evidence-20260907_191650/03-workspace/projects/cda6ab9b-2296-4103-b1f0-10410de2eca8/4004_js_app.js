var app = angular.module('AuthServer', ['controllers',
  'services', 'ui.router', 'mgcrea.ngStrap', 'ngAnimate',
  'LocalStorageModule', 'cgBusy', 'ngTable','dndLists',
/****************** PERMISSION + JWT ******************/
  'angular-jwt','permission', 'permission.ui',
/****************** PERMISSION + JWT ******************/
'monospaced.qrcode'
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
    // unauthenticatedRedirector: ['$state', function($state) {
    //     $state.go('login');
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
  .state('permission', {
    url: '/permission',
    templateUrl: 'templates/permission.html',
    controller: 'PermissionCtrl',
    data:{
      permissions: {
        only: 'AUTH_PERM',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('role', {
    url: '/role',
    templateUrl: 'templates/role.html',
    controller: 'RoleCtrl',
    data:{
      permissions: {
        only: 'AUTH_ROLE',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('user', {
    url: '/user',
    templateUrl: 'templates/user.html',
    controller: 'UserCtrl',
    data:{
      permissions: {
        only: 'AUTH_USER',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })
  .state('changepassword', {
    url: '/changepassword',
    templateUrl: 'templates/changepassword.html',
    controller: 'ChangePasswordCtrl',
    data:{
      requiresLogin: false
    }
  })
  .state('login2fa', {
    url: '/login2fa',
    templateUrl: 'templates/login2fa.html',
    controller: 'Login2FACtrl',
    data:{
      permissions: {
        only: 'AUTH_2FA',
        redirectTo: 'login'
      },
      requiresLogin: true
    }
  })

  // if none of the above states are matched, use this as the fallback
  $urlRouterProvider.otherwise( function($injector) {
    var $state = $injector.get("$state");
    $state.go('user');

  });
  // $urlRouterProvider.when('/OpManagement', '/OpManagement/overviewOperatingRoom')

})
.run(function($rootScope, $state, AuthService, PermPermissionStore, PermRoleStore,
  /*authManager,*/ $window, $document,jwtOptions,
   $injector, jwtHelper, $timeout, $interval,$document, PUBLIC_CONFIG) {

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
  // var PERMISSIONS = [
  //   "AUTH_ROLE",
  //   "AUTH_PERM",
  //   "AUTH_USER",
  //   "AUTH_USER_ALL"
  // ]
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
  //     // AuthService.logout();
  //     AuthService.clearToken()
  // });


  $rootScope.$on('$stateChangePermissionStart', function(event, toState, toParams, options) {
      console.log('$stateChangePermissionStart to:', toState.name);
  });
  $rootScope.$on('$stateChangePermissionAccepted', function(event, toState, toParams, options) {
      console.log('$stateChangePermissionAccepted to:', toState.name );
  });
  $rootScope.$on('$stateChangePermissionDenied', function(event, toState, toParams, options) {
      console.log('$stateChangePermissionDenied to:', toState.name);
      alert('沒有對應的權限進到此畫面:'+toState.name);
  });
/* 當state 轉移時，檢查token是否有效
   若無效就試著refresh
   refresh成功的話，就重新前往原本要去的state */
  $rootScope.$on('$stateChangeStart',
  function(event, toState, toParams, fromState, fromParams, options){
    console.log('$stateChangeStart to', toState);
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
        console.log(err);
        AuthService.logout();
      }
    }
  }

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

.directive('authUser', function(AuthService){
  return {
    restrict: 'A',
    link: function(scop, element, attrs) {
      var userData = AuthService.getCurrentUser();
      var name = userData ? userData['name']: '';
      var displayLabel = name;

      element.text(displayLabel);
    }
  }
})

.directive(
    "checkNotIdle",
    function( $document, $parse ){
        // I connect the Angular context to the DOM events.
        var linkFunction = function( $scope, $element, $attributes ){
            // Get the expression we want to evaluate on the
            // scope when the document is clicked.
            var scopeExpression = $attributes.checkNotIdle;
            // Compile the scope expression so that we can
            // explicitly invoke it with a map of local
            // variables. We need this to pass-through the
            // click event.
            //
            // NOTE: I ** think ** this is similar to
            // JavaScript's apply() method, except using a
            // set of named variables instead of an array.
            var invoker = $parse( scopeExpression );
            // Bind to the document click event.
            $document.on(
                "click keyup scroll",
                function( event ){
                    // When the click event is fired, we need
                    // to invoke the AngularJS context again.
                    // As such, let's use the $apply() to make
                    // sure the $digest() method is called
                    // behind the scenes.
                    $scope.$apply(
                        function(){
                            // Invoke the handler on the scope,
                            // mapping the jQuery event to the
                            // $event object.
                            invoker(
                                $scope,
                                {
                                    $event: event
                                }
                            );
                        }
                    );
                }
            );
            // $document.on("touchend", function(event){
            //   $scope.$apply(function(){
            //     invoker($scope, {event: event})
            //   })
            // });
            // $document.on("keyup", function(event){
            //   $scope.$apply(function(){
            //     invoker($scope, {event: event})
            //   })
            // });

            // TODO: Listen for "$destroy" event to remove
            // the event binding when the parent controller
            // is removed from the rendered document.
        };
        // Return the linking function.
        return( linkFunction );
    }
)
.directive('idleTimerCountDown', function($rootScope){
  return {
    restrict: 'A',
    link: function(scop, element, attrs) {
      var unregister = $rootScope.$on('idleTimer.countDown', function(event, arg){
        // console.log('idleTimerCountDown:', arg)
        element.text(arg);
      })
      scop.$on('$destroy', function(){
        unregister();
      })

    }
  }
})
;