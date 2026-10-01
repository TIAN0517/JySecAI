app.factory('loginService', function (baseHttp) {
    return {
        login: function (params, callback) {
            return baseHttp.service('api_app/login', params, callback);
        },
        register: function (params, callback) {
            return baseHttp.service('api_app/loginRegister', params, callback);
        },
        forgetpwd: function (params, callback) {
            return baseHttp.service('api_app/forgetpwd', params, callback);
        }
    }
})
app.factory('AuthenticationService', ['Base64', '$http', '$cookies', '$rootScope', '$timeout', '$window', 'loginService',
    function (Base64, $http, $cookieStore, $rootScope, $timeout, $window, loginService) {
        var service = {};

        //登入
        service.Login = function (loginUser, callback) {
            $timeout(function () {
                loginService.login(loginUser, function (data, status, headers, config) {
                    callback(data);
                })
            }, 1000);
        }

        //註冊
        service.Register = function (registerUser, callback) {
            $timeout(function () {
                loginService.register(registerUser, function (data, status, headers, config) {
                    callback(data);
                })
            }, 1000);
        }
        
        service.SetCredentials = function (response) {
            // var authdata = Base64.encode(response.token + ':' + response.userId);
            if (response.res == 1) {
                var currentUser = {
                    ut: response.token,
                    usi: response.userId,
                    userName : response.userName,
                    userEnable: response.userEnable,
                    cphoneNo: response.cphoneNo,
                    tphoneNo: response.tphoneNo,
                    addressCode: response.addressCode,
                    address: response.address
                }
                $rootScope.isLogin = true;
                $rootScope.currentUser = currentUser;
            }

            // $http.defaults.headers.common['Authorization'] = 'Basic' + authdata;
        }

        service.ClearCredentials = function () {
            // $http.defaults.headers.common.Authorization = 'Basic';
        }
        return service;
    }

]).factory('Base64', function () {
    var keyStr = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
    return {
        encode: function (input) {
            var output = "";
            var chr1, chr2, chr3 = "";
            var enc1, enc2, enc3, enc4 = "";
            var i = 0;

            do {
                chr1 = input.charCodeAt(i++);
                chr2 = input.charCodeAt(i++);
                chr3 = input.charCodeAt(i++);

                enc1 = chr1 >> 2;
                enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
                enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
                enc4 = chr3 & 63;

                if (isNaN(chr2)) {
                    enc3 = enc4 = 64;
                } else if (isNaN(chr3)) {
                    enc4 = 64;
                }

                output = output +
                    keyStr.charAt(enc1) +
                    keyStr.charAt(enc2) +
                    keyStr.charAt(enc3) +
                    keyStr.charAt(enc4);
                chr1 = chr2 = chr3 = "";
                enc1 = enc2 = enc3 = enc4 = "";
            } while (i < input.length);

            return output;
        },
        decode: function (input) {
            var output = "";
            var chr1, chr2, chr3 = "";
            var enc1, enc2, enc3, enc4 = "";
            var i = 0;
            var base64test = /[^A-Za-z0-9\+\/\=]/g;
            if (base64test.exec(input)) { }
            input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

            do {
                enc1 = keyStr.indexOf(input.charAt(i++));
                enc2 = keyStr.indexOf(input.charAt(i++));
                enc3 = keyStr.indexOf(input.charAt(i++));
                enc4 = keyStr.indexOf(input.charAt(i++));

                chr1 = (enc1 << 2) | (enc2 >> 4);
                chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
                chr3 = ((enc3 & 3) << 6) | enc4;

                output = output + String.fromCharCode(chr1);
                if (enc3 != 64) {
                    output = output + String.fromCharCode(chr2);
                }
                if (enc4 != 64) {
                    output = output + String.fromCharCode(chr3);
                }

                chr1 = chr2 = chr3 = "";
                enc1 = enc2 = enc3 = enc4 = "";
            } while (i < input.length);

            return output;
        }
    }

})
