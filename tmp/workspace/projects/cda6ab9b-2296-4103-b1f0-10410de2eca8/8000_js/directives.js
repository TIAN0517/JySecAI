angular.module('directives', [])
  .directive('ngEnter', function() {
    return function(scope, element, attrs) {
      element.bind("keydown keypress", function(event) {
        if (event.which === 13) {
          scope.$apply(function() {
            scope.$eval(attrs.ngEnter);
          });
          event.preventDefault();
        }
      });
    };
  })
  .directive('webBlank', function() {
    return {
      restrict: 'A',
      link: function(scop, element, attrs) {
        var href = element[0].href;
        if (href) {
          element.attr('target', '_blank')
        }
      }
    }
  })

  .directive('authUser', function(AuthService) {
    return {
      restrict: 'A',
      link: function(scop, element, attrs) {
        var userData = AuthService.getCurrentUser();
        var name = userData ? userData['name'] : '';
        var displayLabel = name;

        element.text(displayLabel);
      }
    }
  })
  .directive('toggleCheckbox', function() {

    /**
     * Directive
     */
    return {
      restrict: 'A',
      transclude: true,
      replace: false,
      require: 'ngModel',
      link: function($scope, $element, $attr, require) {

        var ngModel = require;

        // update model from Element
        var updateModelFromElement = function() {
          // If modified
          var checked = $element.prop('checked');
          if (checked != ngModel.$viewValue) {
            // Update ngModel
            ngModel.$setViewValue(checked);
            $scope.$apply();
          }
        };

        // Update input from Model
        var updateElementFromModel = function() {
          // Update button state to match model
          $element.trigger('change');
        };

        // Observe: Element changes affect Model
        $element.on('change', function() {
          updateModelFromElement();
        });

        // Observe: ngModel for changes
        $scope.$watch(function() {
          return ngModel.$viewValue;
        }, function() {
          updateElementFromModel();
        });

        // Initialise BootstrapToggle
        $element.bootstrapToggle();
      }
    };
  })
  // 顯示派遣分類的名稱
  .directive('dispatchModeFromNtfd', function($http) {

    function getDispatchModeName(mode) {
      switch (mode) {
        case 0:
          return 'BLS';
        case 1:
          return 'MER';
        case 2:
          return 'ALS';
        default:
          return '';
      }
    }

    return {
      restrict: 'E',
      scope: {
        externalKey: '='
      },
      link: function(scope, element, attrs) {
        scope.$watch('externalKey', function(newValue, oldValue) {
          if (newValue) {
            var externalKey = newValue;
            $http.get('/CaseRecords/dispatchModeByExternalKey/' + externalKey)
              .then(function(response) {
                var dispatchMode = response.data.DispatchMode;
                var dispatchModeName = getDispatchModeName(dispatchMode);
                element.text(dispatchModeName);
              })
              .catch(function(error) {
                console.log(error);
              })
          }
        });
      }
    }
  })
  // 顯示派遣原因
  .directive('caseTypeNameFromNtfd', function($http) {

    return {
      restrict: 'E',
      scope: {
        recordUuid: '='
      },
      link: function(scope, element, attrs) {
        scope.$watch('recordUuid', function(newValue, oldValue) {
          if (newValue) {
            var recordUuid = newValue;
            $http.get('/CaseRecords/CaseTypeNameByCaseNo/' + recordUuid)
              .then(function(response) {
                if (response.data) {
                  var CaseTypeName = response.data.CaseTypeName;
                  element.text(CaseTypeName);
                }
              })
              .catch(function(error) {
                console.log(error);
              })

          }
        });
      }
    }
  })
  // 顯示醫師簽核狀態
  .directive('pcrDoctorOrderStatus', function() {

    return {
      restrict: 'E',
      scope: {
        status: '='
      },
      link: function(scope, element, attrs) {
        scope.$watch('status', function(newValue, oldValue) {
          var output = "";
          if (newValue) {
            var status = newValue;

            switch (status) {
              case 1:
                output = "未簽核";
                break;
              case 2:
                output = "已簽核";
                break;
              case 3:
                output = "無須簽核";
                break;
              default:
                output = "";
                break;
            }
          }
          element.text(output);

        });
      }
    }
  })

  .directive('pcrAnswerRecord', function() {
    return {
      restrict: 'E',
      scope: {
        freeTypingValue: '=',
        questionTypeId: '=',
        displayLabel: '='
      },
      link: function(scope, element, attrs) {

        function updateValue(newValue, oldValue) {
          var output = "";
          if (newValue) {
            var questionTypeId = scope.questionTypeId;
            var freeTypingValue = scope.freeTypingValue;
            var displayLabel = scope.displayLabel;
            switch (questionTypeId) {
              case 1:
                output = moment(freeTypingValue).format('YYYY-MM-DD HH:mm:ss');
                break;
              case 2:
                output = displayLabel;
                break;
              case 3:
                output = freeTypingValue;
                break;
              case 4:
                output = freeTypingValue;
                break;
              case 5:
                output = "*" + displayLabel;
                break;
              case 6:
                output = moment(freeTypingValue).format('YYYY-MM-DD');
                break;
              case 7:
                output = freeTypingValue;
                break;
            }
          }
          element.text(output);

        }
        scope.$watch('questionTypeId', updateValue);
      }
    }
  })

  .directive('qaByCode', function(PrintFormatSvc) {

    return {
      restrict: 'E',
      scope: {
        code: '=',
        qamap: '=',
        qarecordmap: '=',
        nextquestionmap: '='
      },
      link: function(scope, element, attrs) {
        function doAnswers(questionCode, ansRecords) {
          var returnElement = "";
          var pcrQuestionTypeId = scope.qamap[questionCode].PcrQuestionTypeId;
          var pcrAnswers = scope.qamap[questionCode].PcrAnswers;
          ansRecords.forEach(function(ansR) {
            for (var i = 0; i < pcrAnswers.length; i++) {
              if (pcrAnswers[i].id == ansR.PcrAnswerId) {
                pcrAnswers[i].hasRecord = true;
                pcrAnswers[i].freeTypingValue = ansR.freeTypingValue;
              }
            }
          })
          for (var i = 0; i < pcrAnswers.length; i++) {
            var ans = pcrAnswers[i];
            if (ans.hasRecord) {
              if (pcrQuestionTypeId == 2 || pcrQuestionTypeId == 5) {
                returnElement += '<span style="margin:2px;margin-left:3px;color:blue;border-style:solid;border-width:1px;padding-bottom:2px;" class="glyphicon glyphicon-stop">' +
                  '<b>' + ans.displayLabel + '</b>' + '</span>'
              } else if (pcrQuestionTypeId == 1 || pcrQuestionTypeId == 6) {
                returnElement += ans.freeTypingValue ? moment(ans.freeTypingValue).format("MM/DD HH:mm:ss") : "";
              } else {
                returnElement += ("<b>" + ans.displayLabel + " " + ans.freeTypingValue + "</b>");
              }

              if (scope.nextquestionmap[ans.code]) {
                returnElement += doNextQAs(scope.nextquestionmap[ans.code].nextQuestion);
              }
            } else {
              returnElement += '<span style="margin:2px;margin-left:3px;" class="glyphicon glyphicon-unchecked">' +
                ans.displayLabel + '</span>'
            }
          }

          return returnElement;
        }

        function doNextQAs(nextQcodes) {
          var returnElement = "";
          nextQcodes.forEach(function(nextQcode) {
            returnElement += doQA(nextQcode.code);
          })
          return "(" + returnElement + ")";
        }

        function doAnsweredQA(record) {
          var returnElement = "";
          returnElement += ("<b>" + record.PcrQuestion.displayLabel + " : " + "</b>");
          returnElement += doAnswers(record.PcrQuestion.code, record.PcrAnswerRecords);
          return returnElement;
        };

        function doQA(code) {
          var returnElement = "";
          var record = scope.qarecordmap[code];
          if (record) {
            returnElement += (doAnsweredQA(record));
          } else {
            var map0 = PrintFormatSvc.findInQAMAP(code, scope.qamap);
            // console.log("code", code);
            if (map0){
              returnElement += ("<b>" + map0.q + " : " + "</b>");
              map0.a.forEach(function(aText) {
                returnElement += ('<span style="margin:2px;margin-left:3px;" class="glyphicon glyphicon-unchecked">' +
                  aText + '</span>')
              })
            }

          }
          return returnElement;
        }

        function updateValue(newValue, oldValue) {
          var code = scope.code;
          if (newValue) {
            element.append(doQA(code));
          }
        }

        scope.$watch('nextquestionmap', updateValue);
      }
    }
  })

  .directive('specQa', function(PrintFormatSvc) {
    return {
      restrict: 'E',
      scope: {
        code: '=',
        text: '=',
        type: '=',
        codes: '=',
        qamap: '=',
        qarecordmap: '=',
        nextquestionmap: '='
      },
      link: function(scope, element, attrs) {
        function findInQuestions(code, questions) {
          for (var i = 0; i < questions.length; i++) {
            // console.log("questions[i]",questions[i]);
            if (questions[i].code == code) {
              return questions[i];
            } else if (questions[i].answer && questions[i].answer.length) {
              for (var j = 0; j < questions[i].answer.length; j++) {
                if (questions[i].answer[j].nextQuestions) {
                  var findInNext = findInQuestions(code, questions[i].answer[j].nextQuestions);
                  if (findInNext) return findInNext;
                }
              }
            }
          }
          return null;
        }

        function findInQARecord(code) {
          for (var i = 0; i < scope.qarecord.length; i++) {
            var blocks = scope.qarecord[i];
            var blocksAry = Object.keys(blocks);
            for (var j = 0; j < blocksAry.length; j++) {
              var block = blocks[blocksAry[j]];
              var q = findInQuestions(code, block.questions);
              if (q) return q;
            }
          }
          return null;
        };

        function doAnswer(ansRecord, toDoNext) {
          var returnElement = "";
          if (ansRecord.isSelected) {
            returnElement += '<span style="margin:1px;margin-left:2px;">' +
              ansRecord.displayLabel + '</span>'
            if (toDoNext && ansRecord.nextQuestions) {
              returnElement += doNextQAs(ansRecord.nextQuestions);
            }
          } else {
            // returnElement += '<span style="margin:1px;margin-left:2px;" class="glyphicon glyphicon-unchecked"></span>'
            // + ansRecord.displayLabel + '</span>'
          }
          return returnElement;
        }

        function doAnswers(questionCode, ansRecords, doNext) {
          var returnElement = "";
          var pcrQuestionTypeId = scope.qamap[questionCode].PcrQuestionTypeId;
          var pcrAnswers = scope.qamap[questionCode].PcrAnswers;
          ansRecords.forEach(function(ansR) {
            for (var i = 0; i < pcrAnswers.length; i++) {
              if (pcrAnswers[i].id == ansR.PcrAnswerId) {
                pcrAnswers[i].hasRecord = true;
                pcrAnswers[i].freeTypingValue = ansR.freeTypingValue;
              }
            }
          })
          for (var i = 0; i < pcrAnswers.length; i++) {
            var ans = pcrAnswers[i];
            if (ans.hasRecord) {
              if (pcrQuestionTypeId == 2 || pcrQuestionTypeId == 5) {
                returnElement += '<span>' +
                  ans.displayLabel + '</span>'
              } else if (pcrQuestionTypeId == 1 || pcrQuestionTypeId == 6) {
                returnElement += ans.freeTypingValue ? moment(ans.freeTypingValue).format("MM/DD HH:mm:ss") : "";
              } else {
                returnElement += (ans.displayLabel + " " + ans.freeTypingValue);
              }

              if (doNext && scope.nextquestionmap[ans.code]) {
                returnElement += doNextQAs(scope.nextquestionmap[ans.code].nextQuestion);
              }
            } else {
              // returnElement += '<span>'
              // + ans.displayLabel + '</span>'
            }
          }

          return returnElement;
        }

        function doNextQAs(nextQcodes) {
          var returnElement = "";
          nextQcodes.forEach(function(nextQcode) {
            returnElement += doQA(nextQcode.code, null, true);
          })
          if (returnElement) {
            return "(" + returnElement + ")";
          } else {
            return "";
          }

        }

        function doAnsweredQA(record, text, doNext) {
          var returnElement = "";

          if (text) {
            returnElement += ("<b>" + text + " : " + "</b>");
          } else {
            returnElement += ("<b>" + record.PcrQuestion.displayLabel + " : " + "</b>");
          }
          returnElement += doAnswers(record.PcrQuestion.code, record.PcrAnswerRecords, doNext);
          return returnElement;
        };

        function type2(code, codes, text) {
          var returnElement = "";
          returnElement += doQA(code, text);
          codes.forEach(function(_code) {
            var record = scope.qarecordmap[_code];
            if (record && record.PcrAnswerRecords) {
              record.PcrAnswerRecords.forEach(function(ansR) {
                var timeTxt = moment(ansR.freeTypingValue).format("HH:mm:ss")
                returnElement += "<span> " + timeTxt + " ; </span>";
              })
            }
          })
          return returnElement;
        }

        function type3(code, codes, text) {
          var returnElement = "";
          var qLabel;
          if (text) {
            qLabel = "<b>" + text + " : " + "</b>"
          } else {
            qLabel = "<b>" + scope.qarecordmap[code].PcrQuestion.displayLabel + " : " + "</b>"
          }

          var times = 0;
          codes.forEach(function(_code) {
            var record = scope.qarecordmap[_code];
            if (record && record.PcrAnswerRecords) {
              times++;
              record.PcrAnswerRecords.forEach(function(ansR) {
                var timeTxt = moment(ansR.freeTypingValue).format("HH:mm:ss")
                returnElement += "<span> " + timeTxt + " ; </span>";
              })
            }
          })

          if (times > 0) {
            returnElement = qLabel + times + "次， " + returnElement;
          } else {
            returnElement += (qLabel + doQA(code, null, true));
          }

          return returnElement;
        }

        function type4(code, codes, text) {
          var returnElement = "";
          var qLabel = "";
          if (text) {
            qLabel = "<b>" + text + " : " + "</b>"
          } else {
            // qLabel =  "<b>"+scope.qarecordmap[code].PcrQuestion.displayLabel + " : " + "</b>"
          }

          codes.forEach(function(_code) {
            var record = scope.qarecordmap[_code];
            if (record && record.PcrAnswerRecords) {
              record.PcrAnswerRecords.forEach(function(ansR) {
                var timeTxt = moment(ansR.freeTypingValue).format("HH:mm:ss")
                returnElement += "<span> " + timeTxt + " ; </span>";
              })
            }
          })

          return qLabel + returnElement;
        }

        function type5(code, codes, text) {
          var returnElement = "";
          var qLabel;
          if (text) {
            qLabel = "<b>" + text + " : " + "</b>"
          } else {
            qLabel = "<b>" + scope.qarecordmap[code].PcrQuestion.displayLabel + " : " + "</b>"
          }
          var space0 = "&emsp;&emsp;";
          var space = space0 + space0 + space0 + space0;
          var count = 0;
          codes.forEach(function(codeObj) {
            if (typeof(codeObj) == "object") {
              returnElement += (doQA(codeObj.code, codeObj.text, false) + space0);
            }
            if (!(scope.qarecordmap[codeObj.code])) {
              returnElement += space;
            } // 沒答案塞空白

            count++;
            if (count == 2) {
              returnElement += "<br>"
            }
          })

          return qLabel + returnElement;
        }

        function doQA(code, text, doNext) {
          var returnElement = "";
          var record = scope.qarecordmap[code];
          if (record) {
            returnElement += doAnsweredQA(record, text, doNext);
          } else {
            var map0 = PrintFormatSvc.findInQAMAP(code, scope.qamap);
            var qText;
            if (text) {
              qText = text;
            } else {
              qText = map0 ? map0.q : "" ;
            }
            // WorkAround 2022-10-12 舊題目被刪除時，設定舊題目不存在的新QuestionID時，會出現只有 : ，而無題目及答案的狀況
            if(qText != ""){
              returnElement += "<b>" + qText + " : " + "</b>";
            }
          }

          return returnElement;
        }

        function defaultF(code, type, text) {
          var doNext = (type == 1);
          return doQA(code, text, doNext);
        }

        function updateValue(newValue, oldValue) {
          if (newValue) {
            if (!scope.code && !scope.type) {
              element.append("<b>" + scope.text + " : " + "</b>");
            } else {
              var elementForAppend = "";
              switch (scope.type) {
                case 2:
                  elementForAppend = type2(scope.code, scope.codes, scope.text)
                  break;
                case 3:
                  elementForAppend = type3(scope.code, scope.codes, scope.text)
                  break;
                case 4:
                  elementForAppend = type4(scope.code, scope.codes, scope.text)
                  break;
                case 5:
                  elementForAppend = type5(scope.code, scope.codes, scope.text)
                  break;
                default:
                  elementForAppend = defaultF(scope.code, scope.type, scope.text);
              }

              element.append(elementForAppend);
            }
          } // if newValue
        } // updateValue()

        scope.$watch('nextquestionmap', updateValue);
      }
    }
  })
  .directive('hospitalOfPcr', function() {
    return {
      restrict: 'E',
      scope: {
        pcr: '='
      },
      link: function(scope, element, attrs) {
        scope.$watch('pcr', function(newValue, oldValue) {
          if (newValue) {
            var pcr = newValue;
            if (pcr.StatusId == 23) {
              // PCR已取消
              element.text('(案件取消)');
            } else {
              if (pcr.PcrCancelReasonId == 3) {
                // 拒絕送醫
                element.text('(拒絕送醫)');
              } else if (pcr.HospitalUuid == null) {
                if (pcr.otherHospitalName) {
                  element.text(pcr.otherHospitalName);
                } else {
                  element.text('(未送醫)');
                }
              } else {
                element.text(pcr.Hospital.name);
              }
            }
          }
        });
      }
    }
  })
  .directive('patientAddress', function() {
    return {
      restrict: 'E',
      scope: {
        pcr: '='
      },
      link: function(scope, element, attrs) {
        scope.$watch('pcr', function(newValue, oldValue) {
          if (newValue) {
            var pcr = newValue;
            if (pcr.patientAddressUnknown) {
              // 患者地址不詳
              element.text('(不詳)');
            } else {
              element.text(pcr.patientAddress);
            }
          }
        });
      }
    }
  })
  .directive('pcrAge', function(){

    return {
      restrict: 'A',
      scope:{
        age: '='
      },
      link: function(scope, element, attrs) {
        scope.$watch('age', function(newValue, oldValue) {
          if(!_.isNil(newValue)){
              var output = "";
              if(newValue==0){
                  output = '新生兒(0歲)'
              }else if(newValue>12){
                  output = Math.round(newValue / 12) + '歲'
              }else{
                  output = newValue+'個月'
              }
              element.text(output);
          }
        });
      }
    }
  })
