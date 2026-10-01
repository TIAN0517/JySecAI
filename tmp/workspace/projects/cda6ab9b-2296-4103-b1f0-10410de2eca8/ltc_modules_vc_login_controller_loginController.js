app.controller('loginController', function ($scope, $rootScope, $location, $window, $state, $http, AuthenticationService, urlSetting) {
    $scope.dataLoading = false;
    $scope.loginUser = {
        uc: null, up: null, ut: 1, fn: 1
    }

    $scope.onRegister = function () {
        $state.go('register');
    }
    $scope.onForget = function () {
        $state.go('forget');
    }


    //user name Login
    $scope.login = function (valid) {
        if (valid) {
            var data = {
                code: $scope.loginUser.uc,
                pwd: $scope.loginUser.up,
                device: 3,
                type: 0
            };

            // web api 登入
            AuthenticationService.Login(data, function (response, request) {
                if (response.res == 1) {
                    AuthenticationService.SetCredentials(response);
                    if (response.userEnable == 0) {
                        $state.go('userAccountDetail');
                    } else {
                        $state.go('home');
                    }
                } else {
                    if (response.resCode == 88) {
                        alert(response.msg);
                    } else {
                        alert("登入失敗");
                    }

                }
            });
        }
    }

    //Facebook login
    $scope.Facebooklogin = function () {
        var provider = new firebase.auth.FacebookAuthProvider();
        firebase.auth().signInWithPopup(provider).then(function (result) {
            var user = result.user;
            var userId = user.uid;
            var displayName = user.displayName;

            if (userId && displayName) {
                var data = {
                    code: userId,
                    userName: displayName,
                    pictureUrl: user.photoURL,
                    email: user.email,
                    device: 3,
                    type: 1
                }

                AuthenticationService.Login(data, function (response, request) {
                    if (response.res == 1) {
                        AuthenticationService.SetCredentials(response);
                        if (response.userEnable == 0) {
                            $state.go('userAccountDetail');
                        } else {
                            $state.go('home');
                        }
                    } else {
                        if (response.resCode == 88) {
                            alert(response.msg);
                        } else {
                            alert("失敗");
                        }

                    }
                })
            }

        }).catch(function (error) {
            var errorCode = error.code;
            var errorMessage = error.message;
        });
    }

    //Google login
    $scope.Googlelogin = function () {
        var provider = new firebase.auth.GoogleAuthProvider();
        firebase.auth().signInWithPopup(provider).then(function (result) {
            let token = result.credential.accessToken;
            let user = result.user;
            if (user) {
                var data = {
                    code: user.uid,
                    userName: user.displayName,
                    pictureUrl: user.photoURL,
                    email: user.email,
                    device: 3,
                    type: 2
                }
                AuthenticationService.Login(data, function (response, request) {
                    if (response.res == 1) {
                        AuthenticationService.SetCredentials(response);
                        if (response.userEnable == 0) {
                            $state.go('userAccountDetail');
                        } else {
                            $state.go('home');
                        }
                    } else {
                        if (response.resCode == 88) {
                            alert(response.msg);
                        } else {
                            alert("失敗");
                        }

                    }
                })

            }


        }).catch(function (error) {
            var errorCode = error.code;
            var errorMessage = error.message;
        });
    }

    //使用LineLogin
    $scope.lineLogin = function () {
        var URL = 'https://access.line.me/oauth2/v2.1/authorize?';
        URL += 'response_type=code';
        URL += '&client_id=1654066811';
        URL += '&redirect_uri=' + urlSetting.frontend +'index.html' ;
        URL += '&state=abcde';
        URL += '&scope=openid%20profile';
        window.location.href = URL;
    }

})

//Line Server login 完成後會導入 code, state 的參數,回傳會在 app.js $urlRouterProvider.otherwise 做攔截 再導到 loginHandlerController 做處理

app.controller('loginHandlerController', function ($rootScope, $scope, $window, $location, $http, $filter, $state, $modal, $stateParams, AuthenticationService, urlSetting) {
    var code = $stateParams.code;
    var state = $stateParams.state;

    var lineLogin = function (resp) {
        var userId = resp.userId;
        var displayName = resp.displayName;
        var pictureUrl = resp.pictureUrl;
        if (userId && displayName) {
            var data = {
                code: userId,
                userName: displayName,
                pictureUrl: pictureUrl,
                device: 3,
                type: 4
            }

            AuthenticationService.Login(data, function (response, request) {
                if (response.res == 1) {
                    AuthenticationService.SetCredentials(response);
                    if (response.userEnable == 0) {
                        $state.go('userAccountDetail');
                    } else {
                        $state.go('home');
                    }
                } else {
                    if (response.resCode == 88) {
                        alert(response.msg);
                    } else {
                        alert("失敗");
                    }

                }
            });
        }
    }

    if (code && state) {
        var data =
            'grant_type=authorization_code' +
            '&code=' + code +
            '&redirect_uri=' + urlSetting.frontend +'index.html'+
            '&client_id=1654066811' +
            '&client_secret=4fc7fef6843467861df653aed7327503';

        $.ajax({
            url: 'https://api.line.me/oauth2/v2.1/token',
            type: 'post',
            contentType: 'application/x-www-form-urlencoded',
            data: data,
            success: function (resp) {
                var accessToken = resp.access_token;
                if (accessToken) {
                    $.ajax({
                        url: 'https://api.line.me/v2/profile',
                        type: 'post',
                        contentType: 'application/x-www-form-urlencoded',
                        beforeSend: function (xhr) {
                            xhr.setRequestHeader("Authorization", "Bearer " + accessToken);
                        },
                        success: function (resp) {
                            lineLogin(resp);
                        },
                        error: function (jqXHR, exception) {
                            $state.go('login');
                        }
                    });
                }

            },
            error: function (jqXHR, exception) {
                $state.go('login');
            }
        });
    }

})




