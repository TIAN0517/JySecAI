CONTROLLERS.controller('SuppliesIssuanceCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices, AuthService) {


      //預設搜尋條件
      var searchQuery = {}

      // ================================ MODAL =========================================
      var receiveModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesIssuanceReceive.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      var detailModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesIssuanceDetail.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      //搜尋
      $scope.searchRequest = function() {
        if (!_.isNil($scope.search.code)) {
          searchQuery['code'] = {
            $like: '%' + $scope.search.code + '%'
          };
        } else {
          delete searchQuery['code'];
        }

        if (!_.isEmpty($scope.search.IssuanceDate)) {
          searchQuery['IssuanceDate'] = {
            $between: [$scope.search.IssuanceDate.startDate.startOf('day').toDate(), $scope.search.IssuanceDate.endDate.endOf('day').toDate()]
          };
        } else {
          delete searchQuery['IssuanceDate'];
        }

        if (!_.isNil($scope.search.RequestManId)) {
          searchQuery['RequestManId'] = $scope.search.RequestManId
        } else {
          delete searchQuery['RequestManId'];
        }
        if (!_.isNil($scope.search.ListStatusId)) {
          searchQuery['ListStatusId'] = $scope.search.ListStatusId
        } else {
          delete searchQuery['ListStatusId'];
        }
        refreshList()
      }
      //查詢核發單
      $scope.searchReceive = function() {
        if (!_.isNil($scope.receiveSearch.receiveCode) && $scope.receiveSearch.receiveCode != "") {
          searchQuery['receiveCode'] = $scope.receiveSearch.receiveCode
          searchQuery['ListStatusId'] = 2
          $scope.receiveTable = getRequestMasters('receive');
        } else {
          EPCRServices.failAlertToModal('錯誤！', '請輸入核發單號！');
          delete searchQuery['receiveCode'];
        }

      }

      $scope.showReceiveModal = function() {
        searchQuery = {}
        $scope.receiveSearch = {}
        // $scope.receiveTable = getRequestMasters('receive');
          receiveModal.$promise.then(receiveModal.show);
      }

      //核發領出(執行核發方出庫 & 申請方入庫)
      $scope.toReceiveConfirm = function() {
        var serialNumber = "" + moment().format('YYYYMMDDHHmmssSS')
        var deferred = $q.defer();
        var receiveCode = $scope.receiveSearch.receiveCode
        $scope.myPromise = deferred.promise;
        //入庫資料
        var toStockInData = {
          code: serialNumber,
          stockInAt: moment(),
          StockInManId: $scope.receiveList[0].RequestManId,
          StockInSourceManId: $scope.receiveList[0].IssuanceManId,
          isRequest: 1,
          StockInDetails: []
        }
        angular.forEach($scope.receiveList[0].SuppliesRequestDetails, function(data) {
          var detailData = {
            SupplyId: data.SupplyId,
            amount: data.IssuanceAmount
          }
          toStockInData.StockInDetails.push(detailData)
        })
        //出庫資料
        var toStockOutData = {
          code: serialNumber,
          stockOutAt: moment(),
          StockOutManId: $scope.receiveList[0].IssuanceManId,
          StockOutSourceManId: $scope.receiveList[0].RequestManId,
          isIssuance: 1,
          StockOutDetails: []
        }
        angular.forEach($scope.receiveList[0].SuppliesRequestDetails, function(data) {
          var detailData = {
            SupplyId: data.SupplyId,
            amount: data.IssuanceAmount
          }
          toStockOutData.StockOutDetails.push(detailData)
        })
        console.log('toStockInData=',toStockInData)
        console.log('toStockOutData=',toStockOutData)
        // return $http.put('/SuppliesRequests/' + $scope.receiveList[0].id, {
        //   ListStatusId: 3
        // })
        // .then(function() {
        //   return $http.post('/Stock/stockOut',toStockOutData)
        // })
        // .then(function() {
        //   return $http.post('/Stock/stockIn',toStockInData)
        // })
        return $http.put('/Stock/Issuance/' + receiveCode, {})
        .then(function() {
          deferred.resolve();
          EPCRServices.successAlert('成功!','領取成功')
          refreshList();
          receiveModal.$promise.then(receiveModal.hide);
        })
        .catch(function(err) {
          deferred.resolve();
          console.log('receive fails =', err)
          if (err && err.data && err.data.error && !_.isEmpty(err.data.error)) {
            EPCRServices.failAlertToModal('錯誤！', err.data.error[0])
          } else {
            EPCRServices.failAlertToModal('錯誤！', '領出失敗！');
          }
        })

      }

      $scope.showDetailModal = function(index) {
        $scope.detail = $scope.checkInList[index]
        $scope.dummyTable2 = showDetail(index)
        console.log('$scope.detail=',$scope.detail)
          detailModal.$promise.then(detailModal.show);
      }

      $scope.toDetailConfirm = function() {
        //確認核發時核發方數量需小於核發方庫存
        var amountCheck = true
        angular.forEach($scope.detail.SuppliesRequestDetails, function(data) {
          if(data.IssuanceAmount > data.IssuanceManStock) {
            amountCheck = false
          }
        })
        if(amountCheck) {
          var deferred = $q.defer();
          $scope.myPromise = deferred.promise;
          var receiveCode = "" + moment().format('YYYYMMDDHHmmssSS')
          var toConfirmData = {
            ListStatusId: 2,
            IssuanceDate: moment(),
            receiveCode: receiveCode,
            SuppliesRequestDetails: []
          }
          angular.forEach($scope.detail.SuppliesRequestDetails, function(data) {
            var detailData = {
              id: data.id,
              IssuanceAmount: data.IssuanceAmount
            }
            toConfirmData.SuppliesRequestDetails.push(detailData)
          })
          return $http.put('/Stock/requestConfirm/' + $scope.detail.id, toConfirmData)
            .then(function(response) {
              deferred.resolve();
              EPCRServices.successAlert('成功!','確認成功')
              refreshList();
              detailModal.$promise.then(detailModal.hide);
            })
            .catch(function(err) {
              deferred.resolve();
              console.log('Edit fails =', err)
              if (err && err.data && err.data.error && !_.isEmpty(err.data.error)) {
                EPCRServices.failAlertToModal('錯誤！', err.data.error[0])
              } else {
                EPCRServices.failAlertToModal('錯誤！', '確認失敗！');
              }
            })
        } else {
          EPCRServices.failAlertToModal('錯誤！', '核發數量不可大於庫存量！');
        }

      }

      $scope.checkIfDatePicker = function(statusId){
        if ( statusId==1 ){
          $scope.search.IssuanceDate = "";
        }
      }

      // ================================ DATE RANGE PICKER =========================================
      // $scope.search = { IssuanceDate: {
      //   startDate: moment().subtract(1, "days"),
      //   endDate: moment()
      //   }
      // };

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
          'cancel.daterangepicker': function(ev, picker) {
            $scope.search.IssuanceDate = {}
          }
        }
      };

      function refreshList() {
        $scope.dummyTable = getRequestMasters();
      }

      function getRequestMasters(type) {
        // 分頁的能力，Server 端也要配合，所以這個範例先不實作
        var param = {}; // 用來打包要回傳給伺服器端的參數集合
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
            searchQuery.time = new Date().getTime();
            searchQuery.sort = sorting;
            searchQuery.count = limit;
            searchQuery.offset = skip;
            // $scope.checkboxes.checked = false;

            console.log(searchQuery)

            return $http.get('/Inventory/searchRequestAndStock', {
                params: searchQuery,
                // paramSerializer: '$httpParamSerializerJQLike'
              })
              .then(function(response) {
                var range = contentRange.parse(response.headers('Content-Range'));
                var count = range.length;
                params.total(count);

                console.log('@@@@ getRequestMasters @@@@ response.data', response.data)
                if(!type) {
                  $scope.checkInList = response.data;
                  return response.data; // 這邊的 return ，是直接給 ng-table 用的，因為 getData 就是它本身需要的功能
                } else {
                  $scope.receiveList = response.data
                  $scope.queryLength = response.data.length

                  if(response.data.length == 0) {
                    EPCRServices.failAlertToModal('失敗！', '無此核發單號！');
                    return []
                  } else {
                    return response.data[0].SuppliesRequestDetails // 這邊的 return ，是直接給 ng-table 用的，因為 getData 就是它本身需要的功能
                  }


                }

              })
              .catch(function(err) {
                console.log('### err', err)
                return [];
              })
          } // function
        })
      }

      function getListStatuses() {
        return $http.get('/ListStatuses')
          .then(function(response) {
            $scope.showListStatuses = response.data
          })
      }

      //取得申請權限清單
      function getRequestList() {
        var userData = AuthService.getCurrentUser();
        return $http.get('/Supplies/requestList',{
          params: userData
        })
        .then(function(response) {
          $scope.showRequestList = response.data
        })
      }

      function getSuppliesUser() {
        var userData = AuthService.getCurrentUser()
        console.log("userData=",userData)
        return $http.get('/SuppliesUsers', {
          params: {
            "account": userData.account
          },
          paramSerializer: '$httpParamSerializerJQLike'
        })
        .then(function(response) {
          console.log('response.data=',response.data)
          searchQuery.IssuanceManId = response.data[0].id
          return response.data[0]
        })
      }

      function showDetail(index) {
        return new NgTableParams({count: Infinity}, { dataset: $scope.checkInList[index].SuppliesRequestDetails, counts: []});
      }

      getListStatuses();
      getRequestList();
      getSuppliesUser()
      .then(function() {
          refreshList();
      })
});
