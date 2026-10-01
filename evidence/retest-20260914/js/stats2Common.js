app.directive('statExport', function() {
  return {
    restrict: 'E',
    replace: true,
    scope: {
      exportUrl: '=',
      search: '=',
      inValid: '=',
      customParameter: '='
    },
    template:
      // '<a href="{{exportUrl}}?{{queryString()}}" class="btn btn-default" ng-init="init();">匯出</a>',
      '<button ng-click="exportStat();" class="btn btn-default" ng-disabled="inValid" ng-init="init();">匯出</button>',
    controller: function($scope, $window, $httpParamSerializer, AuthService, EPCRServices) {
      $scope.exportStat = exportStat;
      $scope.init = init;

      function init() {} // init()
      function exportStat() {
        return Promise.resolve()
          .then(function() {
            var search = {};
            if ($scope.customParameter && $scope.customParameter.searchFormat) search = $scope.customParameter.searchFormat($scope.search);
            else search = $scope.search;
            // $scope.search.token = AuthService.getToken();
            search.token = AuthService.getToken();
            if(AuthService.isTokenExpired(search.token)){
              return AuthService.refreshToken()
              .then(function(){
                search.token = AuthService.getToken();
                return search;
              })
            }
            return search;
          })
          .then(function(search){
            var queryString = $httpParamSerializer(search);

            queryString = (queryString.length > 0 ? '?' : '') + queryString;
            $window.location.href = $scope.exportUrl + queryString;
            return EPCRServices.successAlert('訊息', '準備下載', 5);
          })
          .catch(function(error) {
            console.log(error);
            // EPCRServices.failAlert('錯誤', '取得統計結果時發生錯誤');
            alert('取得統計結果時發生錯誤');
          })
          .finally(function() {
            $scope.search.dateBegin = null;
            $scope.search.dateEnd = null;
          });
      } // exportStat()
    },
    link: function(scope, element, attrs) {}
  };
});

app.directive('statParameters', function($datepicker, $http) {
  var myDatepicker;
  var templatePromise = $http.get('templates/stat106/statParameters.html')
    .then(function(response) {
      return response.data;
    });

  return {
    restrict: 'EA',
    replace: true,
    scope: {
      title: '=',
      search: '=', //Two-way data binding
      diagram: '=',
      searchFunc: '&',
      detailUrl: '=',
      exportUrl: '=',
      customParameter: '='
    },
    templateUrl: 'templates/stat106/statParameters.html',
    controller: function($scope, $element, $compile, $state) {
      // var controller = this;
      $scope.calendarModes = {
        'DAY': '日報',
        'MONTH': '月報',
        'QUARTER': '季報',
        'YEAR': '年報',
        // 'MTOM': '同月比',
        // 'QTOQ': '同季比'
      }
      $scope.calendar = {};

      function formCheck(search) {
        if (search.dateBegin && search.dateEnd) {
          return moment(search.dateBegin).isSameOrBefore(moment(search.dateEnd));
        } else {
          return false
        }
      }

      $scope.SetDateBegin = function(mode, sourceDate) {
        $scope.search.dateBegin = SetDatePoint(mode, sourceDate, true);
        // console.log($scope.search.dateBegin);
      };

      $scope.SetDateEnd = function(mode, sourceDate) {
        $scope.search.dateEnd = SetDatePoint(mode, sourceDate, false);
        // console.log($scope.search.dateEnd);
      };

      // 依據模式設定時間為 選取時間 開始端點 或 結束端點
      function SetDatePoint(mode, sourceDate, isStart) {
        // console.log(mode, sourceDate);
        var result = sourceDate;
        if (sourceDate) {
          switch (mode) {
            case 'DAY': // 日報
              if (isStart)
                result = moment(sourceDate).startOf('day').format();
              else
                result = moment(sourceDate).endOf('day').format();
              break;
            case 'MONTH': // 月報
              if (isStart)
                result = moment(sourceDate).startOf('month').format();
              else
                result = moment(sourceDate).endOf('month').format()
              break;
            case 'QUARTER': // 季報
              if (isStart)
                result = moment(sourceDate).startOf('quarter').format();
              else
                result = moment(sourceDate).endOf('quarter').format()
              break;
            case 'YEAR': // 年報
            case 'MTOM':
            case 'QTOQ':
              if (isStart)
                result = moment(sourceDate).startOf('year').format();
              else
                result = moment(sourceDate).endOf('year').format()
              break;
            case 'WEEK':
              if (isStart) result = moment(sourceDate).day('MONDAY').startOf('DAY').format();
              else result = moment(sourceDate).day('MONDAY').add(6, 'DAY').endOf('DAY').format();
              break;
          } // switch
        } // if
        // console.log(result);
        return result;
      } // SetDatePoint

      $scope.goSearch = function(search) {
        // 自動時間區間
        if (search.dateBegin && !search.dateEnd &&
          // 同月即同季比不適用此邏輯
          !(search.mode == 'MTOM' || search.mode == 'QTOQ')) {
          search.dateEnd = SetDatePoint(search.mode, search.dateBegin);
        } // if

        if (formCheck(search)) {
          $scope.searchFunc(search);
        } else {
          alert('日期錯誤');
        }
      }

      $scope.changeMode = function(mode) {
        switch (mode) {
          case 'DAY': //日報
            $scope.calendar.startView = 0;
            $scope.calendar.minView = 0;
            break;
          case 'MONTH': //月報
            $scope.calendar.startView = 1;
            $scope.calendar.minView = 1;
            break;
          case 'YEAR': //年報
          case 'QTOQ': //同季比
          case 'MTOM': //同月比
            $scope.calendar.startView = 2;
            $scope.calendar.minView = 2;
            break;
          case 'QUARTER': //季報
            $scope.calendar.startView = 1;
            $scope.calendar.minView = 1;
            break;
        }

        templatePromise
          .then(function(template) {
            var contents = $compile(template)($scope);
            $element.html(contents);
          })
      }

      $scope.changeMode($scope.search.mode);

      $scope.stringify = function(json) {
        return JSON.stringify(json);
      }

    },
    link: function($scope, $element, iAttrs, controller) {

    }
  };
});

app.directive('statChooser', function($datepicker, $http) {
  var myDatepicker;
  var templatePromise = $http.get('templates/stat106/statChooser.html')
    .then(function(response) {
      return response.data;
    });

  return {
    restrict: 'EA',
    scope: {
      statList: '='
    },
    controller: function($scope, $element, $compile, $state) {

      $scope.changeStat = function(stat) {
        if (stat) {
          $state.go(stat.state);
        }
      }

      templatePromise
        .then(function(template) {
          var contents = $compile(template)($scope);
          $element.html(contents);
        })
    },
    link: function($scope, $element, iAttrs, controller) {

    }
  };
});


app.filter('rocDateFilter', ['$filter', function($filter) {
  return function(date) {
    var convertedDate = moment(date);
    var rocYear = convertedDate.year() - 1911;
    return $filter('date')(convertedDate.toDate(), rocYear + 'MMdd HH:mm:ss');
  }

}]);
app.filter('birthdayFilter', [function() {
  return function(date) {
    var theDate = moment(date);
    var now = moment();

    return now.diff(theDate, 'years');
  }

}]);
app.filter('sexFilter', [function() {
  return function(sex) {
    if (sex) {
      switch (sex) {
        case 1:
          return '男';
        case 2:
          return '女';
        default:
          return '未知';
      }
    } else {
      return '未知';
    }
  }

}]);
