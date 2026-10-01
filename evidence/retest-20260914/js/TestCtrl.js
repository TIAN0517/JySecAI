CONTROLLERS.controller('TestCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, EPCRServices, $window, EPCRServices, AuthService) {
    $scope.add = {};
    $scope.ambItems = {};
    $scope.isOfficialCase = false;
    var ambsData = {};
    var ambsList = [];
    var ambsCode = "";

    var addInit = function(id) {
        return $http.get('/Ambs', {
                params: { 'AmbCategoryId': id },
                paramSerializer: '$httpParamSerializerJQLike'
            })
            .then(function(response) {
                $scope.ambsQuestions = response.data;
                return $http.get('json/ambAnswer.json')
            })
            .then(function(response) {
                $scope.answerList = response.data
            })
    }

    var addModal = $modal({
        scope: $scope,
        templateUrl: 'templates/modal/ambAdd.html',
        animation: 'no-animation',
        placement: 'center',
        backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
        show: false,
        //onHide: refreshList
    });

    $scope.showAddModal = function(id, code) {
        addInit(id);
        ambsCode = code;
        addModal.$promise.then(addModal.show);
    }

    function initData() {
        return $q.all([
            setSexs(),
            setAwarnesses(),
            setBreaths(),
            setSymptoms(),
            setAmbCategories(),
            setAmbulances(),
            setDispatchTypes()
        ])
    } // initData()
    
    function setSexs() {
        return $http.get('/Sexs/')
            .then(function (response) {
                $scope.showSex = response.data;
            });
    } // setSexs()
    function setAwarnesses() {
        return $http.get('/Awarenesses/')
            .then(function (response) {
                $scope.showAwareness = _.keyBy(response.data, 'id');
            });
    } // setAwarnesses()
    function setBreaths() {
        return $http.get('/Breaths/')
            .then(function (response) {
                $scope.showBreath = _.keyBy(response.data, 'id');
            });
    } // setBreaths()
    function setSymptoms() {
        return $http.get('/Symptoms/')
            .then(function (response) {
                $scope.showSymptom = _.keyBy(response.data, 'id');
            });
    } // setSymptoms()
    function setAmbCategories() {
        return $http.get('/AmbCategories')
            .then(function (response) {
                $scope.showAmbCategory = _.keyBy(response.data, 'id');
            });
    } // setAmbCategories()
    function setAmbulances() {
        return $http.get('/Ambulances', {
            params: {
                count: 1000,
                disabled: false,
		sort: 'code'
            },
            paramSerializer: '$httpParamSerializerJQLike'
        })
            .then(function (response) {
		$scope.showAmbulances = _.keyBy(response.data, 'code');
            });
    } // setAmbulances()
    function setDispatchTypes() {
        return $http.get('/DispatchType/')
        .then(function (response) {
            $scope.showDispatchTypes = response.data;
        });
    } // setDispatchTypes()

    initData();

    $scope.addAmbs = function(id) {
        console.log("id", id)
        if (!_.isNil(id)) {
            if(_.findIndex(ambsList, { id: id })==-1){
                var data = { 'id': id };
                ambsList.push(data)
                $scope.tableParams = tableInit()
            }
        }

    }

    $scope.addCase = function() {
        var dispatchedAt = new Date();
        var add = angular.copy($scope.add);
        add['dispatchedAt'] = dispatchedAt;
        add['age'] = $scope.add['age']*12;
        add['recordUuid'] = add['recordUuid'] ? add['recordUuid'] : ("Test" + moment(dispatchedAt).format("YYMMDDHHmmss"));
        add['isSimulation'] = !$scope.isOfficialCase;
        add['isMCI'] = false;
        add['DispatchTypeId'] = $scope.DispatchTypeId;
        console.log("addInforamtion:", add);
        if (AuthService.checkPerm('EPCR_OFFICIALCASE')){
          add['force'] = true;
        }
        add['ambs'] = [];
        for(var Abb in ambsData){
            add['ambs'].push({
                Abb: Abb,
                issuesCode: ambsData[Abb]
            })
        }
        $http.post('/CaseRecords/create', add)
            .then(function(response) {
                console.log('Add success!')
                EPCRServices.successAlert('通知！', '建立成功');
                // Reset data
                $scope.add={};
                add = {};
                ambsList=[]
                $scope.tableParams= tableInit();
                $scope.AmbCategoryId='';
                $scope.ambItems = {};
                ambsData = {};
            })
            .catch(function(err) {
                console.log('Add fails =', err)
                if (!_.isEmpty(err.data.errors)) {
                    EPCRServices.failAlert('錯誤！', err.data.errors[0], null);
                } else {
                    EPCRServices.failAlert('錯誤！', '建立失敗！', null);
                } // if
            })
    }

    $scope.toAdd = function() {
        var issuesCode = "";
        angular.forEach($scope.ambsQuestions, function(value) {
            if ($scope.ambItems[value.id]) {
                issuesCode += $scope.ambItems[value.id]
            } else {
                issuesCode += ' ';
            }
        })
        ambsData[ambsCode] = issuesCode

        addModal.$promise.then(addModal.hide)
    }

    function tableInit() {
        return new NgTableParams({
            page: 1, // show first page
            count: 10, // count per page,
            sorting: { createdAt: 'desc' }
        }, {
            filterDelay: 300,
            getData: function(params) {
                return ambsList;
            }
        })
    }
});
