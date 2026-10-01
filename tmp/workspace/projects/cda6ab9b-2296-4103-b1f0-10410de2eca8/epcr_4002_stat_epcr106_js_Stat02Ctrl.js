// 送醫紀錄報表
app.controller('Stat02Ctrl', function($scope, $state, $controller, $http) {
    $scope.search = {
        mode: 'DAYS',
    };
    $scope.dateEnd = {};
    $scope.title = '送醫紀錄報表';
    $scope.customParameter = {

        url: 'stat/epcr106/templates/statParameters02.html',
        hideSearch: true,
        searchFormat: format,
    };
    $scope.exportUrl = '/stat/stat01/exportCsv';

    init();

    function init() {
        getDispatchType()
        .then(function(results){
            $scope.customParameter['DispatchTypeList'] = results;
        })
        .catch(function(error){
            console.log(error);
            alert('無法取得派遣類型');
        });
    } // init()

    function getDispatchType(){
        return $http.get('/DispatchTypes')
        .then(function(response){
            return response.data;
        })
    }

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

    $controller('StatBaseCtrl', {
        $scope: $scope
    });

});