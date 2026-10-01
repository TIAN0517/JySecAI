CONTROLLERS.controller('SuppliesRequestDetailPrintCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices, AuthService, $stateParams) {


      console.log("$stateParams", $stateParams)
      var param = $stateParams

      function refreshList(param) {
        $scope.requestPrintTable = getRequestMasters(param);
      }

      function getRequestMasters(param) {
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
            console.log('param=',param)
            param.time = new Date().getTime();
            param.sort = sorting;
            param.count = limit;
            param.offset = skip;
            // $scope.checkboxes.checked = false;

            console.log(param)

            return $http.get('/SuppliesRequests', {
                params: param,
                paramSerializer: '$httpParamSerializerJQLike'
              })
              .then(function(response) {
                var range = contentRange.parse(response.headers('Content-Range'));
                var count = range.length;
                params.total(count);

                console.log('@@@@ getRequestMasters @@@@ response.data', response.data)
                $scope.checkInList = response.data;

                return response.data[0].SuppliesRequestDetails; // 這邊的 return ，是直接給 ng-table 用的，因為 getData 就是它本身需要的功能
              })
              .catch(function(err) {
                console.log('### err', err)
                return [];
              })
          } // function
        })
      }



      refreshList(param);
});
