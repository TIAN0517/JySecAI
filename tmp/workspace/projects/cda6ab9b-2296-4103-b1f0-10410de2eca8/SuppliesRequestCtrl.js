CONTROLLERS.controller('SuppliesRequestCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices, AuthService, $stateParams, $window) {


      //預設搜尋條件
      var searchQuery = {
        ListStatusId: {
          $notIn: [4]
        }
      }

      //申請附檔的資料
      var requestDetailList = []
      // ================================ DATE RANGE PICKER =========================================
      // $scope.search = { requestDate: {
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
            $scope.search.requestDate = {}
          }
        }
      };
      // ================================ MODAL =========================================
      var addModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesRequestAdd.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      var detailModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesRequestDetail.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      var delModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesRequestDel.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      })

      //搜尋
      $scope.searchRequest = function() {
        if (!_.isNil($scope.search.code)) {
          searchQuery['code'] = {
            $like: '%' + $scope.search.code + '%'
          };
        } else {
          delete searchQuery['code'];
        }

        if (!_.isEmpty($scope.search.requestDate)) {
          searchQuery['requestDate'] = {
            $between: [$scope.search.requestDate.startDate.startOf('day').toDate(), $scope.search.requestDate.endDate.endOf('day').toDate()]
          };
        } else {
          delete searchQuery['requestDate'];
        }

        if (!_.isNil($scope.search.IssuanceManId)) {
          searchQuery['IssuanceManId'] = $scope.search.IssuanceManId
        } else {
          delete searchQuery['IssuanceManId'];
        }
        if (!_.isNil($scope.search.ListStatusId)) {
          searchQuery['ListStatusId'] = $scope.search.ListStatusId
        } else {
          delete searchQuery['ListStatusId'];
        }
        refreshList()

      }

      $scope.getSuppliesDropDown = function() {
          getSupplies($scope.add.detail.SortCodeId);

      }

      $scope.showAddModal = function() {
      checkAlreadyRequest()
        .then(function(result) {
          if (result) {
            getSuppliesUser()
              .then(function(response) {
                $scope.add = {
                  userName: response.name,
                  RequestManId: response.id,
                  requestDate: moment(),
                  detail: {}
                }
              })
            addModal.$promise.then(addModal.show);
          } else {
            EPCRServices.failAlert('錯誤!','尚有申請單未結案')
          }
        })
      }

      //新增RequestMaster & RequestDetail
      $scope.toAdd = function(formAdd) {
          var serialNumber = "" + moment().format('YYYYMMDDHHmmssSS')
          if(formAdd.$valid) {
            if(_.isNil($scope.dummyTable2)) {
              EPCRServices.failAlertToModal('錯誤!','未新增任何耗材')
            } else {
              var deferred = $q.defer();
              $scope.myPromise = deferred.promise;
              var toAddData = {
                code: serialNumber,
                requestDate: $scope.add.requestDate,
                ListStatusId: 1,
                RequestManId: $scope.add.RequestManId,
                IssuanceManId: $scope.add.IssuanceManId,
                note: $scope.add.note,
                SuppliesRequestDetails: []
              }
              angular.forEach($scope.dummyTable2.data, function(data) {
                var detailData = {
                  SupplyId: data.SupplyId,
                  requestAmount: data.requestAmount
                }
                toAddData.SuppliesRequestDetails.push(detailData)
              })
              console.log('toAddData=',toAddData)
              return $http.post('/SuppliesRequests',toAddData)
                .then(function(response) {
                  deferred.resolve();
                  refreshList();
                  addModal.$promise.then(addModal.hide);
                })
                .catch(function(err) {
                  deferred.resolve();
                  console.log('delete fails =', err)
                  if (err && err.data && err.data.error && !_.isEmpty(err.data.error)) {
                    EPCRServices.failAlertToModal('錯誤！', err.data.error[0])
                  } else {
                    EPCRServices.failAlertToModal('錯誤！', '新增失敗！');
                  }
                })
            }
          } else {
            EPCRServices.failAlertToModal('錯誤！', '必填欄位未填寫！');
          }

      }

      $scope.showDetailModal = function(index) {

        $scope.detail = $scope.checkInList[index]
        $scope.dummyTable3 = showDetail(index)
        console.log('$scope.detail=',$scope.detail)
          detailModal.$promise.then(detailModal.show);
      }

      $scope.showDelModal = function(index) {
        $scope.delete = {
          "id": $scope.checkInList[index].id
        }
        delModal.$promise.then(delModal.show)
      }

      //取消申請單
      $scope.toDelete = function() {
        var deferred = $q.defer();
        $scope.myPromise = deferred.promise;
        return $http.put('/SuppliesRequests/' + $scope.delete.id,{
          ListStatusId: 4
          })
          .then(function(response) {
              deferred.resolve();
              EPCRServices.successAlert('成功!','取消成功')
              refreshList()
              delModal.$promise.then(delModal.hide);
          })
          .catch(function(err) {
            deferred.resolve();
            console.log('delete fails =', err)
            if (err && err.data && err.data.error && !_.isEmpty(err.data.error)) {
              EPCRServices.failAlertToModal('錯誤！', err.data.error[0])
            } else {
              EPCRServices.failAlertToModal('錯誤！', '取消失敗！');
            }
          })
      }

      //新增暫存Detail資料&呈現
      $scope.addRequestDetail = function() {
          if(!_.isNil($scope.add.detail.SupplyId) && !_.isNil($scope.add.detail.requestAmount)) {
            return $http.get('/Supplies',{
              params: {id: $scope.add.detail.SupplyId}
            })
            .then(function(response) {
              var detailData = {
                "SupplyId": response.data[0].id,
                "name": response.data[0].name,
                "requestAmount": $scope.add.detail.requestAmount,
                "UnitCode": response.data[0].UnitCode.name
              }
              requestDetailList.splice(0,0,detailData);
              //清空資料
              cleanAddDetail()
              $scope.dummyTable2 = showRequestDetail();
            })
          } else {
            EPCRServices.failAlertToModal('錯誤！', '耗材或數量未填寫');
          }
      }

      //刪除暫存Detail資料&呈現
      $scope.delRequestDetail = function(index) {
        console.log('index=',index)
        requestDetailList.splice(index, 1);
        $scope.dummyTable2 = showRequestDetail();
      }
      //申請單列印功能
      $scope.detailPrint = function() {
        getConfig()
          .then(function(result) {
            var hostname = result.hostname
            var printServer = result.printServer
            var port = result.port

            var url = hostname + ':' + port + '/#/suppliesRequestDetailPrint/'
              + $scope.detail.id + '?token=' + AuthService.getToken();
            console.log(url)
            $window.open(printServer + '/api/render?url=' + encodeURIComponent(url), '_blank')
          })

      }

      //清除新增入庫細項的輸入框資料
      function cleanAddDetail() {
          $scope.add.detail = {}
      }

      function refreshList() {
        $scope.dummyTable = getRequestMasters();
      }

      function getRequestMasters() {
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

            return $http.get('/SuppliesRequests', {
                params: searchQuery,
                // paramSerializer: '$httpParamSerializerJQLike'
              })
              .then(function(response) {
                var range = contentRange.parse(response.headers('Content-Range'));
                var count = range.length;
                params.total(count);

                console.log('@@@@ getRequestMasters @@@@ response.data', response.data)
                $scope.checkInList = response.data;

                return response.data; // 這邊的 return ，是直接給 ng-table 用的，因為 getData 就是它本身需要的功能
              })
              .catch(function(err) {
                console.log('### err', err)
                return [];
              })
          } // function
        })
      }


      //取得是否已經有申請單存在
      function checkAlreadyRequest() {
        return $http.get('/SuppliesRequests', {
          params: {
            RequestManId: searchQuery.RequestManId,
            ListStatusId: {
              $notIn: [3,4]
            }
          }
        })
        .then(function(response) {
          if(response.data.length > 0) {
            return false
          } else {
            return true
          }
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
          searchQuery.RequestManId = response.data[0].id
          return response.data[0]
        })
      }

      function getListStatuses() {
        return $http.get('/ListStatuses')
          .then(function(response) {
            $scope.showListStatuses = response.data
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

      function showRequestDetail(){
        return new NgTableParams({count: Infinity}, { dataset: requestDetailList, counts: []});
      }

      function showDetail(index) {
        return new NgTableParams({count: Infinity}, { dataset: $scope.checkInList[index].SuppliesRequestDetails, counts: []});
      }
      getRequestList();
      getListStatuses();
      getSortCodes();
      getSuppliesUser()
      .then(function() {
          refreshList();
      })
});
