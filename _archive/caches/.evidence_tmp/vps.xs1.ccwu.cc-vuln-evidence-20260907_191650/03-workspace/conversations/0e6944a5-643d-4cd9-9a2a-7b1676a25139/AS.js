SERVICES.factory('AuthService', function(jwtHelper, $http, $state, $q) {
  var LOCALSTORAGE_KEY = AUTH_LOCALSTORAGE_KEY;
  var LOCALSTORAGE_REFRESH_KEY = AUTH_REFRESH_KEY;

  var DEFAULT_LOGIN_STATE = 'login';

  function getTokenPayload() {
    var expToken = localStorage.getItem(LOCALSTORAGE_KEY);
    if (expToken) {
      var tokenPayload = jwtHelper.decodeToken(expToken);
      return tokenPayload
    }
    return null;
  }

  function getToken() {
    var expToken = localStorage.getItem(LOCALSTORAGE_KEY);
    return expToken;
  }

  function getAuthHeader() {
    var expToken = localStorage.getItem(LOCALSTORAGE_KEY);
    if (expToken) {
      return {
        key: "Authorization",
        value: "Bearer " + expToken
      }
    } else {
      return null;
    }
  }

  function checkPerm(target) {
    var tokenPayload = getTokenPayload();
    if (tokenPayload) {
      if (tokenPayload.permissions && tokenPayload.permissions.indexOf(target) != -1) {
        return true;
      }
    }
    return false;
  }

  function login(credentials) {
    return $http.post('/login', {
      username: credentials.username,
      password: credentials.password,
      captcha: credentials.captcha,
      domain: 'AUTH_SERVER'
    })
      .then(function(response) {
        var ret = response.data;
        localStorage.setItem(LOCALSTORAGE_KEY, ret.token);
        if(ret.use2FA){
          // 前往雙因子認證畫面
          $state.go('login2fa');
        }else{
          localStorage.setItem(LOCALSTORAGE_REFRESH_KEY, ret.refreshToken);
          var redirectTo = getDefaultState();
          $state.go(redirectTo);
        }
      })
  }

  function login2FA(userToken){
    return $http.post('/login2FA',{
        userToken: userToken,
        domain: 'AUTH_SERVER'
    })
    .then(function(response){
      var ret = response.data;
      localStorage.setItem(LOCALSTORAGE_KEY, ret.token);
      localStorage.setItem(LOCALSTORAGE_REFRESH_KEY, ret.refreshToken);
      var redirectTo = getDefaultState();
      $state.go(redirectTo);
    });
  }


  function clearToken(){
    localStorage.removeItem(LOCALSTORAGE_KEY);
    localStorage.removeItem(LOCALSTORAGE_REFRESH_KEY);
  }


  function logout() {
    clearToken()
    console.log('GOTO DEFAULT_LOGIN_STATE:', DEFAULT_LOGIN_STATE)
    $state.go(DEFAULT_LOGIN_STATE);
  }

  function getCurrentUser() {
    var payload = getTokenPayload();
    if(payload){
      return payload.user;
    }else{
      return null;
    }
  }

  function defaultState(role){
    var targetState = 'user';
    return targetState;
  }


  function getDefaultState(){
    var token = getToken();
    if(_.isNil(token)){
      return DEFAULT_LOGIN_STATE;
    }
    if(jwtHelper.isTokenExpired(token)){
      return DEFAULT_LOGIN_STATE;
    }

    var payload = getTokenPayload();

    if(payload && payload.user && payload.user.role){
      return defaultState(payload.user.role);
    }else{
      return defaultState(null);
    }
  }

  function refreshToken(){
    var refreshToken = localStorage.getItem(LOCALSTORAGE_REFRESH_KEY);
    if(refreshToken){
      return $http.post('/refreshToken',{
        refreshToken: refreshToken
      })
      .then(function(response){
        var ret = response.data;
        localStorage.setItem(LOCALSTORAGE_KEY, ret.token);
        localStorage.setItem(LOCALSTORAGE_REFRESH_KEY, ret.refreshToken);
      })
    }else{
      return $q.reject(new Error('RefreshToken not exists.'));
    }
  }

  return {
    checkPerm: checkPerm,
    login: login,
    logout: logout,
    getCurrentUser: getCurrentUser,
    getAuthHeader: getAuthHeader,
    getToken: getToken,
    getDefaultState: getDefaultState,
    refreshToken: refreshToken,
    clearToken: clearToken,
    login2FA: login2FA
  }
})
