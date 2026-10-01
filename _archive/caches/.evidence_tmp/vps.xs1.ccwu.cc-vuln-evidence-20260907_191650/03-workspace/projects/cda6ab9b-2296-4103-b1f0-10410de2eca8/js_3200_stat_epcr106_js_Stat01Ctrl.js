app.controller('Stat01Ctrl', function($scope, $state, $controller, $http) {
    $scope.search = {
        mode: 'DAYS',
        formVersionParam: {
            text: '目前版本(>=5)',
            minFormVersionId: 5
        },
        hasBackTracking: true
    };
    $scope.dateEnd = {};
    $scope.title = '回溯報表';
    $scope.customParameter = {

        url: 'stat/epcr106/templates/statParameters01.html',
        hideSearch: true,
        searchFormat: format,
        versionParams:[
            {
                text: '目前版本(>=5)',
                minFormVersionId: 5
            },
            {
                text: '2020/01/31改版前(<=4)',
                maxFormVersionId: 4
            }
        ]
    };
    $scope.exportUrl = '/stat/stat01/exportCsv';

    init();

    function init() {
        getFormCategory()
        .then(function(results){
            $scope.customParameter['FormCategoryList'] = results;
        })
        .catch(function(error){
            console.log(error);
            alert('無法取得回溯題目分類');
        });
    } // init()

    function getFormCategory(){
        return $http.get('/FormCategories')
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