// 顯示EPCR 或 MER 的評估處置
  .directive('answerRecord', function(){
      function getAnswer(questionTypeId, pcrAnswerRecord){
          var output = '';
          switch(questionTypeId){
              case 1://'DateTime':
                  output = _.isNil(pcrAnswerRecord.freeTypingValue) ? '' : moment(pcrAnswerRecord.freeTypingValue).format('YYYY/MM/DD HH:mm:ss');
              break;
              case 4://'Text':
              case 3://'Int':
                  output = pcrAnswerRecord.freeTypingValue;
              break;
              case 2://'Select':
              case 5://'Checkbox':
                  output = pcrAnswerRecord.PcrAnswer.displayLabel;
              break;
              default:
                  output = pcrAnswerRecord.PcrAnswer.displayLabel;
              break;
          }

          return output;
      }

    return {
      restrict: 'A',
      scope:{
        pcrRecord: '='
      },
      link: function(scope, element, attrs) {
        scope.$watch('pcrRecord', function(newValue, oldValue) {
          if(!_.isNil(newValue)){
              var output = [];
              var pcrRecord = newValue;
              var PcrAnswerRecords = pcrRecord.PcrAnswerRecords;
              for(var idx in PcrAnswerRecords){
                  var pcrAnswerRecord = PcrAnswerRecords[idx];
                  output.push(getAnswer(pcrRecord.PcrQuestion.PcrQuestionTypeId, pcrAnswerRecord));
              }

              element.text(output.join(','));
          }
        });
      }
    }
  })
  .directive('vitalSign', function($http){

    function getMeasureStatuses(){
        return $http.get('/MeasureStatuses')
        .then(function(response){
            return _.keyBy(response.data, 'id');
        })
    }

    function getAwarenesses(){
        return $http.get('/Awarenesses')
        .then(function(response){
            return _.keyBy(response.data, 'code');
        })
    }

    function getContants(){
        return getMeasureStatuses()
        .then(function(measureStatusList){
            return getAwarenesses()
            .then(function(awarenessesList){
                return  {
                    measureStatusList: measureStatusList,
                    awarenessesList: awarenessesList
                }
            });
        })
    }

    var contantPromise = getContants();

    function getAnswer(VitalSignTypeId, value, MeasureStatusId){
        return contantPromise
        .then(function(constants){

            var output = '';
            if(MeasureStatusId==1){
                switch(VitalSignTypeId){
                    case 1:
                        output = constants.awarenessesList[value].name;
                    break;
                    case 2:
                    case 3:
                    case 4:
                    case 5:
                    case 6:
                    case 7:
                    case 11:
                    case 12:
                        output = value;
                    break;
                    case 8:
                        output = 'E'+value;
                    break;
                    case 9:
                        output = 'V'+value;
                    break;
                    case 10:
                        output = 'M'+value;
                    break;
                }

            }else{
                output = constants.measureStatusList[MeasureStatusId].name
            }

            return output;
        })
    }

    return {
      restrict: 'A',
      scope:{
        data: '=',
      },
      link: function(scope, element, attrs) {
        scope.$watch('data', function(newValue, oldValue) {
          if(!_.isNil(newValue)){
              var vitalSign = newValue;
              getAnswer(vitalSign.VitalSignTypeId, vitalSign.value, vitalSign.MeasureStatusId)
              .then(function(output){
                  element.text(output);
              });
          }
        });
      }
    }
  })
  .directive('imageData', function($http, $sce, AuthService){
    function getImageDataByDispatchRecordUuid(dispatchRecordUuid){
      return $http.get('/EcgImages/OfDispatchRecord/'+dispatchRecordUuid)
      .then(function(response){
        return response.data;
      })
    }

    return {
      restrict: 'E',
      // template: '<div ng-repeat="img in imageData"><div style="position:relative;padding-top:50%;width:100%;"><div style="position:absolute;top:0px;left:0px;bottom:0px;right:0px;" ng-switch="img.imageData.mimeType"><embed ng-switch-default style="width:100%;height:100%;" ng-src="{{img.url}}"></embed><img ng-switch-when="image/jpeg" style="max-width:100%;max-height:100%;" ng-src="{{img.url}}"></img></div></div></div>',
      template: '<div ng-repeat="img in imageData"><img ng-src="{{img.url}}" style="max-width:100%;max-height:100%;""></div>',
      scope:{
        dispatchRecordUuid: '=',
      },
      link: function(scope, element, attrs) {
        scope.$watch('dispatchRecordUuid', function(newValue, oldValue) {
          if(!_.isNil(newValue)){
            var dispatchRecordUuid = newValue;
            return getImageDataByDispatchRecordUuid(dispatchRecordUuid)
            .then(function(results){
              for(var i in results){
                var result = results[i];
                var token = AuthService.getToken();
                result.url = $sce.trustAsResourceUrl(result.url+"?token="+token)
              }
              scope.imageData = results;
            })
          }
        });
      }
    }

  })
  .directive('vitalsignVideo', function($http, $sce, AuthService, $window){
    var configPromise = getConfig();
    var imageTypePromise = getImageType();
    var videoTypePromise = getVideoType();
    function getConfig(){
      return $http.get('/config')
      .then(function(response){
        return response.data;
      })
    }
    function getImageType(){
      return configPromise
      .then(function(config){
        var url = config.vitalSignVideoServer+'/imageTypes';
        return $http.get(url)
      })
      .then(function(response){
        return response.data;
      })
    }
    function getVideoType(){
      return configPromise
      .then(function(config){
        var url = config.vitalSignVideoServer+'/videoTypes';
        return $http.get(url)
      })
      .then(function(response){
        return response.data;
      })
    }


    function getDataByPcrUuid(uuid, imageTypeIds, videoTypeIds){
      return $http.get('/Pcrs/vitalSignVideoDataOf/'+uuid,{
        params: {
          imageTypeIds: imageTypeIds,
          videoTypeIds: videoTypeIds
        },
        paramSerializer: '$httpParamSerializerJQLike'
      })
      .then(function(response){
        return response.data;
      })
    }

    return {
      restrict: 'E',
      template:
`
<h3>照片</h3>
<div ng-repeat="(typeId, images) in imageData">
  <div class="row">
    <div class="col-md-12">
      <h4>{{imageTypeMap[typeId].name}}</h4>
    </div>
  </div>
  <div class="row">
    <div class="col-md-6" ng-repeat="img in images">
      <img ng-src="{{img.url}}" style="max-width:100%;max-height:100%;" img-orientation ng-click="openImage(img.url)">
    </div>
  </div>
</div>
<h3>錄影</h3>
<div ng-repeat="(typeId, videos) in videoData">
  <div class="row">
    <h4>{{videoTypeMap[typeId].name}}</h4>
  </div>
  <div class="row">
    <div class="col-md-6" ng-repeat="vid in videos">
      <video ng-src="{{vid.url}}" controls></video>
    </div>
  </div>
</div>
`,
      scope:{
        options: '='
      },
      link: function(scope, element, attrs) {
        scope.openImage = function(url){
          $window.open(url);
        }
        scope.$watch('options', function(newValue, oldValue) {
          if(!_.isNil(newValue)){
            var token = AuthService.getToken();
            var PcrUuid = newValue.PcrUuid;
            var imageTypeIds = newValue.imageTypeIds;
            var videoTypeIds = newValue.videoTypeIds;
            return imageTypePromise
            .then(function(imageTypes){
              scope.imageTypeMap = _.keyBy(imageTypes, 'id');
            })
            .then(function(){
              return videoTypePromise
            })
            .then(function(videoTypes){
              scope.videoTypeMap = _.keyBy(videoTypes,'id');
            })
            .then(function(){
              return getDataByPcrUuid(PcrUuid, imageTypeIds, videoTypeIds)
            })
            .then(function(results){
              for(var dataType in results){
                var data = results[dataType]
                for(var typeId in data){
                  var group = data[typeId];
                  for(var i in group){
                    var item = group[i];
                    item.url = $sce.trustAsResourceUrl(item.url+"?token="+token)
                  }
                }
              }
              scope.imageData = results.image;
              scope.videoData = results.video;
            })
          }
        });
      }
    }

  })
  .directive('imgOrientation', function(){
    return {
      restrict: 'A',
      link: function(scope, element/*, attrs*/) {
        function setTransform(transform) {
          element.css('-ms-transform', transform);
          element.css('-webkit-transform', transform);
          element.css('-moz-transform', transform);
          element.css('transform', transform);
        }

        var parent = element.parent();
        $(element).bind('load', function() {
          EXIF.getData(element[0], function() {
            var orientation = EXIF.getTag(element[0], 'Orientation');
            var height = element.height();
            var width = element.width();
            if (orientation && orientation !== 1) {
              switch (orientation) {
                case 2:
                  setTransform('rotateY(180deg)');
                  break;
                case 3:
                  setTransform('rotate(180deg)');
                  break;
                case 4:
                  setTransform('rotateX(180deg)');
                  break;
                case 5:
                  setTransform('rotateZ(90deg) rotateX(180deg)');
                  if (width > height) {
                    parent.css('height', width + 'px');
                    element.css('margin-top', ((width -height) / 2) + 'px');
                  }
                  break;
                case 6:
                  setTransform('rotate(90deg)');
                  if (width > height) {
                    parent.css('height', width + 'px');
                    element.css('margin-top', ((width -height) / 2) + 'px');
                  }
                  break;
                case 7:
                  setTransform('rotateZ(90deg) rotateY(180deg)');
                  if (width > height) {
                    parent.css('height', width + 'px');
                    element.css('margin-top', ((width -height) / 2) + 'px');
                  }
                  break;
                case 8:
                  setTransform('rotate(-90deg)');
                  if (width > height) {
                    parent.css('height', width + 'px');
                    element.css('margin-top', ((width -height) / 2) + 'px');
                  }
                  break;
              }
            }
          });
        });
      }
    };
  })
  .directive('formAnswerRecord', function(){
      function getAnswer(question, answerRecord){
          var output = '';
          switch(question.FormQuestionTypeId){
              case 1://'DateTime'
                  var dateformat = 'YYYY/MM/DD'
                  var timeformat = 'HH:mm'
                  if(question.customData && question.customData.timeformat){
                    timeformat = question.customData.timeformat;
                  }
                  output = _.isNil(answerRecord.freeTypingValue) ? '' : moment(answerRecord.freeTypingValue).format(dateformat+' '+timeformat);
              break;
              case 6://'Date'
                  var timeformat = 'YYYY/MM/DD'
                  if(question.customData && question.customData.timeformat){
                    timeformat = question.customData.timeformat;
                  }
                  output = _.isNil(answerRecord.freeTypingValue) ? '' : moment(answerRecord.freeTypingValue).format(timeformat);
              break;
              case 11://'Time'
                  var timeformat = 'HH:mm:ss'
                  if(question.customData && question.customData.timeformat){
                    timeformat = question.customData.timeformat;
                  }
                  output = _.isNil(answerRecord.freeTypingValue) ? '' : moment(answerRecord.freeTypingValue).format(timeformat);
              break;
              case 4://'Text'
              case 3://'Int'
              case 9://String
              case 10: // Display
                  output = answerRecord.freeTypingValue;
              break;
              case 2://'Radio'
              case 5://'Checkbox'
              case 7://'Select'
                  output = answerRecord.FormAnswer.displayLabel;
              break;
              default:
                  output = answerRecord.FormAnswer.displayLabel;
              break;
          }

          return output;
      }

    return {
      restrict: 'A',
      scope:{
        record: '='
      },
      link: function(scope, element, attrs) {
        scope.$watch('record', function(newValue, oldValue) {
          if(!_.isNil(newValue)){
              var output = [];
              var record = newValue;
              var answerRecords = record.FormAnswerRecords;
              for(var idx in answerRecords){
                  var answerRecord = answerRecords[idx];
                  output.push(getAnswer(record.FormQuestion, answerRecord));
              }

              element.text(output.join(','));
          }
        });
      }
    }

  })

  .directive('formRepeatSection', function() {

      function processRepeatSection(FormRecords) {
          return _.groupBy(FormRecords, 'sectionIndex');
      }

      return {
          restrict: 'E',
          scope: {
              records: '='
          },
          template:
`<span ng-repeat="(index, section) in repeatSection">
  <span>#{{index}}</span><br>
  <div style="padding-left: 10px;" ng-repeat="sectionRow in section">
      <div ng-if="sectionRow.FormQuestion.FormQuestionTypeId==8"  style="padding-left: 10px;">
          <form-repeat-section records="sectionRow.FormRecords"></form-repeat-section>
      </div>
      <div ng-if="sectionRow.FormQuestion.FormQuestionTypeId!=8">
      {{sectionRow.FormQuestion.displayLabel}}:<span form-answer-record record="sectionRow"></span>
      </div>
  </div>
</span>`,
          link: function(scope, element, attrs) {
              scope.repeatSection = processRepeatSection(scope.records)
          }
      }
  })

  .directive('ohcaFormStatus', function() {
    return {
      restrict: 'E',
      scope: {
        pcr: '=',
        bundleCountField: '@',
        completeCountField: '@'
      },
      link: function(scope, element, attrs) {
        scope.$watch('pcr', function(newValue, oldValue) {
          if (newValue) {
            var pcr = newValue;
            if (pcr[scope.bundleCountField]==0) {
              // PCR已取消
              element.text('未填寫');
            } else {
              if (pcr[scope.completeCountField] == 0) {
                // 拒絕送醫
                element.text('追蹤中');
              } else {
                element.text('已完成');
              }
            }
          }
        });
      }
    }
  })

  .directive('hospitalBacktracking', function($http, $q) {
    var configPromise = getConfig();
    function getConfig(){
      return $http.get('/config')
      .then(function(response){
        return response.data;
      })
    }


    function getHospitalBacktracking(recordUuid){
      return getHospitalDispatch(recordUuid)
      .then(function(results){
        if(results.length>0){
          var theDispatch = results[0]
          return getFormBundle(theDispatch.FormBundleUuid)
        }else{
          return null;
        }
      })
    }

    function getHospitalDispatch(recordUuid) {
      return configPromise
      .then(function(config){
        var url = config.HospitalServer + '/Dispatches'
        return $http.get(url,{
          params: {
            recordUuid: recordUuid
          }
        })
      })
      .then(function(response){
        return response.data;
      })
    }

    function getFormBundle(FormBundleUuid){
        if(FormBundleUuid==null){
            var deferred = $q.defer()
            deferred.resolve(null);
            return deferred.promise;
        }else{
            return configPromise
            .then(function(config){
              var url = config.HospitalServer+'/FormBundles/getContentOf/'+FormBundleUuid
              return $http.get(url)
            })
            .then(function(response){
                return response.data;
            })
        }
    }


    return {
        restrict: 'E',
        scope: {
            uuid: '='
        },
        template:
`
<div class="panel panel-primary">
  <div class="panel-heading">
    <h1 class="panel-title">醫院回溯:{{ hospitalBacktracking.FormCategory.displayLabel }}</h1>
    <span>
    最後更新:{{ hospitalBacktracking.updatedAt | date:'yyyy-MM-dd HH:mm:ss' }}
    </span>
  <i ng-if="hospitalBacktracking.isComplete==false">未完成</i>
  </div>
  <div class="panel-body">
    <table class="table table-bordered table-striped table-hover">
    <thead>
      <tr>
        <th>題目</th>
        <th>答案</th>
      </tr>
    </thead>
    <tr ng-repeat="row in hospitalBacktracking.FormRecords">
      <td>
        {{ row.FormQuestion.displayLabel }} {{row.sectionIndex}}
      </td>
      <td>
        <span form-answer-record record="row"></span>
        <form-repeat-section records="row.FormRecords"></form-repeat-section>
      </td>
    </tr>
    </table>
  </div>
</div>
`,
        link: function(scope, element, attrs) {
          scope.$watch('uuid', function(newValue, oldValue) {
            if (newValue) {
              var PcrUuid = scope.uuid;
              getHospitalBacktracking(PcrUuid)
              .then(function(result){
                scope.hospitalBacktracking = result
              })
            }
          });
        }
    }
  })
  .directive('ohcaFormBundle', function() {
    return {
      restrict: 'E',
      scope: {
        pcr: '=',
        formbundle: '=',
        edit: '=',
        delete: '='
      },
      template:`
<div class="row panel panel-primary" ng-if="FormBundle">
  <div class="panel-heading">
    <h1 class="panel-title">
      {{ FormBundle.FormCategory.displayLabel }}
    </h1>
    <span>
      最後更新:{{ FormBundle.updatedAt | date:'yyyy-MM-dd HH:mm:ss' }}
    </span>
    <i ng-if="FormBundle.isComplete==false">未完成</i>
  </div>

  <div class="panel-body">
    <table class="table table-bordered table-striped table-hover">
      <thead>
        <tr>
          <th>題目</th>
          <th>答案</th>
        </tr>
      </thead>

      <tr ng-repeat="row in FormBundle.FormRecords">
        <td>
          {{ row.FormQuestion.displayLabel }} {{row.sectionIndex}}
        </td>
        <td>
          <span form-answer-record record="row"></span>
          <form-repeat-section records="row.FormRecords"></form-repeat-section>
        </td>
      </tr>
    </table>
    <button ng-show="edit" class="btn btn-primary" ng-click="editBacktrackingModal(Pcr, FormBundle)">編輯內容</button>
    <button ng-show="delete" class="btn btn-danger" ng-click="deleteBacktracking(FormBundle.uuid)">刪除重寫</button>
  </div>
</div>
`,
      link: function(scope, element, attrs) {
        scope.$watch('pcr', function(newValue, oldValue) {
          if (newValue) {
            scope.Pcr = newValue;
          }
        }, true);

        scope.$watch('formbundle', function(newValue, oldValue){
          scope.FormBundle = scope.formbundle;
        },true)

        scope.$watch('edit', function(newValue, oldValue){
          if( newValue ){
            scope.editBacktrackingModal = scope.edit;
          }
        },true)

        scope.$watch('delete', function(newValue, oldValue){
          if( newValue ){
            scope.deleteBacktracking = scope.delete;
          }
        },true)


      }
    }
  })
