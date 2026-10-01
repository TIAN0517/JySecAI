/* 新增回溯 */
CONTROLLERS.controller('BacktrackingCtrl', function($scope, $state, $window, $timeout,
    $http, AlertService, AuthService, $stateParams, PcrQuestionService, $q) {

    var dispatchId = $stateParams.dispatchId;
    var vm = {};
    $scope.vm = vm;
    $scope.params = { };
    var currentCategoryId;
    var currentDispatch;

    function getDispatch(dispatchId){
        return $http.get('/Dispatches/'+dispatchId)
        .then(function(response){
            return response.data;
        })
    }

    function setUpDispatch(dispatchId){
        return getDispatch(dispatchId)
        .then(function(result){
            currentDispatch = result;
            $scope.currentDispatch = currentDispatch;
        });
    }

    function getCategory(){
        return $http.get('/PcrCategories')
        .then(function(response) {
        	return response.data;
        })
    }

    function setUpCategory(){
    	return getCategory()
    	.then(function(results){
            $scope.showPcrCategories = _.keyBy(results, 'id')
        })
    }

    function setUpForm(categoryId){
        currentCategoryId = categoryId;
    	return PcrQuestionService.getJson(categoryId)
    	.then(function(results){
    		vm.model = {};
    		vm.fields = results;
    		// 讓vm.fields 可以存取到 model
            angular.forEach(vm.fields, function(item, index) {
                item['model'] = vm.model;
            });
        });
    }

    function generateBundle(fields, model, VERSION, categoryId, dispatchId, hospitalUuid) {
        var pcrBundle = {};
        pcrBundle['PcrVersionId'] = VERSION;
        pcrBundle['PcrRecords'] = []
        pcrBundle['PcrCategoryId'] = categoryId
        pcrBundle['DispatchId'] = dispatchId;
        pcrBundle['isComplete'] = checkIfCompleted(fields, model);
        pcrBundle['PcrBundleUuid'] = null;
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


    $scope.createBacktracking = function(categoryId, prevCategoryId){
    	var anyPageBusyDefer = $q.defer();
    	$scope.anyPageBusy = anyPageBusyDefer.promise;
    	var task;
    	if(_.isEmpty(vm.model)==false){
    		var result = confirm("更換類型將清除之前填寫的內容，是否確定？")
    		if(result){
    			task = setUpForm(categoryId);
    		}else{
    			$scope.params.pcrCategoryId = parseInt(prevCategoryId);
    			task = $q.when();
    		}
    	}else{
    		task = setUpForm(categoryId);
    	}

    	task.finally(function(){
    		anyPageBusyDefer.resolve();
    	})
    }

    function saveBundle(data){
        return $http.post('/PcrBundles/addTo/'+dispatchId, data)
            .then(function(response) {
                return response.data;
            });
    }

    function save(){
        return PcrQuestionService.getVersion()
        .then(function(currentVersion){
            var hospitalUuid = currentDispatch.HospitalUuid;
            var bundle = generateBundle(vm.fields, vm.model, currentVersion, currentCategoryId, dispatchId, hospitalUuid)
            return saveBundle(bundle);
        })
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

    $scope.save = save;
    $scope.cancel = cancel;

    function init(){
    	return setUpCategory()
        .then(function(){
            return setUpDispatch(dispatchId);
        });
    }

    init();

});

