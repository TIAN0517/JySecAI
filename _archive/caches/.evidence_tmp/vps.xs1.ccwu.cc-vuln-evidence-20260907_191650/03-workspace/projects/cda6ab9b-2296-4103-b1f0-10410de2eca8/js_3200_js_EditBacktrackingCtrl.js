/* 新增回溯 */
CONTROLLERS.controller('EditBacktrackingCtrl', function($scope, $state, $window, $timeout,
    $http, AlertService, AuthService, $stateParams, PcrQuestionService, $q) {

    var pcrBundleUuid = $stateParams.pcrBundleUuid;
    var currentBundle;

    var vm = {};
    $scope.vm = vm;
    $scope.params = { };
    $scope.currentCategory;

    function setUpForm(pcrBundle){
        var categoryId = pcrBundle.PcrCategoryId;
    	return PcrQuestionService.getJson(categoryId)
    	.then(function(results){
    		vm.model = fillModel(pcrBundle)
    		vm.fields = results;
    		// 讓vm.fields 可以存取到 model
            angular.forEach(vm.fields, function(item, index) {
                item['model'] = vm.model;
            });
        });
    }

    function fillModel(pcrBundle) {
        var pcrRecords = pcrBundle.PcrRecords;
        var model = {}

        angular.forEach(pcrRecords, function(record) {
            var keyName = record.PcrQuestion.code;
            var pcrQuestionTypeId = record.PcrQuestion.PcrQuestionTypeId;
            var pcrAnswerRecords = record.PcrAnswerRecords;
            switch (pcrQuestionTypeId) {
                // Date / Datetime
                case 1:
                case 6:
                    angular.forEach(pcrAnswerRecords, function(ansRecord) {
                        if (ansRecord.freeTypingValue) {
                            model[keyName] = moment(ansRecord.freeTypingValue).toDate();
                        }
                    });
                    break;
                case 2:
                case 7:
                    angular.forEach(pcrAnswerRecords, function(ansRecord) {
                        // console.log('case 2:', ansRecord)
                        model[keyName] = ansRecord.PcrAnswer.code;
                    });
                    break;
                case 3:
                    angular.forEach(pcrAnswerRecords, function(ansRecord) {
                        model[keyName] = parseInt(ansRecord.freeTypingValue);
                    });
                    break;
                case 4:
                    angular.forEach(pcrAnswerRecords, function(ansRecord) {
                        //console.log('case 4:', ansRecord)
                        model[keyName] = ansRecord.freeTypingValue;
                    });
                    break;
                case 5:
                    angular.forEach(pcrAnswerRecords, function(ansRecord) {
                        //console.log('case 5:', ansRecord)
                        // var visitAnswer = [];
                        //console.log("multiCheckbox", item)
                        //console.log("visitBundle", visitBundle)
                        if (model[keyName]) {
                            model[keyName].push(ansRecord.PcrAnswer.code)
                        } else {
                            model[keyName] = [];
                            model[keyName].push(ansRecord.PcrAnswer.code)
                        }

                    })
                    break;
            }
        })
        return model;
    }


    function generateBundle(fields, model, VERSION, categoryId, dispatchId, hospitalUuid) {
        console.log("fields", fields)
        console.log("model", model)

        var pcrBundle = {};
        pcrBundle['PcrVersionId'] = VERSION;
        pcrBundle['PcrRecords'] = []
        pcrBundle['PcrCategoryId'] = categoryId
        pcrBundle['DispatchId'] = dispatchId;
        pcrBundle['isComplete'] = checkIfCompleted(fields, model);
        pcrBundle['HospitalUuid'] = hospitalUuid;

        angular.forEach(model, function(item, key) {
            var pcrRecord = {};
            var pcrAnswer = {};

            var vmFields = _.find(fields, { 'key': key });
            pcrRecord['PcrQuestionId'] = vmFields.data.QuestionSN;
            pcrRecord['PcrAnswerRecords'] = []

            switch (vmFields.type) {
                case 'multiCheckbox':
                    angular.forEach(model[key], function(item, key) {
                        var visitAnswer = {};
                        var box = _.find(vmFields.templateOptions.options, { 'value': item });
                        pcrAnswer['PcrAnswerId'] = box.answerID
                        pcrRecord.PcrAnswerRecords.push(pcrAnswer)
                    })
                    break;
                case 'input':
                case 'datetimepicker':
                    pcrAnswer['freeTypingValue'] = model[key]
                    pcrAnswer['PcrAnswerId'] = vmFields.data.answerSN
                    pcrRecord.PcrAnswerRecords.push(pcrAnswer)

                    break;
                case 'radio':
                case 'select':
                    var vmAnswer = _.find(vmFields.templateOptions.options, { 'value': item });
                    pcrAnswer['PcrAnswerId'] = vmAnswer.answerID
                    pcrRecord.PcrAnswerRecords.push(pcrAnswer)
                    break;
            }
            console.log("pcrRecord", pcrRecord)
            pcrBundle.PcrRecords.push(pcrRecord)
        })
        return pcrBundle;
    }

    function checkIfCompleted(fields, models) {
        var isComplete = true;
        angular.forEach(fields, function(question, idx) {
            var key = question.key;
            if (_.isNil(question.templateOptions.disabled) || question.templateOptions.disabled == false) {
                console.log(key, _.isNil(models[key]));
                if (_.isNil(models[key])) {
                    isComplete = false;
                }
            }
        });
        return isComplete;
    }


    function getPcrBundle(pcrBundleUuid){
        return $http.get('/PcrBundles/'+pcrBundleUuid)
        .then(function(response) {
            return response.data;
        })
    }

    function saveBundle(data, pcrBundleUuid){
        return $http.post('/PcrBundles/updateTo/'+pcrBundleUuid, data)
            .then(function(response) {
                return response.data;
            });
    }

    function save(){
        var versionId = currentBundle.PcrVersionId;
        var categoryId = currentBundle.PcrCategoryId;
        var dispatchId = currentBundle.Dispatch.id;
        var hospitalUuid = currentBundle.HospitalUuid;
        var bundle = generateBundle(vm.fields, vm.model, versionId, categoryId, dispatchId, hospitalUuid)
        return saveBundle(bundle, pcrBundleUuid)
        .then(function(){
            alert('回溯已儲存');
            $window.close();
        })
        .catch(function(error){
            console.log(error);
            alert('無法儲存回溯');
        });
    }

    function cancel(){
        $window.close();
    }

    function createNew(){
        var result = confirm('重新填寫時，目前的回溯內容將會被取代。是否確定?');
        if(result){
            $state.go('backtracking', {
                dispatchId: currentBundle.Dispatch.id,
                hospitalUuid: currentBundle.HospitalUuid
            })
        }
    }

    $scope.save = save;
    $scope.cancel = cancel;
    $scope.createNew = createNew;

    function init(){
        var anyPageBusyDefer = $q.defer();
        $scope.anyPageBusy = anyPageBusyDefer.promise;
    	return getPcrBundle(pcrBundleUuid)
        .then(function(result){
            $scope.currentCategory = result.PcrCategory;
            currentBundle = result;
            $scope.currentBundle = currentBundle;
            setUpForm(currentBundle);
        })
        .finally(function(){
            anyPageBusyDefer.resolve();
        })
    }

    init();

});

