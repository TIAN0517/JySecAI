CONTROLLERS.controller('SuppliesStockOutCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices, AuthService) {
      //預設搜尋條件
      var searchQuery = {}
      console.log("time1!!!!!!!!!!!",moment().format('x'))
      //出庫附檔的資料
      var StockOutDetailList = []

      // ================================ DATE RANGE PICKER =========================================
      $scope.search = { stockOutAt: {
        startDate: moment().subtract(1, "days"),
        endDate: moment()
        }
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
        },
        eventHandlers: {
          'cancel.daterangepicker': function(ev, picker) {
            $scope.search.stockOutAt = {}
          }
        }
      };
      // ================================ DATE RANGE PICKER =========================================

      // ================================ MODAL =========================================
      var addModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesStockOutAdd.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      var editModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesStockOutEdit.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      var detailEditModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesStockOutDetailEdit.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      var delModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesStockOutDel.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      //搜尋
      $scope.searchStockOut = function() {
        if (!_.isNil($scope.search.code)) {
          searchQuery['code'] = {
            $like: '%' + $scope.search.code + '%'
          };
        } else {
          delete searchQuery['contractCode'];
        }

        if (!_.isEmpty($scope.search.stockOutAt)) {
          searchQuery['stockOutAt'] = {
            $between: [$scope.search.stockOutAt.startDate.startOf('day').toDate(), $scope.search.stockOutAt.endDate.endOf('day').toDate()]
          };
        } else {
          delete searchQuery['stockOutAt'];
        }

        if (!_.isNil($scope.search.StockOutKindId)) {
          searchQuery['StockOutKindId'] = $scope.search.StockOutKindId
        } else {
          delete searchQuery['StockOutKindId'];
        }
        refreshList()

      }


      //根據耗材分類來取得所屬耗材下拉選單
      $scope.getSuppliesDropDown = function(type) {
        if(type== 'add') {
          getSupplies($scope.add.detail.SortCodeId);
        } else {
          getSupplies($scope.detailEdit.Supply.SortCodeId);
        }
      }



      //新增入庫Modal
      $scope.showAddModal = function() {
        //清空Detail
        StockOutDetailList.length = 0
        getSuppliesUser()
          .then(function(response) {
            $scope.add = {
              userName: response.name,
              StockOutManId: response.id,
              stockOutAt: moment(),
              detail: {}
            }
          })
        $scope.error = ''
          addModal.$promise.then(addModal.show);
      }


      //新增StockOutMaster & StockOutDetail
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
              stockOutAt: $scope.add.stockOutAt,
              StockOutManId: $scope.add.StockOutManId,
              StockOutSourceManId: $scope.add.StockOutManId,
              StockStorageId: $scope.add.StockStorageId,
              StockOutKindId: $scope.add.StockOutKindId,
              note: $scope.add.note,
              storageNote: $scope.add.storageNote,
              StockOutDetails: []
            }
            angular.forEach($scope.dummyTable2.data, function(data) {
              var detailData = {
                SupplyId: data.SupplyId,
                expiryDate: data.expiryDate,
                amount: data.amount
              }
              toAddData.StockOutDetails.push(detailData)
            })
            console.log('toAddData=',toAddData)
            return $http.post('/Stock/stockOut',toAddData)
              .then(function(response) {
                deferred.resolve();
                refreshList();
                EPCRServices.successAlert('成功!','新增成功')
                addModal.$promise.then(addModal.hide);
              })
              .catch(function(err) {
                console.log(err)
                deferred.resolve();
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


      //編輯入庫modal
      $scope.showEditModal = function(index) {

        $scope.edit = angular.copy($scope.checkInList[index]);

        refreshDetailList()
        console.log('$scope.edit=',$scope.edit)
          editModal.$promise.then(editModal.show);
      }

      //編輯StockOutMaster資料
      $scope.toEdit = function(formEdit) {
        console.log("formEdit", formEdit)
        if (formEdit.$valid) {
          var deferred = $q.defer();
          $scope.myPromise = deferred.promise;
          //TODO modifyManId 須取得當前使用者是誰
          var toEditData = {
            stockOutAt: $scope.edit.stockOutAt,
            StockOutManId: $scope.edit.StockOutManId,
            StockStorageId: $scope.edit.StockStorageId,
            StockOutKindId: $scope.edit.StockOutKindId,
            storageNote: $scope.edit.storageNote,
            note: $scope.edit.note
          };
          return $http.put('/StockOutMasters/' + $scope.edit.id, toEditData)
            .then(function(response) {
                deferred.resolve();
                EPCRServices.successAlert('成功!','修改成功')
                refreshList()
                editModal.$promise.then(editModal.hide);
            })
            .catch(function(err) {
              deferred.resolve();
              console.log('Edit fails =', err)
              if (err && err.data && err.data.error && !_.isEmpty(err.data.error)) {
                EPCRServices.failAlertToModal('錯誤！', err.data.error[0])
              } else {
                EPCRServices.failAlertToModal('錯誤！', '修改失敗！');
              }
            })
          } else {
            $scope.error = '必填欄位未輸入完成，請確認，謝謝'
          }

      }
      //編輯入庫細項modal
      $scope.showDetailEditModal = function(index) {
        $scope.detailEdit = angular.copy($scope.edit.StockOutDetails[index])
        getSupplies($scope.detailEdit.Supply.SortCodeId);
        console.log('$scope.detailEdit=',$scope.detailEdit)
        detailEditModal.$promise.then(detailEditModal.show)
      }


      //編輯入庫細項(StockOutDetail)資料
      $scope.toDetailEdit = function(formDetailEdit) {
        if(formDetailEdit.$valid) {
          var deferred = $q.defer();
          $scope.myPromise = deferred.promise;
          var toEditDetailData = {
            amount: $scope.detailEdit.amount,
            expiryDate: $scope.detailEdit.expiryDate,
            SupplyId: $scope.detailEdit.SupplyId
          }
          console.log('toEditDetailData=',toEditDetailData)
          return $http.put('/Stock/stockOutDetail/' + $scope.detailEdit.id, toEditDetailData)
            .then(function(response) {
              deferred.resolve();
              refreshDetailList();
              detailEditModal.$promise.then(detailEditModal.hide);
            })
            .catch(function(err) {
              deferred.resolve();
              console.log('Edit fails =', err)
              if (err && err.data && err.data.error && !_.isEmpty(err.data.error)) {
                EPCRServices.failAlertToModal('錯誤！', err.data.error[0])
              } else {
                EPCRServices.failAlertToModal('錯誤！', '修改失敗！');
              }
            })
        } else {
          console.log('必填欄位沒有寫')
        }
      }
      //刪除入庫modal
      $scope.showDelModal = function(index) {
        $scope.delete = {
          "id": $scope.checkInList[index].id
        }
          delModal.$promise.then(delModal.show);
      }

      $scope.toDelete = function() {
        var deferred = $q.defer();
        $scope.myPromise = deferred.promise;
        return $http.delete('/Stock/stockOut/' + $scope.delete.id)
          .then(function(response) {
              deferred.resolve();
              EPCRServices.successAlert('成功!','刪除成功')
              refreshList()
              delModal.$promise.then(delModal.hide);
          })
          .catch(function(err) {
            deferred.resolve();
            console.log('delete fails =', err)
            if (err && err.data && err.data.error && !_.isEmpty(err.data.error)) {
              EPCRServices.failAlertToModal('錯誤！', err.data.error[0])
            } else {
              EPCRServices.failAlertToModal('錯誤！', '刪除失敗！');
            }
          })
      }


      //新增暫存Detail資料&呈現
      $scope.addStockOutDetail = function() {
          if(!_.isNil($scope.add.detail.SupplyId) && !_.isNil($scope.add.detail.amount)) {
            return $http.get('/Supplies',{
              params: {id: $scope.add.detail.SupplyId}
            })
            .then(function(response) {
              var detailData = {
                "SupplyId": response.data[0].id,
                "name": response.data[0].name,
                "expiryDate": $scope.add.detail.expiryDate,
                "amount": $scope.add.detail.amount,
                "UnitCode": response.data[0].UnitCode.name
              }
              StockOutDetailList.splice(0,0,detailData);
              //清空資料
              cleanAddDetail()
              $scope.dummyTable2 = showStockOutDetail();
            })
          } else {
            EPCRServices.failAlertToModal('錯誤！', '耗材或數量未填寫');
          }

      }
      //刪除暫存Detail資料&呈現
      $scope.delStockOutDetail = function(index) {
        console.log('index=',index)
        StockOutDetailList.splice(index, 1);
        $scope.dummyTable2 = showStockOutDetail();
      }

      //清除新增入庫細項的輸入框資料
      function cleanAddDetail() {
          $scope.add.detail = {}
      }

      function refreshList() {

        $scope.dummyTable = getStockOutMasters();

      }

      function refreshDetailList() {
        $scope.dummyTable3 = getStockOutDetails()
      }

      function getStockOutMasters() {
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

            return $http.get('/StockOutMasters', {
                params: searchQuery,
                // paramSerializer: '$httpParamSerializerJQLike'
              })
              .then(function(response) {
                var range = contentRange.parse(response.headers('Content-Range'));
                var count = range.length;
                params.total(count);

                console.log('@@@@ getStockOutMasters @@@@ response.data', response.data)
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


      function getStockOutDetails() {
        // 分頁的能力，Server 端也要配合，所以這個範例先不實作
        var param = {}; // 用來打包要回傳給伺服器端的參數集合
        return new NgTableParams({
          // page: 1,
          count: Infinity // count per page,
        }, {
          counts:[],
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

            param.StockOutMasterId = $scope.edit.id

            return $http.get('/StockOutDetails', {
                params: param,
                // paramSerializer: '$httpParamSerializerJQLike'
              })
              .then(function(response) {
                var range = contentRange.parse(response.headers('Content-Range'));
                var count = range.length;
                params.total(count);

                console.log('@@@@ getStockOutDetails @@@@ response.data', response.data)

                return response.data; // 這邊的 return ，是直接給 ng-table 用的，因為 getData 就是它本身需要的功能
              })
              .catch(function(err) {
                console.log('### err', err)
                return [];
              })
          } // function
        })
      }

      function getStockOutKinds() {
        return $http.get('/StockOutKinds')
          .then(function(response) {
            $scope.showStockOutKinds = response.data
          })
      }

      function getStockStorages() {
        return $http.get('/StockStorages')
          .then(function(response) {
            $scope.showStockStorages = response.data
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
            $scope.showSupplies = response.data
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
          searchQuery.StockOutManId = response.data[0].id
          return response.data[0]
        })
      }

      function showStockOutDetail(){
        return new NgTableParams({count: Infinity}, { dataset: StockOutDetailList, counts: []});
      }





      getStockOutKinds();
      getSortCodes();
      getStockStorages();
      getSuppliesUser()
      .then(function() {
          refreshList();
      })
});
