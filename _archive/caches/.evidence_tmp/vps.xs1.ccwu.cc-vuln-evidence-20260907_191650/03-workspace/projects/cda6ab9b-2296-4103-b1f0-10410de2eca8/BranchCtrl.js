CONTROLLERS.controller('BranchCtrl', function($q, $modal, $scope, $state,
  NgTableParams, $http, $element, EPCRServices) {

  var defaultSorting = {};
  var responseList = []

  var defaultParams = {
    disabled: false
  };
  var customParams = angular.copy(defaultParams); // 前端輸入的查詢條件放這

  function tableInit() {
    return new NgTableParams({
      page: 1, // show first page
      count: 10, // count per page,
      sorting: {
        BranchGroup: 'ASC'
      }
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
        $scope.SEQ = skip;
        if (!_.isEmpty(customParams)) {
          for (var key in customParams)
            conditions[key] = customParams[key];
        } // if
        // ------------------------------------------------------------------------

        // console.log(conditions);
        return $http.get('/Branches/search', {
            params: conditions,
            paramSerializer: '$httpParamSerializerJQLike'
          })
          .then(function(response) {
            // console.log(response);
            var range = contentRange.parse(response.headers('Content-Range'));
            var count = range.length;
            params.total(count);

            deferred.resolve()
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

  // $scope.checkboxes = {
  //   checked: false,
  //   items: {}
  // }
  // // watch for check all checkbox
  // $scope.$watch(function() {
  //     return $scope.checkboxes.checked;
  // }, function(value) {
  //     angular.forEach(responseList, function(item) {
  //         $scope.checkboxes.items[item.id] = value;
  //     });
  // });
  // // watch for data checkboxes
  // $scope.$watch(function() {
  //     return $scope.checkboxes.items;
  // }, function(values) {
  //     var checked = 0,
  //         unchecked = 0,
  //         total = responseList.length;
  //     angular.forEach(responseList, function(item) {
  //         checked += ($scope.checkboxes.items[item.id]) || 0;
  //         unchecked += (!$scope.checkboxes.items[item.id]) || 0;
  //     });
  //     if (total > 0 && ((unchecked == 0) || (checked == 0))) {
  //         console.log('checked=', checked, 'total=', total);
  //         $scope.checkboxes.checked = (checked == total);
  //     }
  //     // grayed checkbox
  //     angular.element($element[0].getElementsByClassName("select-all")).prop("indeterminate", (checked != 0 && unchecked != 0));
  // }, true);

  // ===============================================================================================

  $scope.Init = function() {
    // 大隊名稱
    $http.get('/branchgroups', {
        params: {
          disabled: false
        },
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(response) {
        $scope.ddlBranchGroups = response.data;
        // 區域
        return $http.get('/districts', {
          params: {
            disabled: false
          },
          paramSerializer: '$httpParamSerializerJQLike'
        });
      })
      .then(function(response) {
        $scope.ddlDistricts = response.data;
      })
      .catch(function(err) {
        console.log('Init err =', err)
      });

    // 預設搜尋
    $scope.tableParams = tableInit();
  };

  $scope.Init();

  // ===============================================================================================

  $scope.selectedDistricts = function(districtId) {
    if (districtId == '' || _.isNil(districtId)) {
      return $scope.ddlZipcodes = [];
    } // if

    $http.get('/zipcodes', {
        params: {
          disabled: false,
          DistrictId: districtId
        },
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(response) {
        $scope.ddlZipcodes = response.data;
        // console.log(response.data, $scope.ddlZipcodes);
      })
      .catch(function(err) {
        console.log('selectedDistricts err =', err)
      });
  };

  // ===============================================================================================

  $scope.searchBranch = function(searchParams) {
    if (!_.isNil(searchParams)) {
      customParams = angular.copy(defaultParams);
      // console.log(searchParams);
      // if (!_.isNil(searchParams['includeDisabled']))
      // {
      // 	delete customParams['disabled'];
      // } // if
      for (var key in searchParams) {
        if (key == 'includeDisabled') {
          if (searchParams[key]) delete customParams['disabled'];
        } // if
        else if (searchParams[key] != '' && !_.isNil(searchParams[key])) {
          customParams[key] = searchParams[key];
        } // else if
      } // for
    } // if

    $scope.tableParams = tableInit();
  };

  // -----------------------------------------------------------------------------------------------

  $scope.clear = function() {
    $scope.search = {};
    $scope.ddlZipcodes = {};
    customParams = angular.copy(defaultParams);
    $scope.tableParams = tableInit();
  };

  // ===============================================================================================

  var AddModel = $modal({
    scope: $scope,
    templateUrl: 'templates/modal/branchAdd.html',
    animation: 'no-animation',
    placement: 'center',
    backdrop: 'static',
    show: false
  });

  // -----------------------------------------------------------------------------------------------
  // 顯示新增視窗
  $scope.showAddModal = function() {
    return $q.when()
      .then(function() {
        return $q.all([getBranchGroups(), getBranchTypes(), getDistricts()])
          .then(function(response) {
            $scope.add = {
              ddlBranchGroups: response[0],
              ddlBranchTypes: response[1],
              ddlDistricts: response[2],
              data: {}
            };
            return AddModel.$promise.then(AddModel.show)
          })
          .catch(function(err) {
            console.log('showAddModal err =', err);
            EPCRServices.failAlert('錯誤!', '取得大隊清單、分隊類型清單、行政區清單時發生錯誤', null);
          });
      })
  };

  // -----------------------------------------------------------------------------------------
  // 發生於縣市選擇時, 要帶入其所屬的鄉鎮市資料
  $scope.addSelectedDistricts = function(districtId, data) {
    if (districtId == '' || _.isNil(districtId)) {
      if (data) data.ddlZipcodes = [];
      return $q.when();
    } // if

    return getZipcodes(districtId)
      .then(function(zipcodes) {
        data.ddlZipcodes = zipcodes;
      })
      .catch(function(err) {
        console.log('addSelectedDistricts err =', err);
        EPCRServices.failAlertToModal('錯誤！', '取得行政區資訊發生錯誤', null);
      });
  };

  // -----------------------------------------------------------------------------------------
  // 新增一筆資料
  $scope.toAdd = function(valid, data) {
    return $http.post('/branches', data)
      .then(function() {
        $scope.tableParams.reload();
      })
      .then(function() {
        AddModel.$promise.then(AddModel.hide);
      })
      .catch(function(err) {
        console.log('toAdd err =', err);
        EPCRServices.failAlertToModal('錯誤!', '請檢查分隊名稱是否已存在!', null);
      });
  };

  // ===============================================================================================

  var EditModel = $modal({
    scope: $scope,
    templateUrl: 'templates/modal/branchEdit.html',
    animation: 'no-animation',
    placement: 'center',
    backdrop: 'static',
    show: false
  });

  // -----------------------------------------------------------------------------------------------

  $scope.showEditModal = function(branchId) {
    return $http.get('/Branches/search', {
        params: {
          id: branchId
        },
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(branchResult) {
        var data = _.clone(branchResult.data[0]);
        return $q.all([
            getBranchGroups(),
            getBranchTypes(),
            getDistricts(),
            getZipcodes(data.DistrictId)
          ])
          .then(function(response) {
						data.DistrictId = data.ZipCode.DistrictId;
						delete data.ZipCode;
						delete data.BranchGroup;
            $scope.edit = {
              ddlBranchGroups: response[0],
              ddlBranchTypes: response[1],
              ddlDistricts: response[2],
              ddlZipcodes: response[3],
							disabledMode: data.disabled,
              data: data
            };
            return EditModel.$promise.then(EditModel.show);
          });
      })
      .catch(function(err) {
        console.log('showEditModal err =', err)
        EPCRServices.failAlert('錯誤!', '資料錯誤!', null);
      });
  };

  // ----------------------------------------------------------------------------------------------
  // 發生於縣市選擇時, 要帶入其所屬的鄉鎮市資料
  $scope.editSelectedDistricts = function(districtId, data) {
    if (districtId == '' || _.isNil(districtId)) {
      if (data) data.ddlZipcodes = [];
      return $q.when();
    } // if

    return getZipcodes(districtId)
      .then(function(zipcodes) {
        data.ddlZipcodes = zipcodes;
      })
      .catch(function(err) {
        console.log('addSelectedDistricts err =', err);
        EPCRServices.failAlertToModal('錯誤！', '取得行政區資訊發生錯誤', null);
      });
  };

  // ----------------------------------------------------------------------------------------------

  $scope.toEdit = function(valid, data) {
    console.log('data', data);
    $http.put('/branches/' + data.id, data)
      .then(function() {
        $scope.tableParams.reload();
      })
      .then(function() {
        EditModel.$promise.then(EditModel.hide);
      })
      .catch(function(err) {
        console.log('toEdit err =', err);
        EPCRServices.failAlertToModal('錯誤!', '請檢查分隊名稱是否已存在!', null);
      });
  };

  // ===============================================================================================

  var DelModel = $modal({
    scope: $scope,
    templateUrl: 'templates/modal/branchDel.html',
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
    DelModel.$promise.then(DelModel.show);
  };

  // ----------------------------------------------------------------------------------------------

  $scope.toDel = function(del) {
    // console.log(del);
    $http.put('/branches/' + del.id, {
        disabled: true
      })
      .then(function() {
        return $scope.tableParams.reload();
      })
      .then(function() {
        DelModel.$promise.then(DelModel.hide);
      })
      .catch(function(err) {
        console.log('toDel err =', err)
        EPCRServices.failAlertToModal('錯誤!', '請檢查是否仍有車輛屬於此分隊!', null);
      });
  };

  // ===========================================================================
  // 取得大隊清單
  function getBranchGroups() {
    return $http.get('/BranchGroups', {
        params: {
          disabled: false
        },
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(response) {
        return response.data
      });
  } // getBranchGroupList()
  // 取得分隊類型清單
  function getBranchTypes() {
    return $http.get('/BranchType', {
        params: {},
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(response) {
        return response.data;
      });
  } // getBranchTypes()
  // 取得縣市清單
  function getDistricts() {
    return $http.get('/Districts', {
        params: {
          disabled: false
        },
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(response) {
        return response.data
      });
  } // getDistricts()
  // 取得鄉鎮市區清單
  function getZipcodes(districtId) {
    return $http.get('/zipcodes', {
        params: {
          disabled: false,
          DistrictId: districtId
        },
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(response) {
        return response.data;
      });
  } // getZipcodes()
});
