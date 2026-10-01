CONTROLLERS.controller('MciListCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices, $window) {

    $scope.openMciDetail = function(CaseRecordId) {
        var openWindow = $window.open('/#/mciDetail/' + CaseRecordId, '_blank')
    }

    // 大傷外科警戒 相關
    var mciWarningModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/mciWarningModal.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
        show: false
    })

    function initMciWarningModal(){
        $scope.mci = {
            hospitals: {},
            announce: ""
        }
    }


    function getHospitalList(){
        return $http.get('/hospitals?sort=name')
        .then(function(response){
            return response.data;
        })
    }

    function setUpHospitalList(){
        return getHospitalList()
        .then(function(results){
            $scope.HospitalList = results;
        })
    }

    function checkAll(value){
        for(var idx in $scope.HospitalList){
            var hospital = $scope.HospitalList[idx];
            $scope.mci.hospitals[hospital.uuid] = value
        }
    }

    function sendMciAnnounce(mciCaseRecordUuid, announce, hospitals){
        var hospitalList = [];
        for(var hospitalUuid in hospitals){
            if(hospitals[hospitalUuid]){
                hospitalList.push(hospitalUuid);
            }
        }

        return $http.post('/MciAnnounces/create/'+mciCaseRecordUuid,{
            content: announce,
            hospitalList: hospitalList
        })
        .then(function(response){
            return response.data;
        });
    }

    $scope.checkAll = checkAll;
    $scope.targetMciCaseRecordUuid = null;

    $scope.showMciWarningMoadl = function(mciCaseRecordUuid) {
        initMciWarningModal();
        $scope.targetMciCaseRecordUuid = mciCaseRecordUuid
        mciWarningModal.$promise.then(mciWarningModal.show);
    }

    $scope.sendMciAnnounce = function(mciCaseRecordUuid, announce, hospitals){
        return sendMciAnnounce(mciCaseRecordUuid, announce, hospitals)
        .then(function(){
            mciWarningModal.$promise.then(mciWarningModal.hide);
        })
        .catch(function(error){
            console.log(error);
            alert('無法送出外科警戒通知');
        });
    }

    // 大傷外科警戒 相關 end

    $scope.customSearch = function(search) {
        searchParams = {}
        if (_.isNil(search)) {
            return EPCRServices.failAlert('錯誤！', '沒有輸入查詢條件！', null)
        }

        if ((search.dateBegin && _.isNil(search.dateEnd)) || (_.isNil(search.dateBegin) && search.dateEnd)) {
            return EPCRServices.failAlert('錯誤！', '請輸入手術日期的起迄區間！', null)
        }
        if (search.dateBegin && search.dateEnd) {
            if (search.dateBegin > search.dateEnd) {
                return EPCRServices.failAlert('警告！', '起迄時間錯誤！', null)
            }

            var dateBegin = moment(search.dateBegin).startOf('day').toDate();
            var dateEnd = moment(search.dateEnd).endOf('day').toDate();
            searchParams['createdAt'] = {
                $between: [dateBegin, dateEnd]
            }
        }

        if (search['uuid'] != '' && !_.isNil(search['uuid'])) {
            searchParams['uuid'] = search['uuid']
        }
        $scope.tableParams = tableInit();
    }
    $scope.clearCondition = function() {
        clearAndTableInit()
    }
    $scope.refreshList = function() {
        clearAndTableInit()
    }

    $scope.validateForm = function(mci){
        var count = 0;
        for(var key in mci.hospitals){
            if(mci.hospitals[key]){
                count++;
            }
        }
        if(count==0){
            return true;
        }else if(_.isEmpty(mci.announce)){
            return true;
        }
        return false;
    }


    function clearAndTableInit() {
        $scope.search = {}
        searchParams = {};
        $scope.tableParams = tableInit();
    }


    // NgTable start
    var searchParams = {}
    var defaultSorting = { createdAt: 'desc' };
    var responseList = []

    function tableInit() {
        return new NgTableParams({
            page: 1, // show first page
            count: 10, // count per page,
            sorting: defaultSorting
        }, {
            filterDelay: 300,
            getData: function(params) {
                var deferred = $q.defer();
                $scope.anyPageBusy = deferred.promise;

                var url = params.url();
                var limit = url.count,
                    skip = url.count * (url.page - 1);
                var sortString;
                // 如果使用 epilogue 免費 api sort需要做調整
                // 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
                // sortString = params.sorting();
                for (var key in params.sorting()) {
                    if (params.sorting()[key] == 'desc') {
                        sortString = '-' + key;
                    } else {
                        sortString = key;
                    }
                }

                var conditions = {
                    // time 防止 cache
                    time: new Date().getTime(),
                    sort: sortString,
                    offset: skip,
                    count: limit
                }

                if (!_.isEmpty(searchParams)) {
                    for (var key in searchParams) {
                        conditions[key] = searchParams[key];
                    }
                } else {
                    var dateEnd = new Date();
                    var dateBegin = moment(dateEnd).subtract(24, 'hours').toDate();
                    conditions['createdAt'] = {
                        $between: [dateBegin, dateEnd]
                    }
                }

                return $http.get('/MciCaseRecords', {
                        params: conditions,
                        paramSerializer: '$httpParamSerializerJQLike'
                    })
                    .then(function(response) {
                        var range = contentRange.parse(response.headers('Content-Range'));
                        var count = range.length;
                        params.total(count);

                        deferred.resolve()
                        return response.data
                    })
                    .catch(function(err) {
                        deferred.resolve();
                        console.log('tableInit err =', err)
                    })

            }
        })
    }
    $scope.tableParams = tableInit()
    setUpHospitalList();

});