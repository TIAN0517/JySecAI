CONTROLLERS.controller('AmbulanceCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices) {

    var searchParams = { disabled: false };

    var addInit = function() {
        $scope.add = {};
    }

    var addModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/ambulanceAdd.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
        show: false,
        onHide: refreshList
    });

    var editModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/ambulanceEdit.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
        show: false,
        onHide: refreshList
    });

    var deleteModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/ambulanceDelete.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
        show: false,
        onHide: refreshList
    });

    $scope.showAddModal = function() {
        addInit();
        addModal.$promise.then(addModal.show);
    }

    $scope.showEditModal = function(index) {
        $scope.edit = responseList[index];
        if (!_.isEmpty($scope.edit.Devices)) {
            $scope.carDeviceParams = new NgTableParams({}, { dataset: $scope.edit.Devices });
        } else {
            $scope.carDeviceParams = new NgTableParams({}, {});
        }
        $scope.newDeviceParams = deviceTableInit();
        editModal.$promise.then(editModal.show);
    }

    $scope.showDeleteModal = function(index) {
        $scope.delete = responseList[index];
        console.log("$scope.delete", $scope.delete)
        deleteModal.$promise.then(deleteModal.show);
    }

    $scope.clear = function() {
        $scope.search = {};
    }

    $scope.searchCar = function(search) {
        searchParams = { disabled: false };
        for (var key in search) {
            if (search[key] != '') {
                searchParams[key] = search[key];
                if (key == 'code') {
                    searchParams[key] = { $like: searchParams[key] + '%' }
                } else if (key == 'licenseNo') {
                    searchParams[key] = { $like: searchParams[key] + '%' }
                } else if (key == 'BranchId') {
                    searchParams[key] = searchParams[key];
                } else if (key == 'includeDisabled') {
                    if (searchParams[key]) delete searchParams['disabled'];
                }
            }
        }
        console.log("searchParams", searchParams);
        $scope.tableParams = tableInit();
    }

    $scope.addTabs = [{
        "title": "車輛資訊",
        "template": "templates/tp/ambulance/carInfoAdd.html"
    }];

    $scope.editTabs = [{
        "title": "車輛資訊",
        "template": "templates/tp/ambulance/carInfoEdit.html"
    }, {
        "title": "目前裝置",
        "template": "templates/tp/ambulance/carDevice.html"
    }, {
        "title": "新增裝置",
        "template": "templates/tp/ambulance/newDevice.html"
    }];

    function dataInit() {
        return $http.get('/Branches', {
                params: { disabled: 0 },
                paramSerializer: '$httpParamSerializerJQLike'
            })
            .then(function(response) {
                //分隊清單
                $scope.showBranches = _.keyBy(response.data, 'id')
                $scope.addBranches = _.keyBy(response.data, 'id')
                $scope.editBranches = _.keyBy(response.data, 'id')
            })
    }

    dataInit();


    $scope.toAdd = function(formCheck) {
        console.log("formCheck", formCheck);
        if (formCheck.$valid) {
            var deferred = $q.defer();
            $scope.myPromise = deferred.promise;
            //TODO modifyManId 須取得當前使用者是誰
            console.log($scope.add);
            $http.post('/ambulances', $scope.add)
                .then(function(response) {
                    deferred.resolve();
                    console.log('Add success!')
                    addInit();
                    addModal.$promise.then(addModal.hide);
                })
                .catch(function(err) {
                    deferred.resolve();
                    console.log('Add fails =', err)
                    if (!_.isEmpty(err.data.errors)) {
                        EPCRServices.failAlertToModal('錯誤！', err.data.errors[0], null);
                    } else {
                        EPCRServices.failAlertToModal('錯誤！', '新增失敗！', null);
                    } // if
                    addModal.$promise.then(addModal.hide)
                })
        } else {
            $scope.error = '有欄位未填寫！'
        }
    }

    $scope.toEdit = function(formCheck) {
        if (formCheck.$valid) {
            var deferred = $q.defer();
            $scope.myPromise = deferred.promise;

            if ($scope.edit.disabled && $scope.edit.enable) $scope.edit.disabled = false;

            delete $scope.edit['Branch'];
            $http.put('/ambulances/' + $scope.edit.id, $scope.edit)
                .then(function() {
                    deferred.resolve();
                    editModal.$promise.then(editModal.hide);
                    console.log('Update success!')
                })
                .catch(function(err) {
                    deferred.resolve();
                    editModal.$promise.then(editModal.hide);
                    console.log('Update Fail!', err);

                    if (!_.isEmpty(err.data.errors)) {
                        EPCRServices.failAlertToModal('錯誤！', err.data.errors[0], null);
                    } else {
                        EPCRServices.failAlertToModal('錯誤！', '修改失敗(編號重複或暫時無法取得連線)！', null);
                    }
                })
        } else {
            $scope.error = '有欄位未填寫';
        }
    }

    $scope.toDelete = function() {
        var deferred = $q.defer();
        $scope.myPromise = deferred.promise;
        $http.put('/ambulances/' + $scope.delete.id, { disabled: 1 ,BranchId:'NULL'})
            .then(function() {
                deferred.resolve();
                deleteModal.$promise.then(deleteModal.hide);
                console.log('Delete success!')
            })
            .catch(function(err) {
                console.error(err);
                deferred.resolve();
                deleteModal.$promise.then(deleteModal.hide)
                    .then(function() {
                        if (!_.isEmpty(err.data) && !_.isEmpty(err.data.errors)) {
                            EPCRServices.failAlertToModal('錯誤！', err.data.errors[0], null);
                        } else {
                            EPCRServices.failAlertToModal('錯誤！', '刪除失敗', null);
                        }
                    })
            })
    }

    var selectedDeviceItem = function() {
        var chain = $q.when();
        for (var key in $scope.checkboxes.items) {
            if ($scope.checkboxes.items[key]) {
                chain = chain.then(function(id) {
                    console.log("id", id, "$scope.edit.id", $scope.edit.id)
                    return $http.put('/Devices/' + id, { AmbulanceId: $scope.edit.id })
                }.bind(null, key))
            }
        }
        return chain;
    }

    $scope.toAddDevice = function() {
        console.log("@@", $scope.checkboxes.items)
        var deferred = $q.defer();
        $scope.myPromise = deferred.promise;
        selectedDeviceItem()
            .then(function(response) {
                console.log(response.data);
                deferred.resolve();
                editModal.$promise.then(editModal.hide);
            })
            .catch(function(err) {
                deferred.resolve();
                console.log('Add fails =', err)
                if (!_.isEmpty(err.data.errors)) {
                    EPCRServices.failAlertToModal('錯誤！', err.data.errors[0], null);
                } else {
                    EPCRServices.failAlertToModal('錯誤!', '新增失敗！', null);
                } // if
                editModal.$promise.then(editModal.hide)
            })
    }

    function refreshList() {
        $scope.checkboxes = {
            checked: false,
            items: {}
        }
        $scope.tableParams = tableInit();
    }

    refreshList();

    var defaultSorting = {};
    var responseList = [];
    var deviceList = [];

    function tableInit() {
        return new NgTableParams({
            page: 1, // show first page
            count: 20, // count per page,
            sorting: defaultSorting
        }, {
            counts: [20, 40, 60, 100],
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
                // sortString = params.sorting();
                for (var key in params.sorting()) {
                    if (params.sorting()[key] == 'desc') {
                        sortString = '-' + key;
                    } else {
                        sortString = key;
                    }
                }

                var query = {
                    sort: sortString,
                    offset: skip,
                    count: limit,
                    time: new Date().getTime()
                }
                $scope.SEQ = skip;
                if (!_.isEmpty(searchParams)) {
                    for (var key in searchParams) {
                        query[key] = searchParams[key];
                    }
                }

                return $http.get('/ambulances', {
                        params: query,
                        // paramSerializer: '$httpParamSerializerJQLike'
                        // paramSerializer: '$httpParamSerializer'
                    })
                    .then(function(response) {
                        var range = contentRange.parse(response.headers('Content-Range'));
                        var count = range.length;
                        params.total(count);
                        responseList = response.data;
                        deferred.resolve()
                        return responseList;
                    })
                    .catch(function(err) {
                        deferred.resolve();
                        console.log('tableInit err =', err)
                    })

            }
        })
    }



    // watch for check all checkbox
    $scope.$watch(function() {
        return $scope.checkboxes.checked;
    }, function(value) {
        angular.forEach(deviceList, function(item) {
            $scope.checkboxes.items[item.id] = value;
        });
    });
    // watch for data checkboxes
    $scope.$watch(function() {
        return $scope.checkboxes.items;
    }, function(values) {
        var checked = 0,
            unchecked = 0,
            total = deviceList.length;
        angular.forEach(deviceList, function(item) {
            checked += ($scope.checkboxes.items[item.id]) || 0;
            unchecked += (!$scope.checkboxes.items[item.id]) || 0;
        });
        if (total > 0 && ((unchecked == 0) || (checked == 0))) {
            console.log('checked=', checked, 'total=', total);
            $scope.checkboxes.checked = (checked == total);
        }
        // grayed checkbox
        angular.element($element[0].getElementsByClassName("select-all")).prop("indeterminate", (checked != 0 && unchecked != 0));
    }, true);


    function deviceTableInit() {
        return new NgTableParams({
            page: 1, // show first page
            count: 20, // count per page,
            sorting: defaultSorting
        }, {
            counts: [20, 40, 60, 100],
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
                //     if (params.sorting()[key] == 'desc') {
                //         sortString = '-' + key;
                //     } else {
                //         sortString = key;
                //     }
                // }

                var query = {
                    AmbulanceId: 'null',
                    sort: sortString,
                    offset: skip,
                    count: limit,
                    time: new Date().getTime()
                }
                return $http.get('/Devices', {
                        params: query,
                        paramSerializer: '$httpParamSerializerJQLike'
                    })
                    .then(function(response) {
                        var range = contentRange.parse(response.headers('Content-Range'));
                        var count = range.length;
                        params.total(count);
                        deviceList = response.data;
                        deferred.resolve()
                        return deviceList;
                    })
                    .catch(function(err) {
                        deferred.resolve();
                        console.log('tableInit err =', err)
                    })

            }
        })
    }

});
