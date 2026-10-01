app.controller('Stat03Ctrl', function($scope, $state, $http, $controller) {
  $scope.search = {
    mode: 'DAYS'
  };
  $scope.dateEnd = {};
  $scope.diagram = {
    threshold: 0,
    target: 0
  };
  $scope.title = '匯總報表';
  $scope.customParameter = {
    url: 'stat/epcr106/templates/statParameters03.html',
    hideSearch: true,
    searchFormat: format
  };
  $scope.exportUrl = '/stat/stat03/exportCsv';


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
        dateEnd = moment(search.dateBegin).add(1, 'MONTH').startOf('DAY').utc().format();
        break;
      case 'QUARTER':
        dateBegin = moment(search.dateBegin).quarter(search.quarter).startOf('QUARTER').utc().format();
        dateEnd = moment(dateBegin).add(1,'QUARTER').utc().format();
        break;
      case 'YEAR':
        dateBegin = moment(search.dateBegin).startOf('YEAR').utc().format();
        dateEnd = moment(search.dateBegin).add(1,'YEAR').utc().format();
        break;
    } // switch

    search.dateBegin = dateBegin;
    search.dateEnd = dateEnd;

    return search;
  } // format()

  $controller('StatBaseCtrl', {
    $scope: $scope
  });

});

