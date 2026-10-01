angular.module('formlyCustomRadio', [])
    .config(function(formlyConfigProvider) {
        formlyConfigProvider.setType({
            name: 'Radio',
            templateUrl: 'templates/formly/radio.html',
            controller: function($scope, FormlyExtensionService) {
                function radioClicked(value, questionCode, currentValue){
                    if(value===currentValue){
                        delete $scope.model[questionCode];
                    }
                }
                function confirmCancel(key) {
                    var ret = confirm("確定刪除?");
                    if (ret) {
                        delete $scope.model[key];
                    }
                }
                $scope.confirmCancel = confirmCancel;
                $scope.radioClicked = radioClicked;

                function EXTFUNC(func, args) {
                    return FormlyExtensionService[func](args);
                }
                $scope.EXTFUNC = EXTFUNC;

                // 2021-02-01 Rong add process wrap and no wrap
                function filterNoWrapOptions(datas){
                  let tmpDatas = []
                  if(datas){
                    angular.forEach(datas, function(o){
                      if(o.data.isNoWrap == true || o.data.isNoWrap == 1){ tmpDatas.push(o); }
                    })
                  } // if
                  return tmpDatas
                }
                function filterWrapOptions(data){
                  var isDisplay = false;
                  if(data){
                    for(var idx in data.nextQuestions){
                      if(!data.nextQuestions[idx].data.isNoWrap){
                        isDisplay = true;
                        break;
                      } // if
                    } // for
                  }
                  return isDisplay ? data:null;
                }
                $scope.filterNoWrapOptions = filterNoWrapOptions;
                $scope.filterWrapOptions = filterWrapOptions;
            }
        })
    });
