/* 回溯編輯器 */
CONTROLLERS.controller('BackTrackingEditorCtrl', function($scope, $state, $window, $timeout,
    $http, AuthService, $stateParams, PcrQuestionService, $q, $modal, $controller) {
    $controller('svgInOpStatusCtrl', { $scope: $scope }); //
    var g_CATEGORY_ID = 0;
    var G_ORIGIN = "*";
    var aryPcrUuid = [];

    if(!_.isNil($stateParams.mainData)){
        if(typeof($stateParams.mainData) == 'string'){
            var param = JSON.parse($stateParams.mainData);
            g_CATEGORY_ID = param.categoryId;
            aryPcrUuid = param.uuids;
        }else{
            window.close();
        } // if
    }

    var vm = {};
    var debugModel = $stateParams.debugModel == 'true' ? true : false;
    var debugFields = $stateParams.debugFields == 'true' ? true : false;
    
    var g_FORM_BUNDLE_UUID;
    var g_VERSION_ID;
    let CATEGORY_ID_CENTER = 1;

    $scope.maxLen = aryPcrUuid.length;
    $scope.curIdx = 0;
    $scope.pcrInfo = {};
    

    function init(PcrUuid) {
        if(_.isNil(PcrUuid)){
            $state.go('ohcaCaseList');
            return;
        }

        $scope.PcrUuid = PcrUuid;
        $scope.debugModel = debugModel;
        $scope.debugFields = debugFields;

        return setupCategory(g_CATEGORY_ID)
        .then(function(){
            return setup();
        })
        .then(function(){
            return showFormly()
        })
    }

    function changePcr(moveNext){
        if(!_.isNil(moveNext)){
            // move next
            if($scope.curIdx < aryPcrUuid.length-1){
                $scope.curIdx++;
            }// else already the last one.
        }else{
            // move previous
            if($scope.curIdx > 0){
                $scope.curIdx--;
            }// else already the first one.
        }

        var _PcrUuid = aryPcrUuid[$scope.curIdx];
        init(_PcrUuid);
    }

    function showFormly(){
        var model;
        var FormCategory

        if(_.isNil($scope.FormBundle)){
            model = {};
            FormCategory = $scope.FormCategory;
        }else{
            model = formBundleToModel($scope.FormBundle);
            FormCategory = $scope.FormBundle.FormCategory;
        }
        
        pcrUuid = $scope.PcrUuid;

        var deferred = $q.defer();
        $scope.cgBusyPromise = deferred.promise;
        return getVersionNumber(pcrUuid, FormCategory.id)
        .then(function(versionId){
            g_VERSION_ID = versionId;
            return getFormlyFields(versionId, FormCategory.id)
            .then(function(formlyFields){
                // FeatureAdd Jordan 2021-06-28 傳入系統的額外資訊 車輛名稱、抵達醫院日期(arrivedHospitalAt)
                addExtInfo_$arrivedHospitalAt(model);
                addExtInfo_$ambulanceInfo(model);

                vm.model = model;
                vm.fields = angular.copy(formlyFields);

                $scope.vm = vm;
                $scope.formlyFields = formlyFields;
            })
        })
        .catch(function(error){
            // alert('無法載入題庫');
            $state.go('ohcaCaseList');
            console.log(error);
        })
        .finally(function(){
            deferred.resolve();
        });
    }

    function addExtInfo_$arrivedHospitalAt(ref_model){
        if(!_.isNil($scope.Pcr) && !_.isNil($scope.Pcr.arrivedHospitalAt)){
            ref_model['$arrivedHospitalAt'] = moment($scope.Pcr.arrivedHospitalAt).format('YYYY-MM-DD 00:00:00');
        }
    }

    function addExtInfo_$ambulanceInfo(ref_model){
        if(!_.isNil($scope.Pcr) && !_.isNil($scope.Pcr.DispatchRecord) && !_.isNil($scope.Pcr.DispatchRecord.Ambulance) ){
            ref_model['$ambulanceInfo'] = $scope.Pcr.DispatchRecord.Ambulance.code 
                                            + '(' + $scope.Pcr.DispatchRecord.Ambulance.licenseNo + ')';
        }
    }

    function setup(){
        var deferred = $q.defer();
        $scope.cgBusyPromise = deferred.promise;
        return setupPcr($scope.PcrUuid)
        .then(function(){
            g_FORM_BUNDLE_UUID = null;
            var formBundle = _.find($scope.Pcr.FormBundles, function(o){
                return o.FormCategoryId == parseInt(g_CATEGORY_ID)
            })
            if(formBundle){
                g_FORM_BUNDLE_UUID = formBundle.uuid;
            }
            return setupFormBundle(g_FORM_BUNDLE_UUID);
        })
        .then(function(){
            // FeatureAdd 取得中心的答案，讓品管時可呈現答案在右方
            if(g_CATEGORY_ID != CATEGORY_ID_CENTER){
                var formBundle = _.find($scope.Pcr.FormBundles, function(o){
                    return o.FormCategoryId == parseInt(CATEGORY_ID_CENTER)
                })
                if(formBundle){
                    return getFormBundle(formBundle.uuid)
                    .then(function(result){
                        $scope.FormBundleCenter = result;
                    })
                }else{
                    $scope.FormBundleCenter = null;
                }
            }else{
                $scope.FormBundleCenter = null;
            }
        })
        .finally(function(){
            deferred.resolve();
        });
    }

    function getCategory(id){
        return $http.get('/FormCategories/'+id)
        .then(function(response){
            return response.data;
        })
    }

    function setupCategory(id){
        return getCategory(id)
        .then(function(results){
            $scope.FormCategory = results;
            // FeatureAdd 取得中心的答案，讓品管時可呈現答案在右方
            if(id != CATEGORY_ID_CENTER){
                return getCategory(id)
                .then(function(data){
                    $scope.FormCategoryCenter = data;
                })
            }else{
                $scope.FormCategoryCenter = null;
            }
        })
        .catch(function(error){
            // alert('無法取得FormCategory');
            $state.go('ohcaCaseList');
            console.log(error);
        });
    }

    function getVersionNumber(uuid, categoryId){
        return $http.get('/FormBundles/getFormVersion',{
            params: {
                PcrUuid: uuid,
                categoryId: categoryId
            }
        })
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

    function getPcr(pcrUuid){
        return $http.get('/Pcrs/'+pcrUuid)
        .then(function(response){
            return response.data;
        });
    }

    function setupPcr(pcrUuid){
        return getPcr(pcrUuid)
        .then(function(result){
            $scope.Pcr = result;
            $scope.status.Pcr = $scope.Pcr;
            $scope.status.getOpStatus($scope.Pcr);
        })
        .catch(function(error){
            // alert('無法取得Pcr');
            $state.go('ohcaCaseList');
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
            formRecordsToModel(model, record)
        }
        return model;
    }

    function formRecordsToModel(model, record){
        var answer=null;
        switch(record.FormQuestion.FormQuestionTypeId){
            case 1: // DateTime
            case 6: //  Date
            case 11: // Time
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
            case 9: // String
            case 10: // Dispaly
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
            case 8: // RepeatSection
                answer = [];
                var recordByIndex = _.groupBy(record.FormRecords, 'sectionIndex')
                for(var sectionIndex in recordByIndex){
                    var section = recordByIndex[sectionIndex];
                    var sectionModel = {};
                    for(var j in section){
                        formRecordsToModel(sectionModel,section[j]);
                    }
                    answer.push(sectionModel)
                }
            break;
        }
        model[record.FormQuestion.code] = answer;
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

    function saveAndNext(model, fields, isComplete){
        saveBacktracking(model, fields, isComplete)
        .then(function(){
            changePcr(1);
        })
        .catch(function(err){
            // 未填寫題目，不切到下一筆
            console.log('==== saveAndNext.err:',err)
        })
    }

    function saveBacktracking(model, fields, isComplete){
        if(checkEmptyAnswers(model)){
            alert('尚未填寫任何題目，請繼續填寫');
            return $q.reject();
        }

        var deferred = $q.defer();
        $scope.modalCgBusyPromise = deferred.promise;
        var output = model; // 在回答過程中，被hide的題目已經把答案也消掉了
        var task;
        if(_.isNil(g_FORM_BUNDLE_UUID)){
            task = $http.post('/FormBundles/addTo/'+ $scope.PcrUuid, {
                FormCategoryId: g_CATEGORY_ID,
                FormVersionId: g_VERSION_ID,
                model: output,
                // isComplete: isComplete
            })
        }else{
            task = $http.put('/FormBundles/updateTo/'+g_FORM_BUNDLE_UUID, {
                model: output,
                // isComplete: isComplete
            });
        }

        return task
        .then(function(){
            if($scope.curIdx >= $scope.maxLen-1){
                // $state.go('ohcaCaseList');
                close();
            }else{
                return setup();
            }
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

    function processRepeatSection(FormRecords){
        var output =[]
        var bySectionIndex = _.groupBy(FormRecords, 'sectionIndex');
        for(var sectionIndex in bySectionIndex){
            output.push(bySectionIndex[sectionIndex])
        }
        return output;
    }

    function goCaseDetail(){
        $window.open('/#/caseDetail/' + $scope.PcrUuid, '_blank');
    }

    function goCaseDetailPrint(){
        $window.open('/#/caseDetailPrint/' + $scope.PcrUuid + '/1', '_blank');
    }

    function goCenterBacktrack(){
        $state.go('centerBacktrack', {uuids:[$scope.PcrUuid], categoryId: CATEGORY_ID_CENTER})
    }

    function close(){
        if(window.opener){
          window.opener.postMessage('addVisitDone.refresh',G_ORIGIN);
        }
        window.close();
    }

    $scope.close = close;
    $scope.saveBacktracking = saveBacktracking;
    $scope.deleteBacktracking = deleteBacktracking;
    $scope.processRepeatSection = processRepeatSection;
    $scope.changePcr = changePcr;
    $scope.saveAndNext = saveAndNext;
    $scope.goCaseDetail = goCaseDetail;
    $scope.goCaseDetailPrint = goCaseDetailPrint;
    $scope.goCenterBacktrack = goCenterBacktrack;

    return $http.get('/config')
    .then(function(response){
        G_ORIGIN = response.data.hostname + ':' + response.data.port;
        changePcr();
    })
});