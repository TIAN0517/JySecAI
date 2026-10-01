/* 參考 https://gist.github.com/ygotthilf/3cf3e36bfbe9881f0e4b */
app.config(authInterceptorConfig);

/* @ngInject*/
function authInterceptorConfig($httpProvider) {
  $httpProvider.interceptors.push('authInterceptor');
}

app.factory('authInterceptor', authInterceptor);

/* @ngInject */
function authInterceptor($q, $injector, $location, jwtOptions) {

  var replays = [];
  var refreshTokenPromise;

  var factory = {
    request: request,
    responseError: responseError
  };

  return factory;

  //////////

  function invokeToken(tokenGetter) {
    var token = null;
    if (Array.isArray(tokenGetter)) {
      token = $injector.invoke(tokenGetter, this, {options: null});
    } else {
      token = tokenGetter();
    }
    return token;
  }

  function tokenGetter(){
    var config = jwtOptions.getConfig();
    var token = invokeToken(config.tokenGetter);
    return token;
  }

  // Add authorization token to headers
  function request(config) {
    config.headers = config.headers || {};
    var token = tokenGetter();
    if (token) {
      config.headers.Authorization = 'Bearer ' + token;
    }

    return config;
  }

  // Intercept 401s and redirect you to login
  function responseError(response) {
    var token = $injector.get('AuthService').getToken();
    if (response.status === 401 && token!=null) {
      return checkAuthorization(response);
    }
    return $q.reject(response);

    /////////

    function checkAuthorization(res) {
      return $q(function(resolve, reject) {

        var replay = {
          success: function(){
            $injector.get('$http')(res.config).then(resolve, reject);
          },

          cancel: function(){
            reject(res);
          }
        };

        replays.push(replay);

        if (!refreshTokenPromise) {
          refreshTokenPromise = $injector.get('AuthService') // REFRESH TOKEN HERE
            .refreshToken()
            .then(clearRefreshTokenPromise)
            .then(replayRequests)
            .catch(cancelRequestsAndRedirect);
        }
      });

      ////////////

      function clearRefreshTokenPromise(auth) {
        refreshTokenPromise = null;
        return auth;
      }

      function replayRequests(auth) {
        replays.forEach(function(replay) {
          replay.success();
        });

        replays.length = 0;

        return auth;
      }

      function cancelRequestsAndRedirect() {
        refreshTokenPromise = null;
        replays.forEach(function(replay) {
          replay.cancel();
        });

        replays.length = 0;

        // 重新登入
        $injector.get('AuthService').logout();
      }
    }
  }
}
