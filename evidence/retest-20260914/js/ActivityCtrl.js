CONTROLLERS.controller('ActivityCtrl', function ($scope, $http) {
    $scope.check = {
        user : '',
        actionType: null,
        targetEntity: null,
        dateBegin: moment().subtract(1, 'day').startOf('day').toDate(),
        dateEnd: moment().endOf('day').toDate()
    };
    $scope.actionTypes = ['read', 'update', 'login/out'];
    $scope.targetEntities = ['案件管理', '案件明細', '列印預覽','Temsis紀錄','登入紀錄','登出紀錄'];

    // $scope.datetimeConfig = {
    //     singleDatePicker: false,
    //     showDropdowns: true,
    //     timePicker: true,
    //     timePicker24Hour: true,
    //     locale: {
    //       format: 'YYYY-MM-DD HH:mm:ss',
    //       applyLabel: "確定",
    //       cancelLabel: '清空',
    //     },
        // minDate: tmpSDatetimeLimit ? moment(tmpSDatetimeLimit.checkPointTimeRecord.recordDatetime).toDate():null,
        // parentEl: '#addPointDatetime',
        // eventHandlers: {
          // 'apply.daterangepicker': function(ev, picker){
          // },
          // 'cancel.daterangepicker': function(ev, picker){
          //  $scope.checkPointTimeModal.addPointDatetime = null;
          // },
          // 'show.daterangepicker': function(ev, picker){
          //   console.log(ev)
          //   console.log(picker)
          // }
        // }
    // }

    $scope.Search = activitySearch;
    $scope.clearSearch = function () {
        $scope.check = {
            user : '',
            actionType: null,
            targetEntity: null,
            dateBegin: '',
            dateEnd: ''
        };
        activitySearch();
    };
    
    function activitySearch() {
        const params = {}
        params.user = $scope.check.user;
        params.actionType = $scope.check.actionType;
        params.targetEntity = $scope.check.targetEntity;
        params.dateBegin = $scope.check.dateBegin;
        params.dateEnd = $scope.check.dateEnd;

        return $http.get('/Activities/search', { params })
              .then(function (response) {
                  $scope.dataFromBackend = response.data;
              })
              .catch(function (error) {
                  console.error('Error fetching data:', error);
              });
    };
});

