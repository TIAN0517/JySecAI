app.controller('epcr106Stat07Ctrl', function($scope, $state, $http, $controller, $q) {
  $scope.search = {
    mode: 'DAYS'
  };
  $scope.dateEnd = {};
  $scope.diagram = {
    threshold: 0,
    target: 0
  };
  $scope.title = '匯總報表';
  // $scope.getStat = getStat
  $scope.customParameter = {
    // url: 'templates/stat106/epcr105StatParameters40.html',
    url: 'templates/stat106/epcr106StatParameters02.html',
    hideSearch: true,
    searchFormat: format
  };
  $scope.exportUrl = '/stat/epcr106Stat07/exportCsv';


  init();

  function init() {} // init()

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
        // dateEnd = moment(search.dateBegin).add(1, 'MONTH').add(-1, 'DAY').startOf('DAY').utc().format();
        dateEnd = moment(search.dateBegin).add(1, 'MONTH').startOf('DAY').utc().format();
        break;
      case 'QUARTER':
        dateBegin = moment(search.dateBegin).quarter(search.quarter).startOf('QUARTER').utc().format();
        // dateEnd = moment(dateBegin).endOf('QUARTER').add(-1, 'DAY').utc().format();
        dateEnd = moment(dateBegin).add(1,'QUARTER').utc().format();
        break;
      case 'YEAR':
        dateBegin = moment(search.dateBegin).startOf('YEAR').utc().format();
        // dateEnd = moment(search.dateBegin).endOf('YEAR').utc().format();
        dateEnd = moment(search.dateBegin).add(1,'YEAR').utc().format();
        break;
    } // switch

    search.dateBegin = dateBegin;
    search.dateEnd = dateEnd;

    return search;
  } // format()

  // function getStat(search) {
  //   return $http.get('/stat/epcr105Stats40', {
  //       params: {
  //         dateBegin: search.dateBegin,
  //         dateEnd: moment(search.dateEnd).endOf('day').format(),
  //         // mode: search.mode,
  //         type: 'JSON',
  //         time: new Date().getTime()
  //       },
  //       paramSerializer: '$httpParamSerializerJQLike'
  //     })
  //     .then(function(response) {
  //       return response.data;
  //     });
  // } // getStat()

  $controller('epcr106StatBaseCtrl', {
    $scope: $scope
  });

});
