CONTROLLERS.controller('SuppliesQueryCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices, AuthService, $window, $httpParamSerializer) {

      //預設搜尋條件
      var searchQuery = {}
      //預設搜尋條件(異動查詢)
      var searchStockChange = {}
      //
      $scope.checkboxes = {
        checked: false,
        items: {}
      }
      $scope.search = {};
      $scope.search.expiryDate = moment().add(30, 'days').toDate();
      $scope.cusIndex = 0;
      $scope.totalLength = 0

      // ================================ DATE RANGE PICKER =========================================
      $scope.sQuery = {};
      $scope.sQuery.dateTime = {
        startDate: moment().subtract(1, "days"),
        endDate: moment()
      };



      $scope.opts = {
        locale: {
          applyClass: 'btn-success',
          applyLabel: "確定",
          // fromLabel: "Od",
          // toLabel: "Do",
          cancelLabel: '取消',
          customRangeLabel: '自訂',
          daysOfWeek: ['週日', '週一', '週二', '週三', '週四', '週五', '週六'],
          firstDay: 1,
          monthNames: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月',
            '10月', '11月', '12月'
          ]
        },
        ranges: {
          '一天內': [moment().subtract(1, 'days'), moment()],
          '三天內': [moment().subtract(3, 'days'), moment()]
        },
        eventHandlers: {
          'apply.daterangepicker': function(ev, picker) {
            $scope.dummyTable2 = getSuppliesStockChange();
          }
        }
      };




      // ================================ MODAL =========================================


      var detailModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesQueryDetail.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      $scope.showDetailModal = function(index) {



        $scope.detail = $scope.checkInList[index]
         searchStockChange.SuppliesUserId = $scope.detail.SuppliesUserId
         searchStockChange.SupplyId = $scope.detail.SupplyId
        $scope.dummyTable2 = getSuppliesStockChange()
          detailModal.$promise.then(detailModal.show);
      }





      //搜尋功能
      $scope.searchInventory = function() {
        if (!_.isNil($scope.search.SuppliesUserId)) {
          searchQuery['SuppliesUserId'] = $scope.search.SuppliesUserId
        } else {
          delete searchQuery['SuppliesUserId'];
        }
        if (!_.isNil($scope.search.SortCodeId)) {
          searchQuery['SortCodeId'] = $scope.search.SortCodeId
        } else {
          delete searchQuery['SortCodeId'];
        }

        if (!_.isNil($scope.search.code)) {
          searchQuery['code'] = $scope.search.code
        } else {
          delete searchQuery['code'];
        }

        if (!_.isNil($scope.search.SupplyId)) {
          searchQuery['SupplyId'] = $scope.search.SupplyId
        } else {
          delete searchQuery['SupplyId'];
        }

        if($scope.search.minimumAmount) {
          searchQuery['minimumAmount'] = $scope.search.minimumAmount
        } else {
          delete searchQuery['minimumAmount']
        }

        if($scope.search.expiryDate) {
          searchQuery['expiryDate'] = moment($scope.search.expiryDate).format("YYYY-MM-DD HH:mm:ss")
        } else {
          delete searchQuery['expiryDate']
        }

        refreshList()
      }

      //多筆查看
      // -------------附加勾選功能------------------------------------------------------
      // watch for check all checkbox
      $scope.$watch(function() {
        return $scope.checkboxes.checked;
      }, function(value) {
        angular.forEach($scope.checkInList, function(item) {
          $scope.checkboxes.items[item.id] = value;
        });
      });

      // watch for data checkboxes
      $scope.$watch(function() {
        return $scope.checkboxes.items;
      }, function(values) {
        var checked = 0,
          unchecked = 0,
          total = $scope.checkInList;
        angular.forEach($scope.checkInList, function(item) {
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
      // -------------附加勾選功能------------------------------------------------------

      $scope.showMultDetail = function() {
        var curIndex = -1;
        var idx = 0;
        var count = 0
        clearMultData();
        for(var key in $scope.checkboxes.items) {
          if($scope.checkboxes.items[key]) {
            count++
            if(curIndex == -1){
              curIndex = idx;
            }
          }
          idx ++;
        }
        if(count < 1) {
          EPCRServices.failAlert('錯誤!','請至少勾選一筆資料')
        } else {
          $scope.totalLength = count
          searchStockChange.SuppliesUserId = $scope.checkInList[curIndex].SuppliesUserId
          searchStockChange.SupplyId = $scope.checkInList[curIndex].SupplyId
          $scope.dummyTable2 = getSuppliesStockChange()
          detailModal.$promise.then(detailModal.show);
        }


      }

      //上一筆
      $scope.previousRecord = function() {
        $scope.cusIndex -= 1;
        searchStockChange.SuppliesUserId = $scope.checkInList[$scope.cusIndex].SuppliesUserId
        searchStockChange.SupplyId = $scope.checkInList[$scope.cusIndex].SupplyId
        $scope.dummyTable2 = getSuppliesStockChange()
      };

      // 下一筆
      $scope.nextRecord = function() {
        $scope.cusIndex += 1;
        searchStockChange.SuppliesUserId = $scope.checkInList[$scope.cusIndex].SuppliesUserId
        searchStockChange.SupplyId = $scope.checkInList[$scope.cusIndex].SupplyId
        $scope.dummyTable2 = getSuppliesStockChange()
      };

      //取得查看對象的ID後呈現庫存清單
      $scope.getSuppliesQuery = function() {
        $scope.checkboxes = {
          checked: false,
          items: {}
        }
        searchQuery.SuppliesUserId = $scope.search.SuppliesUserId;
        if($scope.search.expiryDate) {
          searchQuery['expiryDate'] = moment($scope.search.expiryDate).format("YYYY-MM-DD HH:mm:ss")
        } else {
          delete searchQuery['expiryDate']
        }
        refreshList()
        clearMultData();
      }

      //根據耗材分類來取得所屬耗材下拉選單
      $scope.getSuppliesDropDown = function() {
          getSupplies($scope.search.SortCodeId);
      }

      //庫存表單列印功能
      $scope.queryPrint = function() {
        getConfig()
          .then(function(result) {
            var hostname = result.hostname
            var printServer = result.printServer
            var port = result.port

            var url = hostname + ':' +port + '/#/suppliesQueryPrint/'
              + $scope.search.SuppliesUserId + '?token=' + AuthService.getToken();
            console.log(url)
            $window.open(printServer + '/api/render?url=' + encodeURIComponent(url), '_blank')
          })


      }

      $scope.detailListDownload = function() {
        let serializerParams = $httpParamSerializer(searchStockChange);
        let url = '/Inventory/searchStockChangeByDownload?token=' + AuthService.getToken();
        if(serializerParams.length > 0){
          url += ((url.indexOf('?') === -1 ) ? '?':'&') + serializerParams
        }
        $window.open(url)


      }

      //清除多選的筆數
      function clearMultData() {

        $scope.cusIndex = 0;
        $scope.totalLength = 0
      }

      function refreshList() {
        $scope.dummyTable = getSuppliesQueryRecord();
      }

      function getSuppliesQueryRecord() {
        // 分頁的能力，Server 端也要配合，所以這個範例先不實作
        var param = {}; // 用來打包要回傳給伺服器端的參數集合
        return new NgTableParams({
          page: 1,
          count: 25 // count per page,
        }, {
          filterDelay: 300,
          getData: function(params) {
            //如果沒選擇查看對象
            if(!$scope.search.SuppliesUserId) {
              return [];
            }
            var url = params.url();
            var limit = url.count,
              skip = url.count * (url.page - 1);
            defaultCount = url.count;
            var sorting;
            if (params.sorting()) {
              // 內建epilogue API，排序的寫法
              for (var key in params.sorting()) {
                if (params.sorting()[key] == 'desc') {
                  sorting = '-' + key;
                } else {
                  sorting = key;
                }
              }
            }
            searchQuery.time = new Date().getTime();
            searchQuery.sort = sorting;
            searchQuery.count = limit;
            searchQuery.offset = skip;


            console.log(searchQuery)

            return $http.get('/Inventory/searchQuery', {
                params: searchQuery,
                // paramSerializer: '$httpParamSerializerJQLike'
              })
              .then(function(response) {
                var range = contentRange.parse(response.headers('Content-Range'));
                var count = range.length;
                params.total(count);

                // console.log('@@@@ getSuppliesQueryRecord @@@@ response.data', response.data)
                $scope.checkInList = response.data;

                //初始化勾選的值
                for(var idx in response.data) {
                  $scope.checkboxes.items[response.data[idx].id] = false;
                }
                // console.log('$scope.checkboxes.items',$scope.checkboxes.items);
                return response.data; // 這邊的 return ，是直接給 ng-table 用的，因為 getData 就是它本身需要的功能
              })
              .catch(function(err) {
                console.log('### err', err)
                return [];
              })
          } // function
        })
      }


      function getSuppliesStockChange() {
        // 分頁的能力，Server 端也要配合，所以這個範例先不實作
        return new NgTableParams({
          page: 1,
          count: 25 // count per page,
        }, {
          filterDelay: 300,
          getData: function(params) {
            var url = params.url();
            var limit = url.count,
              skip = url.count * (url.page - 1);
            defaultCount = url.count;
            var sorting;
            if (params.sorting()) {
              // 內建epilogue API，排序的寫法
              for (var key in params.sorting()) {
                if (params.sorting()[key] == 'desc') {
                  sorting = '-' + key;
                } else {
                  sorting = key;
                }
              }
            }
            searchStockChange.time = new Date().getTime();
            searchStockChange.sort = sorting;
            searchStockChange.count = limit;
            searchStockChange.offset = skip;
            searchStockChange.startDate = $scope.sQuery.dateTime.startDate.startOf('day').toDate()
            searchStockChange.endDate = $scope.sQuery.dateTime.endDate.endOf('day').toDate()
            // $scope.checkboxes.checked = false;

            return $http.get('/Inventory/searchStockChange', {
                params: searchStockChange,
                // paramSerializer: '$httpParamSerializerJQLike'
              })
              .then(function(response) {
                var range = contentRange.parse(response.headers('Content-Range'));
                var count = range.length;
                params.total(count);

                console.log('@@@@ getSuppliesStockChange @@@@ response.data', response.data)


                return response.data; // 這邊的 return ，是直接給 ng-table 用的，因為 getData 就是它本身需要的功能
              })
              .catch(function(err) {
                console.log('### err', err)
                return [];
              })
          } // function
        })
      }

      //取得權限清單
      function getCheckUserList() {
        var userData = AuthService.getCurrentUser();
        return $http.get('/Supplies/permissionList',{
          params: userData
        })
        .then(function(response) {
          $scope.showPermissionList = response.data
        })
      }

      function getSortCodes() {
        return $http.get('/SortCodes')
          .then(function(response) {
            $scope.showSortCodes = response.data
          })
      }

      function getSupplies(SortCodeId) {
        return $http.get('/Supplies',{
          params: {
            SortCodeId: SortCodeId
          }
        })
          .then(function(response) {
            console.log('response.data=',response.data)
            $scope.showSupplies = response.data
          })
      }
      //取得config/publicConfig.json
      function getConfig() {
        return $http.get('/config')
          .then(function(response) {
            return response.data
          })
      }

      //取得耗材最小庫存量

      getCheckUserList();
      getSortCodes();

});
