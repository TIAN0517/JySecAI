CONTROLLERS.controller('CaseDetailPrintCtrl', function($q, $modal, $scope, $state,
    NgTableParams, $http, $element, $stateParams, $timeout, AuthService, PcrQuestionService, $window, PrintFormatSvc) {

var script = document.querySelector('script[src="https://maps.google.com/maps/api/js?key=AIzaSyB-ZbIMj6Now6cnwor9QRwjx6zEnzdYvU4"]');
if (script) {
    script.parentNode.removeChild(script);
}

    var vitalSignVideoServer;
    // var videoPath;
    // var historyVideoPath;
    var imagePath;

    $scope.authToken = AuthService.getToken();
    $scope.datetime = new Date().getTime();

    $scope.colspanA = {
      "1":6,
      "2":3,
      "3":2,
      "4":2,
      "5":1,
      "6":1,
    };
    $scope.colspanB = {
      "1":4,
      "2":2,
      "3":2,
      "4":1
    };
    $scope.levels = {
			"0":"無燒燙傷",
			"1":"一級",
			"2":"二級",
			"3":"三級"
		}
    $scope.vm = {} ;

    $scope.panels = [
    {
      "title": "派遣資訊",
      "template": "templates/tp/caseDetail/p_dispatchInfo.html"
    },
    {
      "title": "案件資訊",
      "template": "templates/tp/caseDetail/p_caseData.html"
    },
    {
      "title": "救護紀錄",
      "template": "templates/tp/caseDetail/p_assessmentDataA.html"
    },
    // {
    //   "title": "垂片資訊",
    //   "template": "templates/tp/caseDetail/ambData.html"
    // },
    {
      "title": "生命徵象",
      "template": "templates/tp/caseDetail/p_vitalSigns.html"
    },
    {
      "title": "補述欄",
      "template": "templates/tp/caseDetail/p_caseDescription.html"
    },
    {
      "title": "檢傷/燒燙傷圖",
      "template": "templates/tp/caseDetail/diagramAndBurn.html"
    },

    // {
    //   "title": "醫療機構",
    //   "template": "templates/tp/caseDetail/p_sendHospitalInfo.html"
    // },
    // {
    //   "title": "心電圖",
    //   "template": "templates/tp/caseDetail/ecgPrint.html"
    // },
    // {
    //   "title": "事件",
    //   "template": "templates/tp/caseDetail/event.html"
    // },
    // {
    //   "title": "波形",
    //   "template": "templates/tp/caseDetail/waveFormPrint.html"
    // },
    // {
    //   "title": "燒傷圖",
    //   "template": "templates/tp/caseDetail/burnData.html"
    // },
    {
      "title": "簽名欄",
      "template": "templates/tp/caseDetail/p_signInfo.html"
    },
    // {
    //   "title": "醫護人員簽名",
    //   "template": "templates/tp/caseDetail/nurseData.html"
    // }
    // {
    //   "title": "檢傷圖",
    //   "template": "templates/tp/caseDetail/diagramData.html"
    // },


    ];

    $scope.spec =
      {
        "title": "新北市政府消防局特殊表",
        "template": "templates/tp/caseDetail/p_assessmentDataB.html"
      }


    var isShow = $stateParams.isShow;

    if (isShow == '1') {
        $scope.isShowButton = true
    } else {
        $scope.isShowButton = false;
    }

    $scope.print = function() {
      var role = AuthService.getCurrentUser().role;

      switch(role){
        case 'HOSPITAL':
          var caseSN = $scope.CaseRecordData.recordUuid +'-' + $scope.DispatchRecordData.serialNumber
            + '-' + $scope.PcrData.serialNumber;
          $window.open('/Pcrs/getPdfByCaseSN/'+caseSN+'?token='+$scope.authToken);
        break;
        default:
          $window.open('/Pcrs/genlatestPdf/'+$scope.PcrData.uuid+'?token='+$scope.authToken);
      }
    }

    var MIN_AREA = 8;
    var ageInMonth = 1;
    var ageType = 1;
    var svgFiles = {
        "1": "burnAdult.svg",
        "2": "burnKid.svg",
        "3": "burnInfant.svg"
    }

    $scope.hasTPList = {
        false: '否',
        true: '是'
    }

    $scope.provideTelephone = {
        false: '否',
        true: '是'
    }

    $scope.unableToSign = {
        false: '否',
        true: '是'
    }

    $scope.ambAnswer = {
        false: '否',
        true: '是'
    }

    var highLightColor;

    var bodyPart;

    var deferred = $q.defer();
    var Promise = deferred.promise;
    var PcrUuidPromise = getPcrUuid();

    function getPcrUuidByCaseSN(caseSN){
      return $http.get('/Pcrs/PcrUuidByCaseSN/'+caseSN)
      .then(function(response){
        return response.data.uuid;
      })
    }

    function getPcrUuid(){
      var pcrUuid = $stateParams.uuid;
      var caseSN = $stateParams.caseSN;
      if(pcrUuid){
        return $q.when(pcrUuid);
      }else{
        return getPcrUuidByCaseSN(caseSN);
      }
    }

    function initData() {
        return $http.get('/Sexs/')
            .then(function(response) {
                $scope.sexList = response.data;
                return $http.get('/Relationships/')
            })
            .then(function(response) {
                $scope.RelationshipList = response.data;
                return $http.get('/EmtLevels/')
            })
            .then(function(response) {
                $scope.EmtLevels = _.keyBy(response.data,'id');
                return $http.get('/PcrCategories/')
            })
            .then(function(response) {
                $scope.PcrCategorieList = response.data;
                return $http.get('/DiagramInjuries/')
            })
            .then(function(response) {
                $scope.injuryTypeList = _.keyBy(response.data, 'id');
                return $http.get('/BurnBodyPart/getBurnBodyPart/' + ageType)
                    // return $http.get('json/burnBodyPart.json')
            })
            .then(function(response) {
                bodyParts = _.keyBy(response.data, 'name');
                return $http.get('/BurnLevels/')
            })
            .then(function(response) {
                highLightColor = _.keyBy(response.data, 'id');
                return $http.get('/Statuses/')
            })
            .then(function(response) {
                $scope.statusesList = _.keyBy(response.data, 'id');
                return $http.get('/DeathAssessments/')
            })
            .then(function(response) {
                $scope.deathAssessmentList = _.keyBy(response.data, 'id');
                return $http.get('/Awarenesses/')
            })
            .then(function(response) {
                $scope.awarenessList = _.keyBy(response.data, 'id');
                return $http.get('/Breaths/')
            })
            .then(function(response) {
                $scope.breathList = _.keyBy(response.data, 'id');
                return $http.get('/Symptoms/')
            })
            .then(function(response) {
                $scope.symptomList = _.keyBy(response.data, 'id');
            })
    }

    function getConfig() {
        return $http.get('/config')
            .then(function(response) {
                return response.data;
            });
    }

    function dataDispatchRecord() {
        return $http.get('/DispatchRecords/' + $scope.DispatchRecordData.uuid, {
                params: {
                    StatusId: {
                        $in: [8]
                    }
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
            .then(function(response) {
                console.log('DispatchRecords response', response.data)
                return response
            })
            .catch(function(err) {
                console.log('err =', err)
            })
    }



  //AP輸入之VitalSgins
  function getAppVitalSigns(){
      return new NgTableParams({
          sorting: { datetime: 'desc' }
      }, {
      filterDelay: 300,
      pages: [],
      counts: [],
      getData: function(params) {
        var deferred = $q.defer();
        $scope.anyPageBusy = deferred.promise;
        // console.log(params.sorting())
        var url = params.url();
        var limit = url.count,
            skip = url.count * (url.page - 1);
        var sortString;
        var measureStatuses ;
        // 如果使用 epilogue 免費 api sort需要做調整
        // 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
        // sortString = params.sorting();

        return PcrUuidPromise
        .then(function(result){
          var pcrUuid = result;
          return $http.get('/MeasureStatuses',{})
          .then(function(response){
            measureStatuses = _.keyBy(response.data,'id') ;
            return $http.get('/VitalSignSets', {
                params:{
                  PcrUuid:pcrUuid,
                  sort: 'VitalSignSetTypeId'
                },
                paramSerializer: '$httpParamSerializerJQLike'
            })
          })
          .then(function(response) {
            var appVitalSignsRaw = response.data;
            var vitalTemplate = {
              uuid:null,
              Awareness:null,
              RespiratoryRate:null,
              Pulse:null,
              SystolicBP:null,
              DiastolicBP:null,
              temp:null,
              SpO2:null,
              GCS_E:null,
              GCS_V:null,
              GCS_M:null,
              '替代測量':null,
              ETCO2:null
            }
            var appVitalSigns = [];
            angular.forEach(appVitalSignsRaw,function(appVitalSign){

              var vitalItem = angular.copy(vitalTemplate);
              angular.forEach(appVitalSign.VitalSigns,function(item){

                if ( vitalTemplate.hasOwnProperty(item.VitalSignType.name)){
                  if ( item.MeasureStatusId > 1 ){
                    vitalItem[item.VitalSignType.name] = measureStatuses[item.MeasureStatusId].name ;
                  }else{
                    vitalItem[item.VitalSignType.name] = item.value ;
                  }
                  // vitalSignInfo
                  if( !_.isNil(item.VitalSignInfos) && !_.isEmpty(item.VitalSignInfos)){
                      for(var idx in item.VitalSignInfos){
                          if(vitalItem[item.VitalSignType.name] == ''){
                              vitalItem[item.VitalSignType.name] = item.VitalSignInfos[idx].name;
                          }else{
                              vitalItem[item.VitalSignType.name] = vitalItem[item.VitalSignType.name] + ' ' + item.VitalSignInfos[idx].name;
                          }
                      }
                  }


                }
              })
              vitalItem["uuid"] = appVitalSign.uuid;
              vitalItem["datetime"] = appVitalSign.datetime;
              vitalItem["VitalSignSetType"] = appVitalSign.VitalSignSetType? appVitalSign.VitalSignSetType.name : '--';
              appVitalSigns.push(vitalItem);
            })

            deferred.resolve()
            return appVitalSigns;
          })
        })
        .catch(function(err) {
          deferred.resolve();
          console.log('getAppVitalSigns err =', err)
        })
      }
    })
  }

    function getPcrsData() {
        var pcrUuid;
        return getPcrUuid()
            .then(function(result) {
                pcrUuid = result;
                return getConfig()
                    .then(function(response) {
                        vitalSignVideoServer = response.vitalSignVideoServer;
                        // videoPath = response.VideoPath;
                        // historyVideoPath = response.historyVideoPath;
                        imagePath = response.imagePath;
                        // console.log("videoPath", videoPath)
                        // console.log("historyVideoPath", historyVideoPath)
                        console.log("imagePath", imagePath)
                        return $http.get('/Pcrs/' + pcrUuid)
                    })
                    .then(function(response) {
                        //基本資訊-救護單資訊(Pcrs)
                        $scope.PcrData = response.data;
                        if (!_.isNil($scope.PcrData.age)) {
                            var ageInMonth = $scope.PcrData.age;
                            if (ageInMonth < 12) {
                                ageType = 3;
                            } else if (ageInMonth < 12 * 14) {
                                ageType = 2;
                            } else {
                                ageType = 1;
                            }
                        }
                        $scope.svgFilename = svgFiles[ageType];
			$scope.PcrData.age = Math.floor(($scope.PcrData.age / 12));
                        // console.log("PcrData=", $scope.PcrData);
                        //基本資訊-案件資訊(CaseRecords)
                        $scope.CaseRecordData = $scope.PcrData.DispatchRecord.CaseRecord;
                        //基本資訊-車輛資訊(DispatchRecords-Ambulances-Branches)
                        $scope.DispatchRecordData = $scope.PcrData.DispatchRecord;
                        $scope.AmbulanceData = $scope.PcrData.DispatchRecord.Ambulance;
                        $scope.BranchData = $scope.PcrData.DispatchRecord.Branch;
                        //基本資訊-補述欄
                        $scope.CaseDescriptions = $scope.PcrData.CaseDescriptions;
                        //基本資訊-後送醫院
                        $scope.HospitalData = $scope.PcrData.Hospital;
                        //評估資訊-檢傷圖(DiagramRecords)
                        $scope.DiagramDatas = $scope.PcrData.DiagramRecords;
                        //評估資訊-燒傷圖(BurnRecords)
                        $scope.BurnDatas = $scope.PcrData.BurnRecords;
                        //
                        $scope.Properties = $scope.PcrData.Properties;

                        $scope.Emts = $scope.PcrData.Emts;
                        //垂片資訊
                        var ambs = $scope.PcrData.Ambs;
                        $scope.convertAmbs = {};
                        angular.forEach(ambs, function(data) {
                            var AmbCategory = data.AmbCategory.name;
                            if (_.isEmpty($scope.convertAmbs[AmbCategory])) {
                                $scope.convertAmbs[AmbCategory] = []
                            }
                            $scope.convertAmbs[AmbCategory].push(data)
                        })
                        console.log("convertAmbs", $scope.convertAmbs);
                        // 整理後送醫院資訊
                        if (!$scope.PcrData.PcrArrivedHospitalHistories) $scope.PcrData.PcrArrivedHospitalHistories = [];
                        // 無抵達醫院記錄歷程, 但有抵達醫院, 從最後一筆補
                        if ($scope.PcrData.PcrArrivedHospitalHistories.length == 0 && $scope.PcrData.arrivedHospitalAt) {
                          $scope.PcrData.PcrArrivedHospitalHistories.push({
                            arrivedHospitalAt: $scope.PcrData.arrivedHospitalAt,
                            hospitalName: $scope.PcrData.Hospital ? $scope.PcrData.Hospital.name : $scope.PcrData.otherHospita
                          });
                        } // if
                        $scope.PcrData.PcrArrivedHospitalHistories.sort(function (a, b) { return moment(b.arrivedHospitalAt).diff(moment(a.arrivedHospitalAt)); });
                    })
                    .then(function() {
                        $scope.AppVitalSigns = getAppVitalSigns();
                        return $http.get('/Awarenesses/');
                    })
                    .then(function(response) {
                        // 清聲痛否
                        $scope.awarenessListApp = _.keyBy(response.data, 'code');
                    })
                    .then(function() {
                        //取得心電圖
                        var query = {
                            'recordUuid': $scope.PcrData.DispatchRecord.uuid,
                            'ImageTypeId': 1
                        }
                        return $http.get(vitalSignVideoServer + '/ImageData', {
                            params: query,
                            paramSerializer: '$httpParamSerializerJQLike'
                        })
                    })
                    .then(function(response) {
                        $scope.showECGs = response.data;
                        $scope.ecgPath = vitalSignVideoServer + imagePath;
                        console.log("showECGs", $scope.showECGs)
                        //取得波形
                        var query = {
                            'recordUuid': $scope.PcrData.DispatchRecord.uuid,
                            'ImageTypeId': 2
                        }
                        return $http.get(vitalSignVideoServer + '/ImageData', {
                            params: query,
                            paramSerializer: '$httpParamSerializerJQLike'
                        })
                    })
                    .then(function(response) {
                        $scope.showWaveForms = response.data;
                        $scope.waveFormPath = vitalSignVideoServer + imagePath;
                        console.log("showWaveForms", $scope.showWaveForms)
                    })
                    .catch(function(err) {
                        console.log(err);
                    })
            });
    }

    //填寫檢傷資料
    //caseType=內科外科的id

    function calculatePercentage(records){
			var percentage = { "1": 0, "2": 0, "3": 0 }

			angular.forEach(records, function(record){
				console.log("percentage",percentage, record.BurnLevelId, bodyParts[record.BurnBodyPart.name].percent);
				if(record.BurnLevelId != "0"){
					// percentage[record.BurnLevelId] += bodyParts[key].percent;
					percentage[record.BurnLevelId] += record.percent ;
				}
			});
			return percentage;
		}

    function addMark(id, X, Y, injuryType, caseType, bodyPart, areaW, areaH, svgId) {
        var sizeW = MIN_AREA + parseInt(areaW);
        var sizeH = MIN_AREA + parseInt(areaH);
        var color = $scope.injuryTypeList[injuryType].color;
        var injuryText = $scope.injuryTypeList[injuryType].name ;
        var mark;

        if (caseType == 1) {
            mark = d3.select(svgId).append("g").attr("id", id)
            mark.append("ellipse")
                .attr("rx", sizeW)
                .attr("ry", sizeH)
                .style("fill", color)
                .style("stroke", "#000000")
                .style("stroke-width", 1)
                .attr("cx", X)
                .attr("cy", Y);

                mark.append("text")
                .style("fill","#FFFF00")
                .attr("x",X-sizeW/2)
                .attr("y",Y+sizeH/2)
                .attr("class","injury-text")
                .text(areaW+'x'+areaH + ' ' +injuryText);
        } else {
            mark = d3.select(svgId).append("g").attr("id", id)
            mark.append("rect")
                .style("fill", color)
                .style("stroke", "#000000")
                .style("stroke-width", 1)
                .attr("x", X - sizeW * 2 / 2)
                .attr("y", Y - sizeH * 2 / 2)
                .attr("width", sizeW * 2)
                .attr("height", sizeH * 2);

                mark.append("text")
                .style("fill","#FFFF00")
                .attr("x",X-sizeW/2)
                .attr("y",Y+sizeH/2)
                .attr("class","injury-text")
                .text(areaW+'x'+areaH + ' ' +injuryText)
        }
    };
    //填寫檢傷資料

    //填寫燒傷圖資料
    function highlightPart(bodyPart, level, svgId) {
        var graphs;
        if (bodyParts[bodyPart]["BurnSubBodyParts"].length > 0) {
            graphs = bodyParts[bodyPart]["BurnSubBodyParts"];
        } else {
            graphs = [{ name: bodyPart }];
        }
        angular.forEach(graphs, function(part) {
            console.log('high light', part.name);
            if (level == "0") {
                d3.selectAll(svgId)
                    .select("#" + part.name).style("fill-opacity", 0);
            } else {
                d3.selectAll(svgId)
                    .select("#" + part.name).style("fill-opacity", 0.9);
                // console.log('highLightColor[level]=', highLightColor[level].color);
                d3.selectAll(svgId)
                    .select("#" + part.name).style("fill", highLightColor[level].color);
            }
        });
    };
    //填寫燒傷圖資料

    //呈現檢傷圖資訊
    $scope.svgDiagramLoaded = function() {
        Promise.then(function() {
            var origW = d3.select("#svgDiagram").attr("width");
            var origH = d3.select("#svgDiagram").attr("height");
            var W = origW*0.6;
            var H = W* (origH/origW);
            //暫時先不管圖片的Ｗ跟Ｈ
            // var W = document.getElementById("diagarmSvg").clientWidth;
            // var H = document.getElementById("diagarmSvg").clientHeight
            console.log('W', W, 'H', H);
            d3.select("#svgDiagram")
                .attr("width", W)
                .attr("height", H)
                .attr("viewBox", "0,0," + origW + "," + origH);

            $scope.$watch('PcrData.DiagramRecords', function(newValue, oldValue) {
              angular.forEach(newValue, function(record) {
                  addMark(record.id, record.coordX, record.coordY,
                      record.DiagramInjury.id,
                      record.DiagramInjury.DiagramInjuryTypeId,
                      record.DiagramBodyPart.name,
                      record.width,
                      record.height,
                      "#svgDiagram");
              });
            })
        })
    };
    //呈現檢傷圖資訊

    //呈現燒燙傷資訊
    $scope.svgBurnLoaded = function() {
        Promise.then(function() {
            var origW = d3.select("#svgBurn").attr("width");
            var origH = d3.select("#svgBurn").attr("height");
            var W = origW*0.5;
            var H = W* (origH/origW);
            //暫時先不管圖片的Ｗ跟Ｈ
            // var W = document.getElementById("burnSvg").clientWidth;
            // var H = document.getElementById("burnSvg").clientHeight;
            console.log('W', W, 'H', H);

            d3.select("#svgBurn")
                .attr("width", W)
                .attr("height", H)
                .attr("viewBox", "0,0," + origW + "," + origH);

            $scope.$watch('BurnDatas', function(newValue, oldValue) {
              angular.forEach(newValue, function(record, key) {
                  highlightPart(record.BurnBodyPart.name, record.BurnLevelId, "#svgBurn");
              });

              $scope.burnPercentage = calculatePercentage(newValue);
            })
        })
    };
    //呈現燒燙傷資訊


    //生命徵象
    var vitalSignSearchParams = {};

    function checkFound(found){
      if (found && (found.questionTypeId== 2 || found.questionTypeId== 5) && found.answer ){
        for (var x = 0 ; x < found.answer.length ; x++){
          if(found.answer[x].isSelected){
            return true ;
          }
        }
      }else{
        if (found.answer){
          return true ;
        }
      }
      return false ;
    }

    function checkSpecShow(blockObj,qarecordmap){
      for (var i = 0 ; i < blockObj.length ; i++){
        for (var j = 0; j < blockObj[i].length; j++) {
          var qObj = blockObj[i][j] ;
          if ( qObj.type == 4 || qObj.type == 5 ){
            for (var k = 0; k < qObj.codes.length; k++) {
              // var found = PrintFormatSvc.findInQARecord(qObj.codes[k],qarecord) ;
              // if (found && checkFound(found)){
              //   return true ;
              // }
              var code = qObj.codes[k]
              // type 4 或 5 的資料結構 codes[k] = { code: "xxx", text: "ooo" }
              if ( qarecordmap[code.code] ){
                return true
              }
            }
          }else {
            // var found = PrintFormatSvc.findInQARecord(qObj.code,qarecord) ;
            // if (found && checkFound(found)){
            //   return true ;
            // }
            var code = qObj.code ;
            if ( qarecordmap[code] ){
              return true
            }
          }
        }
      }
      return false ;
    }

    $scope.showVolunteerName = function(record) {
      return record.AssistantRoleId === 5 && record.Volunteer;
    }

    $scope.showBlock = {} ;
    var pcrVersionId ;
    var pcrUuid;
    initData()
        .then(function() {
            deferred.resolve();
        })
	.then(function() {
          return getPcrsData()
        })
        .then(function() {
          return PcrUuidPromise
          .then(function(result){
             pcrUuid = result;
            return $http.get('/PcrBundles?PcrUuid='+ pcrUuid ) ;
          })
        })
        .then(function(result){
          $scope.vm.qaRecordMap = PrintFormatSvc.convertBundles2Map(result.data) ;
          // console.log("$scope.vm.pcrBundles",$scope.vm.qaRecordMap);
          return $http.get('/json/printFormatA.json')
        })
        .then(function(result){
          $scope.vm.printFormatA = result.data ;
          return $http.get('/json/printFormatB1.json')
        })
        .then(function(result){
          $scope.vm.printFormatB1 = result.data ;
          $scope.showBlock['B1'] = checkSpecShow($scope.vm.printFormatB1, $scope.vm.qaRecordMap);
          return $http.get('/json/printFormatB2.json')
        })
        .then(function(result){
          $scope.vm.printFormatB2 = result.data ;
          $scope.showBlock['B2'] = checkSpecShow($scope.vm.printFormatB2, $scope.vm.qaRecordMap);
          return $http.get('/json/printFormatB3.json')
        })
        .then(function(result){
          $scope.vm.printFormatB3= result.data ;
          $scope.showBlock['B3'] = checkSpecShow($scope.vm.printFormatB3, $scope.vm.qaRecordMap);
          return $http.get('/json/printFormatB4.json')
        })
        .then(function(result){
          $scope.vm.printFormatB4 = result.data ;
          $scope.showBlock['B4'] = checkSpecShow($scope.vm.printFormatB4, $scope.vm.qaRecordMap);
          return $http.get('/json/printFormatB5.json')
        })
        .then(function(result){
          $scope.vm.printFormatB5 = result.data ;
          $scope.showBlock['B5'] = checkSpecShow($scope.vm.printFormatB5, $scope.vm.qaRecordMap);
          return $http.get('/json/printFormatB6.json')
        })
        .then(function(result){
          $scope.vm.printFormatB6 = result.data ;
          $scope.showBlock['B6'] = checkSpecShow($scope.vm.printFormatB6, $scope.vm.qaRecordMap);
          return $http.get('/json/printFormatB7.json')
        })
        .then(function(result){
          $scope.vm.printFormatB7 = result.data ;
          $scope.showBlock['B7'] = checkSpecShow($scope.vm.printFormatB7, $scope.vm.qaRecordMap);
          return $http.get('/json/printFormatB8.json')
        })
        .then(function(result){
          $scope.vm.printFormatB8 = result.data ;
	  console.log($scope.vm.printFormatB8)
          $scope.showBlock['B8'] = checkSpecShow($scope.vm.printFormatB8, $scope.vm.qaRecordMap);
          return $http.get('/json/printFormatB9.json')
        })
        .then(function(result){
          $scope.vm.printFormatB9 = result.data ;
          $scope.showBlock['B9'] = checkSpecShow($scope.vm.printFormatB9, $scope.vm.qaRecordMap);
          return $http.get('/json/printFormatB10.json')
        })
        .then(function(result){
          $scope.vm.printFormatB10 = result.data ;
          $scope.showBlock['B10'] = checkSpecShow($scope.vm.printFormatB10, $scope.vm.qaRecordMap);
          return $http.get('/PcrVersions?isDefault=true')
        })
        .then(function(result){
          var newestPcrVersionId = result.data[0].id ;

          return $http.get('/pcrs/getVersionOf/' + pcrUuid)
          .then(function(result){
            if(result && result.data){
              pcrVersionId = result.data;
            }else{
              pcrVersionId = newestPcrVersionId;
            }
            return $http.get('/pcrQuestionsAndAnswers?count=250&PcrVersionId='+pcrVersionId) ;
          })
        })
        .then(async function(result){
          try {
            if (!$scope.showBlock['B8']) return result;
            var target = result.data.find(row => row.code === 'AT_STEMI12A');
            if (target.PcrAnswers[0].displayLabel) return result;
            var url = (await getConfig()).vitalSignVideoServer;
            var res = await $http.get(`${url}/extEcg/airesult/${$scope.PcrData.DispatchRecordUuid}`);
            target.PcrAnswers[0].displayLabel = formatAIMessage(res.data[0].ImageDataAIResults)
          } catch (err) {
            console.log(err.message)
          } finally {
            return result;
          }
        })
        .then(function(result){
          $scope.vm.questionAnswerMap = _.keyBy(result.data, 'code');
          return $http.get('/PcrQuestions/nextQuestionMap?PcrVersionId='+pcrVersionId) ;
        })
        .then(function(result){
          $scope.vm.nextQuestionMap = result.data ;
          $timeout(function(){
            console.log("DONE");
            $scope.isDone = true;
            $scope.$apply();
          },0);
        })
        .catch(function(err) {
            console.log(err)
        })
});

function formatAIMessage(imageDataAIResults) {
  // ex: 'p.STEMI 5.1%,預測可信度：low;疾病風險：low risk'
  let msg = [];
  // 1.${ai_pred_name} ${ai_pred_value}
  let ai_pred_name = _.find(imageDataAIResults, x => x.code == 'ai_pred_name');
  let ai_pred_value = _.find(imageDataAIResults, x => x.code == 'ai_pred_value');
  if (ai_pred_name && ai_pred_value) msg.push(`${ai_pred_name.value} ${ai_pred_value.value}`);
  // 2.預測可信度：${AI_CONFIDENCE_MAP[confidence]}
  let confidence = _.find(imageDataAIResults, x => x.code == 'confidence');
  if (confidence && AI_CONFIDENCE_MAP[confidence.value]) msg.push(`預測可信度：${AI_CONFIDENCE_MAP[confidence.value]}`);
  // 3.疾病風險：${ai_pred_result}
  let ai_pred_result = _.find(imageDataAIResults, x => x.code == 'ai_pred_result');
  if (ai_pred_result) msg.push(`疾病風險：${ai_pred_result.value}`);
  return msg.join(',');
}
