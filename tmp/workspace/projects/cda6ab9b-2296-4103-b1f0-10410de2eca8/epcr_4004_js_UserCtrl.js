CONTROLLERS.controller('UserCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, AlertServices, AuthService) {

    var defaultSorting = {};
    var responseList = []

    var defaultParams = {
        disabled: false
    };
    var customParams = angular.copy(defaultParams); // 前端輸入的查詢條件放這

    $scope.passwordInvalid = false;
    $scope.accountStatusList = [{value: false, name: '有效'},{value: true, name: '已停用'}]
    $scope.currentAccount = AuthService.getCurrentUser().account;

    function tableInit() {
        return new NgTableParams({
            page: 1, // show first page
            count: 10, // count per page,
            sorting: defaultSorting
        }, {
            filterDelay: 300,
            getData: function(params) {
                var deferred = $q.defer();
                $scope.anyPageBusy = deferred.promise;
                var url = params.url();
                var limit = url.count,
                    skip = url.count * (url.page - 1);
                var sortString;
                // 如果使用 epilogue 免費 api sort需要做調整
                // 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
                sortString = params.sorting();
                // for (var key in params.sorting()) {
                // 	if (params.sorting()[key] == 'desc') {
                // 		sortString = '-' + key;
                // 	} else {
                // 		sortString = key;
                // 	}
                // }

                // ------------------------------------------------------------------------
                var conditions = {
                    sort: sortString,
                    offset: skip,
                    count: limit,
                    time: new Date().getTime()
                };

                if (!_.isEmpty(customParams)) {
                    for (var key in customParams)
                        conditions[key] = customParams[key];
                } // if
                // ------------------------------------------------------------------------

                // console.log(conditions);
                return $http.get('/Users', {
                        params: conditions,
                        paramSerializer: '$httpParamSerializerJQLike'
                    })
                    .then(function(response) {
                        // console.log(response);
                        var range = contentRange.parse(response.headers('Content-Range'));
                        var count = range.length;
                        params.total(count);

                        deferred.resolve()
                        responseList = response.data;
                        // console.log(response.data);
                        return response.data
                    })
                    .catch(function(err) {
                        deferred.resolve();
                        console.log('tableInit err =', err)
                    })
            }
        })
    }


    // ===============================================================================================

    $scope.Init = function() {
        // 角色名稱
        $http.get('/Roles', {
                paramSerializer: '$httpParamSerializerJQLike'
            })
            .then(function(response) {
                $scope.ddlRoles = response.data;
            })
            .catch(function(err) {
                console.log('Init err =', err)
            });

        // 預設搜尋
        clear();
        // $scope.tableParams = tableInit();
    };

    $scope.Init();

    // ===============================================================================================

    $scope.searchUser = function(searchParams) {
        if (!_.isNil(searchParams)) {
            customParams = angular.copy(defaultParams);
            for (var key in searchParams) {
                if (searchParams[key] != '' && !_.isNil(searchParams[key]))
                    customParams[key] = searchParams[key];
            } // for
        } // if

        $scope.tableParams = tableInit();
    };

    // -----------------------------------------------------------------------------------------------

    $scope.clear = clear;

    function clear(){
        $scope.search = {
            disabled: false
        };
        $scope.ddlZipcodes = {};
        customParams = angular.copy(defaultParams);
        $scope.tableParams = tableInit();
    }

    // ===============================================================================================

    var AddModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/userAdd.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static',
        show: false
    });

    // -----------------------------------------------------------------------------------------------
    // 顯示新增視窗
    $scope.showAddModal = function() {
        $scope.add = {
            ddlRoles: $scope.ddlRoles,
            isLocal: true, // default value,
            applyPasswordRules: true
        };
        AddModal.$promise.then(AddModal.show)
    };

    // -----------------------------------------------------------------------------------------
    // 新增一筆資料
    $scope.toAdd = function(valid, add) {
        // console.log('Add', add);
        var data = {};
        if (_.isNil(add.RoleId) || add.RoleId == '') return AlertServices.failAlertToModal('錯誤!', '請選擇角色', null);
        else data['RoleId'] = add.RoleId;

        if (_.isNil(add.name) || add.name == '') return AlertServices.failAlertToModal('錯誤!', '請輸入USER名稱', null)
        else data['name'] = add.name;

        if (!_.isNil(add.account) && add.account != '') data['account'] = add.account;
        if (!_.isNil(add.password) && add.password != '') data['password'] = add.password;
        if (!_.isNil(add.passwordConfirmation) && add.passwordConfirmation != '') data['passwordConfirmation'] = add.passwordConfirmation;
        if (!_.isNil(add.extAccount) && add.extAccount != '') data['extAccount'] = add.extAccount;
        if (add.isLocal) {
            data['isLocal'] = add.isLocal
        } else {
            data['isLocal'] = false
        }
        data['customData'] = add.customData;

        // console.log('data', data);
        $http.post('/Users', data)
            .then(function() {
                $scope.tableParams.reload();
            })
            .then(function() {
                AddModal.$promise.then(AddModal.hide);
            })
            .catch(function(err) {
                console.log('toAdd err =', err);
                AlertServices.failAlertToModal('錯誤!', '存檔失敗!', null);
            });
    };

    // ===============================================================================================

    var EditModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/userEdit.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static',
        show: false
    });

    // -----------------------------------------------------------------------------------------------

    $scope.showEditModal = function(idx) {
        var User;
        console.log('responseList', responseList[idx]['id'])
        $http.get('/Users/' + responseList[idx]['id'])
            .then(function(response) {
                var theUser = response.data;
                if(theUser.customData && typeof(theUser.customData)=='object'){
                    theUser.customData = JSON.stringify(theUser.customData)
                }
                // console.log('theUser',theUser.data)
                return $http.get('/Roles', {
                        paramSerializer: '$httpParamSerializerJQLike'
                    })
                    .then(function(response) {
                        $scope.roleList = response.data
                        $scope.edit = theUser;
                        console.log('@@@@theUser', theUser.data)
                        if (!_.isNil(theUser)) {
                            User = theUser.Permissions;
                            $scope.selectedUser = User;

                            var permissionsIds = []
                            angular.forEach(User, function(data) {

                                permissionsIds.push(data.id)
                            })
                            console.log('@@@@permissionsIds', permissionsIds)
                            return getPermission(permissionsIds)
                                .then(function(thePermissions) {
                                    console.log('@@@@thePermissions', thePermissions)
                                    $scope.permissionList = {
                                        selected: null,
                                        lists: {
                                            "已有權限": User,
                                            "全部權限": thePermissions
                                        }
                                    }
                                    EditModal.$promise.then(EditModal.show)
                                })
                        } else {
                            AlertServices.failAlert('錯誤！', '分隊已被刪除！', null);
                            refreshList()
                        }

                    })
            })
    }

    // ----------------------------------------------------------------------------------------------

    $scope.toEdit = function(edit) {
    	var data = edit;
        console.log('data', data);
        if(data['customData']==''){
            data['customData'] = null;
        }

        var insertData = [];
        angular.forEach($scope.selectedUser, function(data) {
            insertData.push({
                PermissionId: data.id,
                UserId: edit.id
            });
        })

        var deferred = $q.defer()
        $scope.myPromise = deferred.promise

        $http.post('/Users/setUserPermissionMap/' + edit.id, {
                insertData: insertData,
                updateUserData: data
            })
            .then(function(response) {
                $scope.tableParams.reload();
                deferred.resolve()
                EditModal.$promise.then(EditModal.hide)
            })
            .catch(function(err) {
                deferred.resolve()
                console.log('setRolePermissionMap err=', err)
                alert('錯誤:'+err.data);
            })
    };

    // ===============================================================================================

    var DelModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/userDel.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static',
        show: false
    });

    // ----------------------------------------------------------------------------------------------

    $scope.showDelModal = function(index) {
        $scope.del = {
            name: $scope.tableParams.data[index].name,
            id: $scope.tableParams.data[index].id
        };
        DelModal.$promise.then(DelModal.show);
    };

    // ----------------------------------------------------------------------------------------------

    $scope.toDel = function(del) {
        console.log(del);
        $http.put('/Users/' + del.id, {
                disabled: true
            })
            .then(function() {
                return $scope.tableParams.reload();
            })
            .then(function() {
                DelModal.$promise.then(DelModal.hide);
            })
            .catch(function(err) {
                console.log('toDel err =', err)
                AlertServices.failAlertToModal('錯誤!', '請檢查是否仍有車輛屬於此分隊!', null);
            });
    };
    //-------------------------------------------------------------------------------------------------

    var getPermission = function(permissionsIds) {
        return $http.get('/Permissions', {
                params: {
                    id: {
                        $notIn: permissionsIds
                    },
                    sort: 'name',
                    disabled: false
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
            .then(function(response) {
                return response.data
            })
    }
    //-------------------------------------------------------------------------------------------------
    function checkPassword(password, passwordConfirmation){
    	if(_.isEmpty(password) && _.isEmpty(passwordConfirmation)){
    		delete $scope.edit['password'];
    		delete $scope.edit['passwordConfirmation'];
    		$scope.passwordInvalid = false;
    	}else{
	    	$scope.passwordInvalid = (password!=passwordConfirmation);
	    }
    }
    $scope.checkPassword = checkPassword;


    /* 離開時關閉 modal */
    $scope.$on('$destroy', function(){
        AddModal.$promise.then(AddModal.hide);
        EditModal.$promise.then(EditModal.hide);
        DelModal.$promise.then(DelModal.hide);
    });

    //-------------------------------------------------------------------------------------------------
    function activateAccount(userId){
        var ret = confirm('確定要重新啟用帳號？')
        if(ret){
            return $http.put('/Users/activateAccount/'+userId)
            .then(function(response){
                AlertServices.successAlert('完成','帳號已重新啟用')
                return $scope.tableParams.reload();
            })
            .catch(function(err){
                console.log(err)
                AlertServices.failAlert('錯誤', '無法重新啟用帳號', null);
            })
        }
    }
    $scope.activateAccount = activateAccount;

    //-------------------------------------------------------------------------------------------------
    function enableAccount(userId){
        var ret = confirm('確定要恢復刪除的帳號？')
        if(ret){
            return $http.put('/Users/enableAccount/'+userId)
            .then(function(response){
                AlertServices.successAlert('完成','帳號已恢復')
                return $scope.tableParams.reload();
            })
            .catch(function(err){
                console.log(err)
                AlertServices.failAlert('錯誤', '帳號已恢復', null);
            })
        }
    }
    $scope.enableAccount = enableAccount;
    // ===============================================================================================

    var resetPasswordModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/resetPassword.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static',
        show: false
    });

    // -----------------------------------------------------------------------------------------------
    // 顯示重設密碼的modal
    $scope.showResetPasswordModal = function(user) {
        $scope.resetData = {
            id: user.id,
            name: user.name,
            account: user.account,
            newPassword: null
        };
        resetPasswordModal.$promise.then(resetPasswordModal.show)
    };

    function resetPassword(userId){
        return $http.put('/Users/resetPassword/'+userId)
        .then(function(response){
            return response.data.newPassword;
        })

    }

    $scope.resetPassword = function(userId){
        var ret = confirm('確定重設密碼?')
        if(ret){
            resetPassword(userId)
            .then(function(newPassword){
                $scope.resetData.newPassword = newPassword;
            })
            .catch(function(err){
                console.log(err);
                AlertServices.failAlertToModal('錯誤','無法重設帳號');
            })
        }
    };

    // ===============================================================================================

    var request2faModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/request2fa.html',
        controller: 'Request2faCtrl',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static',
        show: false,
        onHide: function(){
            $scope.tableParams.reload();
        }
    });

    // -----------------------------------------------------------------------------------------------
    // 顯示啟用雙因子認證的modal
    function showRequest2faModal(user){
        $scope.request2faData = {
            user: user,
            theModal: request2faModal
        }
        request2faModal.$promise.then(request2faModal.show)
    }

    function revoke2FA(userId){
        return $http.put('/Users/'+userId,{
            use2FA: false
        })
    }

    $scope.request2FA = function(user) {
        showRequest2faModal(user)
    }

    $scope.revoke2FA = function(user){
        var ret = confirm('確定取消雙因子認證？')
        if(ret){
            revoke2FA(user.id)
            .then(function(response){
                $scope.tableParams.reload();
                AlertServices.successAlert('完成','已關閉雙因子認證');
            })
            .catch(function(err){
                AlertServices.failAlert('錯誤',err.data.message);
            })
        }
    }



});