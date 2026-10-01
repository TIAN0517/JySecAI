SERVICES.factory('AuthService', function(jwtHelper, $http, $state) {
  var LOCALSTORAGE_KEY = AUTH_LOCALSTORAGE_KEY;
  var DEFAULT_LOGIN_STATE = 'login';
  var LOCALSTORAGE_REFRESH_KEY = AUTH_REFRESH_KEY;

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
    console.log('checkPerm:', target);
    var tokenPayload = getTokenPayload();
    if (tokenPayload) {
      if (tokenPayload.permissions && tokenPayload.permissions.indexOf(target) != -1) {
        return true;
      }
    }
    return false;
  }

  function login(credentials) {
    return $http.get('/config')
    .then(function(response){
      var config = response.data;
      var authServer = config.authServer;
      // return $http.get(authServer+'/login', {
      //     params: {
      //       username: credentials.username,
      //       password: credentials.password
      //     },
      //     paramSerializer: '$httpParamSerializerJQLike'
      //   })
      return $http.post(authServer+'/login', {
        username: credentials.username,
        password: credentials.password,
        captcha: credentials.captcha
      },{ withCredentials: true })
    })
    .then(function(response) {
      var token = response.data.token;
      var refreshToken = response.data.refreshToken;
      localStorage.setItem(LOCALSTORAGE_KEY, token);
      localStorage.setItem(LOCALSTORAGE_REFRESH_KEY, refreshToken);
      var redirectTo = getDefaultState();
      $state.go(redirectTo);
    })
  }


  function logout() {
    localStorage.removeItem(LOCALSTORAGE_KEY);
    localStorage.removeItem(LOCALSTORAGE_REFRESH_KEY);
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
    var targetState = 'monitor';
    return targetState;
  }


  function getDefaultState(){
    var payload = getTokenPayload();
    // var targetState = 'resourceManagement';
    if(payload && payload.user && payload.user.role){
      return defaultState(payload.user.role);
    }else{
      return defaultState(null);
    }
  }

  return {
    checkPerm: checkPerm,
    login: login,
    logout: logout,
    getCurrentUser: getCurrentUser,
    getAuthHeader: getAuthHeader,
    getToken: getToken,
    getDefaultState: getDefaultState
  }
})
