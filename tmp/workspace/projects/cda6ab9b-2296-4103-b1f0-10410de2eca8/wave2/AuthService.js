SERVICES.factory('AuthService', function(jwtHelper, $http, $state, $q, PUBLIC_CONFIG) {
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
    // console.log('checkPerm:', target);
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
      },{ withCredentials: true }) // withCredentials = true 才會送出cookie 如此才能夠使用cookie裡面的session id (用於captcha功能)
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

  function ssoLogin(sessionId) {
    return $http.get('/config')
      .then(function(response){
        var config = response.data;
        var authServer = config.authServer;
        return $http.post(authServer + '/ssoLogin', {
          sessionId: sessionId
        });
      })
      .then(function(response) {
        var token = response.data.token;
        var refreshToken = response.data.refreshToken;
        localStorage.setItem(LOCALSTORAGE_KEY, token);
        localStorage.setItem(LOCALSTORAGE_REFRESH_KEY, refreshToken);
        var redirectTo = getDefaultState();
        $state.go(redirectTo);
      });
  }

  async function logout(logoutType) {
    switch (logoutType) {
      case 15:
        await clearToken15()
        break;

      default:  
        await clearToken()
        break;
    }
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

  var roleDefaultStateMap = __ROLE_DEFAULT_STATE_MAP__;

  function defaultState(role){
    var theDefault = roleDefaultStateMap["__DEFAULT__"];
    var targetState = theDefault;
    if(role==null){
      return targetState;
    }
    var state = roleDefaultStateMap[role]
    if(state){
      targetState = state;
    }
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
      return defaultState(DEFAULT_LOGIN_STATE);
    }
  }

  function refreshToken(){
    var refreshToken = localStorage.getItem(LOCALSTORAGE_REFRESH_KEY);
    if(refreshToken){
      return $http.post(PUBLIC_CONFIG.authServer+'/refreshToken',{
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

  function clearToken(){
    return $http.post('/Activities/logoutRecord',{
              actionType: 'login/out',
              originalData: null,
              targetEntity: '登出紀錄',
              activityDescription: '登出成功'
            })
            .then(()=>{
              localStorage.removeItem(LOCALSTORAGE_KEY);
              localStorage.removeItem(LOCALSTORAGE_REFRESH_KEY);
            })
  }

  function clearToken15(){
    return $http.post('/Activities/logoutRecord',{
              actionType: 'login/out',
              originalData: null,
              targetEntity: '登出紀錄',
              activityDescription: '閒置超過15分鐘登出'
            })
            .then(()=>{
              localStorage.removeItem(LOCALSTORAGE_KEY);
              localStorage.removeItem(LOCALSTORAGE_REFRESH_KEY);
            })
  }

  function isTokenExpired(token){
    return jwtHelper.isTokenExpired(token);
  }

  return {
    checkPerm: checkPerm,
    login: login,
    ssoLogin: ssoLogin,
    logout: logout,
    getCurrentUser: getCurrentUser,
    getAuthHeader: getAuthHeader,
    getToken: getToken,
    getDefaultState: getDefaultState,
    refreshToken: refreshToken,
    clearToken: clearToken,
    isTokenExpired: isTokenExpired
  }
})
