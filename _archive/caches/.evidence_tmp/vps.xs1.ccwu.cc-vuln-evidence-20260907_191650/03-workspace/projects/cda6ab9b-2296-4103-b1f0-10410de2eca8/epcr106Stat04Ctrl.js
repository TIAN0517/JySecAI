app.controller('epcr106Stat04Ctrl', function($scope, $state, $http, $controller, $q) {
  $scope.search = {
    mode: 'DAYS'
  };
  $scope.dateEnd = {};
  $scope.diagram = {
    threshold: 0,
    target: 0
  };
  $scope.title = '各大隊施打靜脈輸液品質指標';
  $scope.getStat = getStat
  $scope.customParameter = {
    // url: 'templates/stat106/epcr106StatParametersMonthAndWeek.html'
    url: 'templates/stat106/epcr106StatParameters02.html',
    searchFormat: format
  };
  $scope.exportUrl = '/stat/epcr106Stats04/exportCsv';


  init();

  function init() {} // init()

  function getStat(search) {
    search = format(search);
    // var dateBegin = null;
    // var dateEnd = null;
    //
    // switch (search.mode) {
    //   case 'DAYS':
    //     dateBegin = moment(search.dateBegin).startOf('DAY').utc().format();
    //     dateEnd = moment(search.dateEnd).endOf('DAY').utc().format();
    //     break;
    //   case 'MONTH':
    //     dateBegin = moment(search.dateBegin).startOf('DAY').utc().format();
    //     dateEnd = moment(search.dateBegin).add(1, 'MONTH').add(-1, 'DAY').startOf('DAY').utc().format();
    //     break;
    //   case 'QUARTER':
    //     dateBegin = moment(search.dateBegin).quarter(search.quarter).startOf('QUARTER').utc().format();
    //     dateEnd = moment(dateBegin).endOf('QUARTER').add(-1, 'DAY').utc().format();
    //     break;
    //   case 'YEAR':
    //     dateBegin = moment(search.dateBegin).startOf('YEAR').utc().format();
    //     dateEnd = moment(search.dateBegin).endOf('YEAR').utc().format();
    //     break;
    // } // switch

    return $http.get('/stat/epcr106Stats04', {
        params: {
          dateBegin: search.dateBegin,
          dateEnd: search.dateEnd,
          time: new Date().getTime()
        },
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(response) {
        return response.data;
      });
  } // getStat()

  function format(search) {
    var dateBegin = null;
    var dateEnd = null;

    switch (search.mode) {
      case 'DAYS':
        dateBegin = moment(search.dateBegin).startOf('DAY').utc().format();
        dateEnd = moment(search.dateEnd).endOf('DAY').utc().format();
        break;
      case 'MONTH':
        dateBegin = moment(search.dateBegin).startOf('DAY').utc().format();
        dateEnd = moment(search.dateBegin).add(1, 'MONTH').add(-1, 'DAY').startOf('DAY').utc().format();
        break;
      case 'QUARTER':
        dateBegin = moment(search.dateBegin).quarter(search.quarter).startOf('QUARTER').utc().format();
        dateEnd = moment(dateBegin).endOf('QUARTER').add(-1, 'DAY').utc().format();
        break;
      case 'YEAR':
        dateBegin = moment(search.dateBegin).startOf('YEAR').utc().format();
        dateEnd = moment(search.dateBegin).endOf('YEAR').utc().format();
        break;
    } // switch

    search.dateBegin = dateBegin;
    search.dateEnd = dateEnd;

    return search;
  } // format()

  $controller('epcr106StatBaseCtrl', {
    $scope: $scope
  });

});
