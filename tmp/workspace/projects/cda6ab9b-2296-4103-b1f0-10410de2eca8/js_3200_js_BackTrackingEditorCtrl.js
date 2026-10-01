/* 回溯編輯器 */
CONTROLLERS.controller('BackTrackingEditorCtrl', function($scope, $state, $window, $timeout,
    $http, AlertService, AuthService, $stateParams, PcrQuestionService, $q, $modal) {
    var vm = {};
    var btModal;
    var DispatchId = $stateParams.dispatchId;
    var debug = $stateParams.debug? toBoolean($stateParams.debug) : false;

    function init() {
        btModal = {
            modal: $modal({
              scope: $scope,
              templateUrl: 'templates/modal/backtrackingModal.html',
              animation: 'no-animation',
              placement: 'center',
              backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗 value = 'static' or boolean
              show: false
            }),
            category:null
        }
        $scope.btModal = btModal;
        $scope.DispatchId = DispatchId;
        $scope.debug = debug;
        return setupCategory()
        .then(function(){
            return setup();
        });
    }

    function setup(){
        var deferred = $q.defer();
        $scope.cgBusyPromise = deferred.promise;
        return setupDispatch(DispatchId)
        .then(function(){
            return setupFormBundle($scope.Dispatch.FormBundleUuid);
        })
        .finally(function(){
            deferred.resolve();
        });
    }

    function getCategory(){
        return $http.get('/FormCategories')
        .then(function(response){
            return response.data;
        })
    }

    function setupCategory(){
        return getCategory()
        .then(function(results){
            $scope.FormCategories = results;
        })
        .catch(function(error){
            alert('無法取得FormCategory');
            console.log(error);
        });
    }

    function getVersionNumber(dispatchId){
        return $http.get('/Dispatches/getFormVersionOf/'+dispatchId)
        .then(function(response){
            return response.data;
        })
    }

    function getFormlyFields(versionId, categoryId){
        var fileName = versionId+'-'+categoryId+'.json';
        return $http.get('/json/new/'+fileName)
        .then(function(response){
            return response.data;
        })
    }

    function getDispatch(DispatchId){
        return $http.get('/Dispatches/'+DispatchId)
        .then(function(response){
            return response.data;
        });
    }

    function setupDispatch(DispatchId){
        return getDispatch(DispatchId)
        .then(function(result){
            $scope.Dispatch = result;
        })
        .catch(function(error){
            alert('無法取得Dispatch');
            console.log(error);
        });
    }

    function getFormBundle(FormBundleUuid){
        if(FormBundleUuid==null){
            var deferred = $q.defer()
            deferred.resolve(null);
            return deferred.promise;
        }else{
            return $http.get('/FormBundles/getContentOf/'+FormBundleUuid)
            .then(function(response){
                return response.data;
            })
        }
    }

    function formBundleToModel(FormBundle){
        var model = {};
        for(var i in FormBundle.FormRecords){
            var record = FormBundle.FormRecords[i];
            var answer=null;
            switch(record.FormQuestion.FormQuestionTypeId){
                case 1: // DateTime
                case 6: //  Date
                    var answerRecord = record.FormAnswerRecords[0];
                    if(!answerRecord) { break; }    // BugFix 2021-05-17 若答案為 NULL 則以下的動作會當掉
                    answer=moment(answerRecord.freeTypingValue).toDate();
                break;
                case 3: // Int
                    var answerRecord = record.FormAnswerRecords[0];
                    if(!answerRecord) { break; }    // BugFix 2021-05-17 若答案為 NULL 則以下的動作會當掉
                    // answer=parseInt(answerRecord.freeTypingValue);
                    answer=String(answerRecord.freeTypingValue);
                break;
                case 4: // Text
                    var answerRecord = record.FormAnswerRecords[0];
                    if(!answerRecord) { break; }    // BugFix 2021-05-17 若答案為 NULL 則以下的動作會當掉
                    answer=answerRecord.freeTypingValue;
                break;
                case 2:
                case 7:
                    var answerRecord = record.FormAnswerRecords[0];
                    if(!answerRecord) { break; }    // BugFix 2021-05-17 若答案為 NULL 則以下的動作會當掉
                    answer=answerRecord.FormAnswer.code;
                break;
                case 5: // Checkbox
                    if(answer==null){
                        answer=[];
                    }
                    for(var j in record.FormAnswerRecords){
                        var answerRecord = record.FormAnswerRecords[j];
                        answer.push(answerRecord.FormAnswer.code);
                    }
                break;
            }
            model[record.FormQuestion.code] = answer;
        }
        return model;
    }

    function setupFormBundle(FormBundleUuid){
        if(_.isNil(FormBundleUuid)){
            $scope.FormBundle = null
            return;
        }else{
            return getFormBundle(FormBundleUuid)
            .then(function(result){
                $scope.FormBundle = result;
            });
        }
    }

    function showBacktrackingModal(model, DispatchId, FormCategory){
        var deferred = $q.defer();
        $scope.cgBusyPromise = deferred.promise;
        return getVersionNumber(DispatchId)
        .then(function(versionId){
            return getFormlyFields(versionId, FormCategory.id)
            .then(function(formlyFields){
                vm.model = model;
                vm.fields = angular.copy(formlyFields);

                $scope.vm = vm;
                $scope.formlyFields = formlyFields;
                btModal.FormCategory = FormCategory;
                btModal.DispatchId = DispatchId;
                btModal.FormVersionId = versionId;
                btModal.modal.$promise.then(btModal.modal.show);
            })
        })
        .catch(function(error){
            alert('無法載入題庫');
            console.log(error);
        })
        .finally(function(){
            deferred.resolve();
        });
    }

    function addBacktrackingModal(Dispatch, FormCategory){
        btModal.FormBundleUuid = null;
        return showBacktrackingModal({}, Dispatch.id, FormCategory);
    }

    function editBacktrackingModal(Dispatch, FormBundle){
        var model = formBundleToModel(FormBundle);
        var FormCategory = FormBundle.FormCategory;
        btModal.FormBundleUuid = FormBundle.uuid;
        return showBacktrackingModal(model, Dispatch.id, FormCategory);
    }

    function getQuestionByKey(key, fields){
        for(var blockIdx in fields){
            var block = fields[blockIdx];
            var result = getQuestionByKeyInBlock(key, block.fieldGroup)
            if(result!=null){
                return result;
            }
        }
    }

    function getQuestionByKeyInBlock(key, fields){
        for(var fIdx in fields){
            var question = fields[fIdx];
            if(question.key==key){
                return question;
            }else{
                for(var aIdx in question.templateOptions.options){
                    var answer = question.templateOptions.options[aIdx];
                    if(answer.nextQuestions){
                        var nxt = getQuestionByKeyInBlock(key, answer.nextQuestions)
                        if(nxt!=null){
                            return nxt;
                        }
                    }
                }
            }
        }
        console.log('Question not found! key=', key);
        return null;
    }

    function checkEmptyAnswers(model){
        var answerCount = _.size(model);
        var nullCount = 0;
        for(var field in model){
            if(_.isNil(model[field])){
                nullCount++;
            }
        }
        if(nullCount==answerCount){
            return true;
        }else{
            return false;
        }
    }

    function saveBacktracking(model, fields, DispatchId, FormCategory, FormBundleUuid, FormVersionId, isComplete){
        if(checkEmptyAnswers(model)){
            alert('尚未填寫任何題目，請繼續填寫');
            return;
        }

        var deferred = $q.defer();
        $scope.modalCgBusyPromise = deferred.promise;
        var output = model; // 在回答過程中，被hide的題目已經把答案也消掉了
        var task;
        if(_.isNil(FormBundleUuid)){
            task = $http.post('/FormBundles/addTo/'+DispatchId, {
                FormCategoryId: FormCategory.id,
                FormVersionId: FormVersionId,
                model: output,
                isComplete: isComplete
            })
        }else{
            task = $http.put('/FormBundles/updateTo/'+FormBundleUuid, {
                model: output,
                isComplete: isComplete
            });
        }

        task.then(function(){
            return btModal.modal.$promise.then(btModal.modal.hide);
        })
        .then(function(){
            return setup();
        })
        .catch(function(error){
            console.log(error);
            alert('無法儲存回溯內容');
        })
        .finally(function(){
            deferred.resolve();
        });
    }

    function deleteBacktracking(FormBundleUuid){
        var deferred = $q.defer();
        $scope.cgBusyPromise = deferred.promise;
        var ret = confirm('確定刪除回溯？')
        if(ret){
            return $http.delete('/FormBundles/'+FormBundleUuid)
            .then(function(){
                return setup();
            })
            .catch(function(error){
                console.log(error);
                alert('無法刪除回溯');
            })
            .finally(function(){
                deferred.resolve();
            })
        }else{
            deferred.resolve();
        }
    }

    $scope.addBacktrackingModal = addBacktrackingModal;
    $scope.editBacktrackingModal = editBacktrackingModal;
    $scope.saveBacktracking = saveBacktracking;
    $scope.deleteBacktracking = deleteBacktracking;

    init();

});