CONTROLLERS.controller('SuppliesInventoryCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices, AuthService, $window, $httpParamSerializer) {

      // ================================ DUMMY DATA =========================================

      //預設搜尋條件
      var searchStockChange = {}


      // ================================ DATE RANGE PICKER =========================================
      $scope.dateTime = {
        startDate: moment().subtract(1, "days"),
        endDate: moment()
      };
      $scope.date = {
        begin: moment().subtract(1, 'day').toDate(),
        end: moment().add(1, 'day').toDate()
      }

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
        }
      };

      //取得查看對象的ID後呈現庫存清單
      $scope.getStockChangeList = function() {
        searchStockChange.SuppliesUserId = $scope.search.SuppliesUserId
        refreshList()
        getRequestList($scope.search.SuppliesUserId);
      }

      //搜尋功能
      $scope.searchInventory = function() {
        if (!_.isNil($scope.search.SuppliesUserId)) {
          searchStockChange['SuppliesUserId'] = $scope.search.SuppliesUserId
        } else {
          delete searchStockChange['SuppliesUserId'];
        }

        if(!_.isEmpty($scope.dateTime)) {
           searchStockChange['startDate'] = $scope.dateTime.startDate.startOf('day').toDate()
           searchStockChange['endDate'] = $scope.dateTime.endDate.endOf('day').toDate()
        }

        if (!_.isNil($scope.search.StockTypeId)) {
          delete searchStockChange['isRequest'];
          delete searchStockChange['isIssuance'];
          switch ($scope.search.StockTypeId) {
              case 1:
                  searchStockChange['isRequest'] = 0
                  break;
              case 2:
                  searchStockChange['isRequest'] = 1
                  break;
              case 3:
                  searchStockChange['isIssuance'] = 0
                  break;
              case 4:
                  searchStockChange['isIssuance'] = 1
                  break;
          }
        }


        if (!_.isNil($scope.search.SupplyId)) {
          searchStockChange['SupplyId'] = $scope.search.SupplyId
        } else {
          delete searchStockChange['SupplyId'];
        }

        if (!_.isNil($scope.search.SourcesId)) {
          searchStockChange['SourcesId'] = $scope.search.SourcesId
        } else {
          delete searchStockChange['SourcesId'];
        }

        refreshList()
      }

      $scope.detailListDownload = function() {
        let serializerParams = $httpParamSerializer(searchStockChange);
        let url = '/Inventory/searchStockChangeByDownload?token=' + AuthService.getToken();
        if(serializerParams.length > 0){
          url += ((url.indexOf('?') === -1 ) ? '?':'&') + serializerParams
        }
        $window.open(url)


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

      //選完查看對象後取得單位清單
      function getRequestList(SuppliesUserId) {

        return $http.get('/Supplies/requestList', {
          params: {
            SuppliesUserId: SuppliesUserId
          }
        })
        .then(function(response) {
          $scope.showSources = response.data
        })
      }

      function refreshList() {
        $scope.dummyTable = getSuppliesStockChange();
      }

      function getSuppliesStockChange() {
        // 分頁的能力，Server 端也要配合，所以這個範例先不實作
        return new NgTableParams({
          page: 1,
          count: 25 // count per page,
        }, {
          filterDelay: 300,
          counts: [],
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
            // $scope.checkboxes.checked = false;
            console.log('searchStockChange=',searchStockChange)
            return $http.get('/Inventory/searchStockChange', {
                params: searchStockChange,
                // paramSerializer: '$httpParamSerializerJQLike'
              })
              .then(function(response) {
                var range = contentRange.parse(response.headers('Content-Range'));
                var count = range.length;
                params.total(count);

                console.log('@@@@ getAllSuppliesStockChange @@@@ response.data', response.data)


                return response.data; // 這邊的 return ，是直接給 ng-table 用的，因為 getData 就是它本身需要的功能
              })
              .catch(function(err) {
                console.log('### err', err)
                return [];
              })
          } // function
        })
      }

      function getSupplies() {
        return $http.get('/Supplies')
          .then(function(response) {
            $scope.showSupplies = response.data
          })
      }

      function getStockType() {
        return $http.get('json/StockType.json')
          .then(function(response) {
            $scope.showStockTypes = response.data
          })
      }

      getCheckUserList();
      getSupplies();
      getStockType();
});