.directive(
    "checkNotIdle",
    function( $document, $parse ){
        // I connect the Angular context to the DOM events.
        var linkFunction = function( $scope, $element, $attributes ){
            // Get the expression we want to evaluate on the
            // scope when the document is clicked.
            var scopeExpression = $attributes.checkNotIdle;
            // Compile the scope expression so that we can
            // explicitly invoke it with a map of local
            // variables. We need this to pass-through the
            // click event.
            //
            // NOTE: I ** think ** this is similar to
            // JavaScript's apply() method, except using a
            // set of named variables instead of an array.
            var invoker = $parse( scopeExpression );
            // Bind to the document click event.
            $document.on(
                "click keyup scroll",
                function( event ){
                    // When the click event is fired, we need
                    // to invoke the AngularJS context again.
                    // As such, let's use the $apply() to make
                    // sure the $digest() method is called
                    // behind the scenes.
                    $scope.$apply(
                        function(){
                            // Invoke the handler on the scope,
                            // mapping the jQuery event to the
                            // $event object.
                            invoker(
                                $scope,
                                {
                                    $event: event
                                }
                            );
                        }
                    );
                }
            );
            // TODO: Listen for "$destroy" event to remove
            // the event binding when the parent controller
            // is removed from the rendered document.
        };
        // Return the linking function.
        return( linkFunction );
    }
)
.directive('idleTimerCountDown', function($rootScope){
  return {
    restrict: 'A',
    link: function(scop, element, attrs) {
      var unregister = $rootScope.$on('idleTimer.countDown', function(event, arg){
        // console.log('idleTimerCountDown:', arg)
        element.text(arg);
      })
      scop.$on('$destroy', function(){
        unregister();
      })

    }
  }
})


