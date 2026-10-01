CONTROLLERS.controller('SuppliesConfigCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $filter, $element, EPCRServices, AuthService) {

      //預設搜尋條件

      var suppliesUserData = {} ;
      var searchQuery = {}



      var addModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesConfigAdd.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      var editModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesConfigEdit.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      var delModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesConfigDel.html',
          animation: 'no-animation',
          placement: 'center',
          backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false
      });

      var unitCodeModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesUnitCodeEdit.html',
          animation: 'no-animation',
          placement: 'center',
          // backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false,
          onHide:refreshList
      });

      var sortCodeModal = $modal({
          scope: $scope,
          templateUrl: 'templates/modal/suppliesSortCodeEdit.html',
          animation: 'no-animation',
          placement: 'center',
          // backdrop: 'static', // ㄚ不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
          show: false,
          onHide:refreshList
      });

      $scope.showAddModal = function() {
          $scope.add = {};
          $scope.error = "";
          addModal.$promise.then(addModal.show);
      }

      $scope.toAdd = function(formAdd, status) {
        console.log("formAdd", formAdd)
        if (formAdd.$valid) {
          var deferred = $q.defer();
          $scope.myPromise = deferred.promise;
          //TODO modifyManId 須取得當前使用者是誰
          var toAddData = {
            "name": $scope.add.name,
            "code": $scope.add.code,
            // "minimumAmount": $scope.add.minimumAmount,
            "UnitCodeId": $scope.add.UnitCodeId,
            "SortCodeId": $scope.add.SortCodeId
          };
          if($scope.add.autoDiff == 1) {
            toAddData.isAuto = false
          } else {
            toAddData.isAuto = true;
          }
          return $http.post('/Supplies',toAddData)
            .then(function(response) {
              deferred.resolve();
              if(status == 'next') {
                $scope.add = {}
                EPCRServices.successAlertToModal('成功!','新增成功')
                refreshList()
              } else {
                EPCRServices.successAlertToModal('成功!','新增成功')
                refreshList()
                addModal.$promise.then(addModal.hide);
              }
            })
            .catch(function(err) {
              deferred.resolve();
              console.log('Add fails =', err)
              if (err && err.data && err.data.error && !_.isEmpty(err.data.error)) {
                EPCRServices.failAlertToModal('錯誤！', err.data.error[0])
              } else {
                EPCRServices.failAlertToModal('錯誤！', '新增失敗！');
              }
            })
          } else {
            $scope.error = '必填欄位未輸入完成，請確認，謝謝'
          }
      }


      $scope.showEditModal = function(index) {
          $scope.error = ''
          $scope.edit = $scope.checkInList[index]
          if($scope.checkInList[index].isAuto) {
            $scope.edit.autoDiff = 2
          } else {
            $scope.edit.autoDiff = 1
          }
          editModal.$promise.then(editModal.show);
      }

      $scope.toEdit = function(formEdit) {
        console.log("formEdit", formEdit)
        if (formEdit.$valid) {
          var deferred = $q.defer();
          $scope.myPromise = deferred.promise;
          //TODO modifyManId 須取得當前使用者是誰
          var toEditData = {
            "name": $scope.edit.name,
            "code": $scope.edit.code,
            // "minimumAmount": $scope.edit.minimumAmount,
            "UnitCodeId": $scope.edit.UnitCodeId,
            "SortCodeId": $scope.edit.SortCodeId
          };
          if($scope.edit.autoDiff == 1) {
            toEditData.isAuto = false;
          } else {
            toEditData.isAuto = true;
          }
          return $http.put('/Supplies/' + $scope.edit.id, toEditData)
            .then(function(response) {
              return updateMinAmount($scope.edit.minimumAmount, $scope.edit.suppliesInventoryId)
            })
            .then(function(result){
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

      $scope.showDelModal = function(index) {
          $scope.delete = {
            "id": $scope.checkInList[index].id
          }
          delModal.$promise.then(delModal.show);
      }

      $scope.toDelete = function() {
          var deferred = $q.defer();
          $scope.myPromise = deferred.promise;
          return $http.delete('/Inventory/deleteSupply/' + $scope.delete.id)
            .then(function(response) {
                deferred.resolve();
                EPCRServices.successAlert('成功!','刪除成功')
                refreshList()
                delModal.$promise.then(delModal.hide);
            })
            .catch(function(err) {
              deferred.resolve();
              console.log('del fails =', err)
              if ( err && err.status==400 ) {
                window.alert("已有耗材使紀錄，無法刪除！")
              } else {
                window.alert("錯誤，刪除失敗！")
              }
            })
      }

      $scope.showUnitCodeEditModal = function() {
          $scope.add = {};
          $scope.error = "";
          unitCodeModal.$promise.then(unitCodeModal.show);
          $scope.unitCodeEditing = {} ;
      }


      $scope.showSortCodeAddModal = function() {
          $scope.add = {};
          $scope.error = "";
          sortCodeModal.$promise.then(sortCodeModal.show);
          $scope.sortCodeEditing = {} ;
      }

      $scope.searchSup = function() {
        if (!_.isNil($scope.search.SortCodeId)) {
          searchQuery['SortCodeId'] = $scope.search.SortCodeId;
        } else {
          delete searchQuery['SortCodeId'];
        }

        if (!_.isNil($scope.search.code)) {
          searchQuery['code'] = {
            $like: '%' + $scope.search.code + '%'
          };
        } else {
          delete searchQuery['code'];
        }

        if (!_.isNil($scope.search.name)) {
          searchQuery['name'] = {
            $like: '%' + $scope.search.name + '%'
          };
        } else {
          delete searchQuery['name'];
        }
        refreshList()
      }

      // vvvvvvvvvvvvvvvvvv耗材項目編輯vvvvvvvvvvvvvvvvvv
      $scope.addSortCodeRow = function(){
        $scope.showSortCodes.push({name:"",editing:true,isNew:true})
        $scope.sortCodeEditing['g'] = true ;
      }
      $scope.cancelSortCodeRow = function(idx,isNew){
        $scope.sortCodeEditing[$scope.showSortCodes[idx].id] = false ;
        $scope.sortCodeEditing['g'] = false ;
        if (isNew){
          $scope.showSortCodes.splice(idx,1)
        }else{
          $scope.showSortCodes[idx].editing = false ;
        }
        getSortCodes();
      }
      $scope.applySortCode = function(id,name,isNew){
        $scope.sortCodeEditing[id] = false ;
        $scope.sortCodeEditing['g'] = false ;
        if ( isNew ){
          return addSortCode(name);
        }else{
          return $http.put('/SortCodes/' + id ,{name:name})
          .then(function(result){
            console.log("SortCode Edited",result);
            getSortCodes();
          })
        }
      }
      $scope.delSortCode = function(id){
        $http.get('/Supplies', {
                params: {
                    SortCodeId: id,
                    count:1
                },
                paramSerializer: '$httpParamSerializerJQLike'
            }).then(function(result){
              if (result.data.length == 0){
                if (window.confirm("確定刪除？")) {
                  $http.delete('/SortCodes/' + id)
                  .then(function(result){
                    console.log("SortCode Deleted",result);
                    getSortCodes();
                  })
                }
              }else{
                window.alert("已有耗材使用此分類，無法刪除！")
              }
            })

      }

      // ^^^^^^^^^^^^^^^^^^耗材項目編輯^^^^^^^^^^^^^^^^^^

      // vvvvvvvvvvvvvvvvvv耗材單位編輯vvvvvvvvvvvvvvvvvv
      $scope.addUnitCodeRow = function(){
        $scope.showUnitCodes.push({name:"",editing:true,isNew:true})
        $scope.unitCodeEditing['g'] = true ;
      }
      $scope.cancelUnitCodeRow = function(idx,isNew){
        $scope.unitCodeEditing[$scope.showUnitCodes[idx].id] = false ;
        $scope.unitCodeEditing['g'] = false ;
        if (isNew){
          $scope.showUnitCodes.splice(idx,1)
        }else{
          $scope.showUnitCodes[idx].editing = false ;
        }
        getUnitCodes();
      }
      $scope.applyUnitCode = function(id,name,isNew){
        $scope.unitCodeEditing[id] = false ;
        $scope.unitCodeEditing['g'] = false ;
        if ( isNew ){
          return addUnitCode(name);
        }else{
          return $http.put('/UnitCodes/' + id ,{name:name})
          .then(function(result){
            console.log("UnitCode Edited",result);
            getUnitCodes();
          })
        }
      }
      $scope.delUnitCode = function(id){
        $http.get('/Supplies', {
                params: {
                    UnitCodeId: id,
                    count:1
                },
                paramSerializer: '$httpParamSerializerJQLike'
            }).then(function(result){
              if (result.data.length == 0){
                if (window.confirm("確定刪除？")) {
                  $http.delete('/UnitCodes/' + id)
                  .then(function(result){
                    console.log("UnitCode Deleted",result);
                    getUnitCodes();
                  })
                }
              }else{
                window.alert("已有耗材使用此分類，無法刪除！")
              }
            })

      }
      // ^^^^^^^^^^^^^^^^^^耗材單位編輯^^^^^^^^^^^^^^^^^^

      $scope.refreshList = function(){
        refreshList();
      }



      function addSortCode(name){
        return $http.post('/SortCodes',{name:name})
        .then(function(result){
          console.log("SortCode Added",result);
          return getSortCodes();
        })
      }

      function addUnitCode(name){
        return $http.post('/UnitCodes',{name:name})
        .then(function(result){
          console.log("UnitCode Added",result);
          return getUnitCodes();
        })
      }

      function getSortCodes() {
        return $http.get('/SortCodes')
          .then(function(response) {
            $scope.showSortCodes = response.data
          })
      }

      function getUnitCodes() {
        return $http.get('/UnitCodes')
          .then(function(response) {
            $scope.showUnitCodes = response.data
          })
      }

      function getIsAuto() {
        return $http.get('json/isAuto.json')
          .then(function(response) {
            $scope.showIsAuto = response.data
          })
      }

      function refreshList() {

        $scope.dummyTable = getSuppliesList();
      }

      function getSuppliesList() {
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

            return $http.get('/Inventory/listByUser', {
                params: searchQuery,
                // paramSerializer: '$httpParamSerializerJQLike'
              })
              .then(function(response) {
                var range = contentRange.parse(response.headers('Content-Range'));
                var count = range.length;
                params.total(count);

                console.log('@@@@ getSuppliesList @@@@ response.data', response.data)
                var supplyList = [] ;
                for ( var i = 0 ; i < response.data.length ; i++ ){
                  var supply = response.data[i].Supply ;
                  supply.minimumAmount = response.data[i].minimumAmount ; // 要用各單位的minimumAmount
                  supply.suppliesInventoryId = response.data[i].id ;
                  supplyList.push(supply) ;
                }
                $scope.checkInList = supplyList;

                return supplyList; // 這邊的 return ，是直接給 ng-table 用的，因為 getData 就是它本身需要的功能
              })
              .catch(function(err) {
                console.log('### err', err)
                return [];
              })
          } // function
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
          return response.data[0]
        })
      }

      function updateMinAmount(minimumAmount, suppliesInventoryId){
        return $http.put('/SuppliesInventories/' + suppliesInventoryId,
        {
          minimumAmount: minimumAmount
        })
      }

      getSuppliesUser()
      .then(function(suserdata){
        if ( suppliesUserData = suserdata ){
          searchQuery['SuppliesUserId'] = suppliesUserData.id ;
        }else{
          window.alert("此使用者非耗材使用者！")
        }
        getSortCodes();
        getUnitCodes();
        getIsAuto();
        refreshList();
      })

});
