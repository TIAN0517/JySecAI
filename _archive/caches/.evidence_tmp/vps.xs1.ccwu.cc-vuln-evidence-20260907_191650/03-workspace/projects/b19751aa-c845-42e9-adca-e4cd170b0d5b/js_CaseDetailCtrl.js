CONTROLLERS.controller('CaseDetailCtrl',
	function ($q, $modal, $scope, $state, $http, $element, $stateParams, $timeout, $window,
		NgTableParams, AuthService, PcrQuestionService, $sce) {

		var vitalSignVideoServer;
		var videoPath;
		var historyVideoPath;
		var imagePath;
		var doctorServer;
		var config;

		var videoModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/videoModal.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			// onHide: refreshList
		});

		$scope.authToken = AuthService.getToken();
		$scope.datetime = new Date().getTime()

		$scope.levels = {
			"0": "無燒燙傷",
			"1": "一級",
			"2": "二級",
			"3": "三級"
		}
		$scope.Tabs = [{
			"title": "基本資訊",
			"template": "templates/tp/caseDetail/caseInfo.html"
		}, {
			"title": "評估資訊",
			"template": "templates/tp/caseDetail/assessmentInfo.html"
		}];

		// $scope.Tabs.activeTab = 0;
		// 原本預設打開的activeTab是"基本資訊", 此時"評估資訊"這個tab裡面的內容已經載入
		// 卻還沒有顯示; 所以"拍照/攝影"的這個區塊裡面的圖片暫時width 與 height都是0
		// "imgOrientation" 這個directive就無法正確判斷要不要改變parent的高與寬
		// 因此改成activeTab = 1, 直接先打開"評估資訊"讓裡面的圖片顯示出來，就能取得正確的寬與高了
		$scope.Tabs.activeTab = 0;

		if (AuthService.checkPerm('EPCR_CASE_SCORE')) {
			$scope.isHospital = false;
			$scope.Tabs.push({
				"title": "案件評比",
				"template": "templates/tp/caseDetail/backtracking.html"
			});
		} // if
		else {
			$scope.isHospital = true;
		} // else

		//大隊醫師簽核
		if (AuthService.checkPerm('EPCR_DOCTOR_ORDER')) {
			function getListRequireDoctorOrder(pcrUuid) {
				return $http.get('/pcrs/pcrBlockRequireDoctorOrder/' + pcrUuid)
					.then(function (response) {
						return response.data;
					})
			}

			function setupListRequireDoctorOrder(pcrUuid) {
				return getListRequireDoctorOrder(pcrUuid)
					.then(function (results) {
						$scope.listRequireDoctorOrder = results;
					})
			}


			$scope.Tabs.push({
				"title": "大隊醫師簽核",
				"template": "templates/tp/caseDetail/preMedicalOrder.html"
			});

			function saveDoctorOrder(pcrUuid) {
				return $http.put('/pcrs/doctorOrder/' + pcrUuid)
					.then(function (response) {
						return response.data;
					})
			}
			$scope.saveDoctorOrder = function (pcrUuid) {
				return saveDoctorOrder(pcrUuid)
					.then(function (response) {
						$scope.PcrData.PcrDoctorOrderStatusId = 2
					})
					.catch(function (error) {
						console.log(error);
						alert('無法簽核!');
					});
			}
		}
		//大隊醫師簽核

		$scope.realTimeVideo = {
			"title": "即時影像",
			"template": "templates/tp/caseDetail/caseVideo.html"
		}
		$scope.panels1 = [
			{
				"title": "案件資訊",
				"template": "templates/tp/caseDetail/caseData.html"
			},
			//  {
			//   "title": "車輛資訊",
			//   "template": "templates/tp/caseDetail/carData.html"
			// },
			{
				"title": "救護單資訊",
				"template": "templates/tp/caseDetail/pcrData.html"
			}
		];
		$scope.panels1_2 = [
			// 	{
			// 	"title": "垂片資訊",
			// 	"template": "templates/tp/caseDetail/ambData.html"
			// }, {
			// 	"title": "補述欄",
			// 	"template": "templates/tp/caseDetail/caseDescription.html"
			// }
		];

		$scope.panels1.activePanel = 0;

		$scope.panel2 = [
			{
				"title": "案摘資訊",
				"template": "templates/tp/caseDetail/caseDescriptionOf.html"
			},
			{
				"title": "垂片資訊",
				"template": "templates/tp/caseDetail/ambData.html"
			},
			{
				"title": "補述",
				"template": "templates/tp/caseDetail/caseDescription.html"
			},
			// {
			//   "title": "案件資訊",
			//   "template": "templates/tp/caseDetail/caseData.html"
			// },
			// {
			//   "title": "車輛資訊",
			//   "template": "templates/tp/caseDetail/carData.html"
			// },
			// {
			//   "title": "救護單資訊",
			//   "template": "templates/tp/caseDetail/pcrData.html"
			// },
			{
				"title": "評估項目",
				"template": "templates/tp/caseDetail/assessmentData.html"
			},
			{
				"title": "醫師指導",
				"template": "templates/tp/caseDetail/doctorInstruction.html"
			},
			// {
			//   "title": "救護人員簽名",
			//   "template": "templates/tp/caseDetail/emtData.html"
			// },
			// {
			//   "title": "醫護人員簽名",
			//   "template": "templates/tp/caseDetail/nurseData.html"
			// },
			// {
			//   "title": "協同單位簽名",
			//   "template": "templates/tp/caseDetail/assistantRecords.html"
			// },
			{
				"title": "檢傷圖/燒傷圖",
				"template": "templates/tp/caseDetail/diagramAndBurn.html"
			},
			// {
			//   "title": "檢傷圖",
			//   "template": "templates/tp/caseDetail/diagramData.html"
			// }, {
			//   "title": "燒傷圖",
			//   "template": "templates/tp/caseDetail/burnData.html"
			// },
			{
				"title": "生命徵象",
				"template": "templates/tp/caseDetail/vitalSigns.html"
			},
			{
				"title": "心電圖",
				"template": "templates/tp/caseDetail/ecg.html"
			},
			{
				"title": "平板拍攝",
				"template": "templates/tp/caseDetail/photoOrVideo.html"
			},
			//  {
			//   "title": "事件",
			//   "template": "templates/tp/caseDetail/event.html"
			// }, {
			//   "title": "波形",
			//   "template": "templates/tp/caseDetail/waveForm.html"
			// },
			{
				"title": "歷史影像",
				"template": "templates/tp/caseDetail/historyVideo.html"
			}
		];

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
			false: '是',
			true: '否'
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

		var pcrUuid = $stateParams.uuid;
		var bodyPart;

		var deferred = $q.defer();
		var Promise = deferred.promise;

		var configPromise = getConfig();
		$scope.hasMerCase = false;

		function initData() {
			// return $http.get('/Sexs/')
			// 	.then(function(response) {
			// 		$scope.sexList = response.data;
			// 		console.log("SexList", response.data);
			return $http.get('/Relationships/')
				// })
				.then(function (response) {
					$scope.RelationshipList = _.keyBy(response.data, 'id');
					return $http.get('/PcrCategories/')
				})
				.then(function (response) {
					$scope.PcrCategorieList = _.keyBy(response.data, 'id');
					return $http.get('/DiagramInjuries/')
				})
				.then(function (response) {
					$scope.injuryTypeList = _.keyBy(response.data, 'id');
					return $http.get('/BurnBodyPart/getBurnBodyPart/' + ageType)
					// return $http.get('json/burnBodyPart.json')
				})
				.then(function (response) {
					bodyParts = _.keyBy(response.data, 'name');
					return $http.get('/BurnLevels/')
				})
				.then(function (response) {
					highLightColor = _.keyBy(response.data, 'id');
					return $http.get('/Statuses/')
				})
				.then(function (response) {
					$scope.statusesList = _.keyBy(response.data, 'id');
					return $http.get('/DeathAssessments/')
				})
				.then(function (response) {
					$scope.deathAssessmentList = _.keyBy(response.data, 'id');
					return $http.get('/Awarenesses/')
				})
				.then(function (response) {
					$scope.awarenessList = _.keyBy(response.data, 'id');
					$scope.awarenessListApp = _.keyBy(response.data, 'code');
					return $http.get('/Breaths/')
				})
				.then(function (response) {
					$scope.breathList = _.keyBy(response.data, 'id');
					return $http.get('/Symptoms/')
				})
				.then(function (response) {
					$scope.symptomList = _.keyBy(response.data, 'id');
				})
				.then(function () {
					return $http.get('/CaseRecipient')
						.then(function (response) {
							$scope.caseRecipientList = response.data;
							return $http.get('/DisinfectionLevels')
						})
						.then(function (response) {
							$scope.disinfectionLevels = _.keyBy(response.data, 'id');
							console.log("DisinfectionLevels", response.data)
						})
				});

		}

		function getConfig() {
			return $http.get('/config')
				.then(function (response) {
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
				.then(function (response) {
					console.log('DispatchRecords response', response.data)
					return response
				})
				.catch(function (err) {
					console.log('err =', err)
				})
		}



		function getPcrsData() {
			return configPromise
				.then(function (response) {
					config = response;
					vitalSignVideoServer = response.vitalSignVideoServer;
					doctorServer = response.doctorServer;
					videoPath = response.VideoPath;
					historyVideoPath = response.historyVideoPath;
					imagePath = response.imagePath;
					console.log("videoPath", videoPath)
					console.log("historyVideoPath", historyVideoPath)
					console.log("imagePath", imagePath)
				})
				.then(function (response) {
					return $http.get('/Pcrs/' + pcrUuid)
				})
				.then(function (response) {
					//基本資訊-救護單資訊(Pcrs)
					$scope.PcrData = response.data;
					console.log("age", $scope.PcrData.age)
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
					$scope.PcrData.age = Math.round(($scope.PcrData.age / 12));
					if (!_.isNil($scope.PcrData.DispatchRecord.DispatchCancelReason)) $scope.PcrData.DispatchCancelReason = $scope.PcrData.DispatchRecord.DispatchCancelReason.name;
					//基本資訊-案件資訊(CaseRecords)
					$scope.CaseRecordData = $scope.PcrData.DispatchRecord.CaseRecord;
					//基本資訊-車輛資訊(DispatchRecords-Ambulances-Branches)
					getCaseMainData($scope.CaseRecordData.recordUuid);
					$scope.DispatchRecordData = $scope.PcrData.DispatchRecord;
					$scope.AmbulanceData = $scope.PcrData.DispatchRecord.Ambulance;
					$scope.BrancheData = $scope.PcrData.DispatchRecord.Ambulance.Branch;
					//基本資訊-補述欄
					$scope.CaseDescriptions = _.sortBy($scope.PcrData.CaseDescriptions, ['createdAt'], ['asc']);
					//基本資訊-後送醫院
					$scope.HospitalData = $scope.PcrData.Hospital;
					//評估資訊-檢傷圖(DiagramRecords)
					$scope.DiagramDatas = $scope.PcrData.DiagramRecords;
					//評估資訊-燒傷圖(BurnRecords)
					$scope.BurnDatas = $scope.PcrData.BurnRecords;
					//評估資訊-評估項目(PcrBundles)
					// $scope.PcrBundles = $scope.PcrData.PcrBundles;
					//
					$scope.Properties = $scope.PcrData.Properties;


					$scope.Emts = $scope.PcrData.Emts;
					console.log("$scope.Emts", $scope.Emts)
					//垂片資訊
					var ambs = $scope.PcrData.Ambs;
					$scope.convertAmbs = {};
					angular.forEach(ambs, function (data) {
						var AmbCategory = data.AmbCategory.name;
						if (_.isEmpty($scope.convertAmbs[AmbCategory])) {
							$scope.convertAmbs[AmbCategory] = []
						}
						$scope.convertAmbs[AmbCategory].push(data)
					})
					console.log("convertAmbs", $scope.convertAmbs);
					return $http.get('/PcrBundles?PcrUuid=' + pcrUuid)
				})
				.then(function (response) {
					//取得pcrBundles
					$scope.PcrBundles = response.data;
					if ($scope.PcrBundles.length > 0) {
						$scope.PcrBundle804 = _.find($scope.PcrBundles, { 'PcrCategoryId': 804 });
						$scope.PcrBundle801 = _.find($scope.PcrBundles, { 'PcrCategoryId': 801 });
						$scope.PcrBundle802 = _.find($scope.PcrBundles, { 'PcrCategoryId': 802 });
						$scope.PcrBundle803 = _.find($scope.PcrBundles, { 'PcrCategoryId': 803 });
						var PcrBundle805 = _.find($scope.PcrBundles, { 'PcrCategoryId': 805 });
						var newRecords805 = [];

						if (PcrBundle805) {
							PcrBundle805.PcrRecords.forEach(function (r) {
								_.find(r.PcrQuestion.PcrBlocks, function (o) {
									if (o.displayLabel == "KPI") {
										newRecords805.push(r);
									}
								})
							})
							$scope.PcrBundle805 = PcrBundle805;
							$scope.PcrBundle805.PcrRecords = newRecords805;
						} // if

						$scope.PcrBundlesO = [$scope.PcrBundle801, $scope.PcrBundle802, $scope.PcrBundle803];
					}
				})
				.then(function () {
					return $http.get('/CaseRecords/CaseDescriptionOf/' + $scope.CaseRecordData.recordUuid)
						.then(function (response) {
							$scope.CaseDescriptionOf = response.data;
						})
				})
				.then(function () {
					//取得visualSign
					vitalSignSearchParams = {
						'recordUuid': $scope.PcrData.DispatchRecord.uuid
					}
					$scope.vitalSignParams = vitalSignInit();
				})
				.then(function () {
					//app輸入的vitalSign
					$scope.AppVitalSigns = getAppVitalSigns();
				})
				.then(function () {
					//取得事件
					eventSearchParams = {
						'recordUuid': $scope.PcrData.DispatchRecord.uuid
					}
					$scope.eventParams = eventInit();
				})
				.then(function () {
					//取得歷史影像
					historyVideoSearchParams = {
						'recordUuid': $scope.PcrData.DispatchRecord.uuid
					}
					$scope.historyVideoParams = historyVideoInit();
				})
				.then(function () {
					//取得心電圖
					var query1 = {
						'recordUuid': $scope.PcrData.DispatchRecord.uuid,
						'ImageTypeId': {
							$in: [1]
						},
						'sort': '-generatedAt'
					}
					// var query5 = {
					// 	'recordUuid': pcrUuid,
					// 	'ImageTypeId': {
					// 		$in: [5]
					// 	},
					// 	'sort':'-ImageTypeId,-generatedAt'
					// }
					// return $q.all([
					// 		($http.get(vitalSignVideoServer + '/ImageData', {
					// 		params: query1,
					// 		paramSerializer: '$httpParamSerializerJQLike'
					// 	})),($http.get(vitalSignVideoServer + '/ImageData', {
					// 		params: query5,
					// 		paramSerializer: '$httpParamSerializerJQLike'
					// 	}))
					// ])

					return $http.get(vitalSignVideoServer + '/ImageData', {
						params: query1,
						paramSerializer: '$httpParamSerializerJQLike'
					})
				})
				// .then(function(responseAry) {
				// var response = responseAry[0].data.concat(responseAry[1].data) ;
				.then(function (response) {
					var result = response.data;
					$scope.showECGs = []
					$scope.ecgPath = vitalSignVideoServer + imagePath;
					for (var idx in result) {
						var url = $scope.ecgPath + result[idx].id;
						$scope.showECGs.push({
							url: $sce.trustAsResourceUrl(url),
							ECG: result[idx]
						});
					}
					console.log("showECGs", $scope.showECGs)
					//取得波形
					var query = {
						'recordUuid': $scope.PcrData.DispatchRecord.uuid,
						'ImageTypeId': 2,
						'sort': '-generatedAt'
					}
					return $http.get(vitalSignVideoServer + '/ImageData', {
						params: query,
						paramSerializer: '$httpParamSerializerJQLike'
					})
				})
				.then(function (response) {
					$scope.showWaveForms = _.keyBy(response.data, 'id');
					$scope.waveFormPath = vitalSignVideoServer + imagePath;
					console.log("showWaveForms", $scope.showWaveForms)
					return getVideoList();
				})
				.then(function () {
					return setupDoctorInstrunction($scope.PcrData.uuid);
				})
				.then(function () {
					return getAssistantRecords(pcrUuid);
				})
				.then(function () {
					return setupVoiceData(pcrUuid);
				})
				.then(function () {
					checkMerCase($scope.CaseRecordData.hasMER, $scope.CaseRecordData.recordUuid);
				})
				.then(function () {
					if (AuthService.checkPerm('EPCR_DOCTOR_ORDER')) {
						return setupListRequireDoctorOrder($scope.PcrData.uuid);
					}
				})
				.then(function () {
					$scope.caseDataEdit.CaseRecipientId = $scope.DispatchRecordData.CaseRecord.CaseRecipientId;
				})
				.then(function () {
					$scope.vitalSignVideoOptions = {
						PcrUuid: $scope.PcrData.uuid,
						imageTypeIds: '5,6,7,8',
						videoTypeIds: '4,5,6,7'
					}
				})
				.catch(function (err) {
					console.log('getPcrsData err =', err)
				})
		}



		//========即時影像
		function getVideoList() {
			return dataDispatchRecord()
				.then(function (response) {
					if (!_.isEmpty(response.data)) {
						// $scope.videoPath = response.data;
						$scope.videoPath = videoPath + response.data.uuid;
					}
				})
		}
		//========即時影像




		var getCaseMainData = function (caseNo) {
			return $http.get('/CaseRecords/getCaseMain/' + caseNo)
				.then(function (response) {
					$scope.caseMainData = response.data;
					console.log('caseMainData', $scope.caseMainData)
				})
		}

		//填寫檢傷資料
		//caseType=內科外科的id

		function calculatePercentage(records) {
			var percentage = { "1": 0, "2": 0, "3": 0 }

			angular.forEach(records, function (record) {
				// console.log("percentage",percentage, record.BurnLevelId, bodyParts[record.BurnBodyPart.name].percent);
				if (record.BurnLevelId != "0") {
					// percentage[record.BurnLevelId] += bodyParts[key].percent;
					percentage[record.BurnLevelId] += record.percent;
				}
			});
			return percentage;
		}

		function addMark(id, X, Y, injuryType, caseType, bodyPart, areaW, areaH, svgId) {
			var sizeW = MIN_AREA + parseInt(areaW);
			var sizeH = MIN_AREA + parseInt(areaH);
			var color = $scope.injuryTypeList[injuryType].color;
			var injuryText = $scope.injuryTypeList[injuryType].name;
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
					.style("fill", "#FFFF00")
					.attr("x", X - sizeW / 2)
					.attr("y", Y + sizeH / 2)
					.attr("class", "injury-text")
					.text(areaW + 'x' + areaH + ' ' + injuryText);
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
					.style("fill", "#FFFF00")
					.attr("x", X - sizeW / 2)
					.attr("y", Y + sizeH / 2)
					.attr("class", "injury-text")
					.text(areaW + 'x' + areaH + ' ' + injuryText);
			}
		};
		//填寫檢傷資料

		//填寫燒傷圖資料
		function highlightPart(bodyPart, level, svgId) {
			var graphs;
			if (bodyParts[bodyPart]["BurnSubBodyParts"].length > 0) {
				graphs = bodyParts[bodyPart]["BurnSubBodyParts"];
			} else {
				graphs = [{
					name: bodyPart
				}];
			}
			angular.forEach(graphs, function (part) {
				// console.log('high light', part.name);
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
		$scope.svgDiagramLoaded = function () {
			Promise.then(function () {
				var origW = d3.select("#svgDiagram").attr("width");
				var origH = d3.select("#svgDiagram").attr("height");
				var W = origW;
				var H = origH;
				//暫時先不管圖片的Ｗ跟Ｈ
				// var W = document.getElementById("diagarmSvg").clientWidth;
				// var H = document.getElementById("diagarmSvg").clientHeight
				console.log('W', W, 'H', H);
				d3.select("#svgDiagram")
					.attr("width", W)
					.attr("height", H)
					.attr("viewBox", "0,0," + origW + "," + origH);

				$scope.$watch('PcrData.DiagramRecords', function (newValue, oldValue) {
					console.log("PcrData.DiagramRecords $watch");
					angular.forEach(newValue, function (record) {
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
		$scope.svgBurnLoaded = function () {
			Promise.then(function () {
				var origW = d3.select("#svgBurn").attr("width");
				var origH = d3.select("#svgBurn").attr("height");

				var H = d3.select("#svgDiagram").attr("height");
				var W = (origW / origH) * H;
				//暫時先不管圖片的Ｗ跟Ｈ
				// var W = document.getElementById("burnSvg").clientWidth;
				// var H = document.getElementById("burnSvg").clientHeight;
				console.log('W', W, 'H', H);

				d3.select("#svgBurn")
					.attr("width", W)
					.attr("height", H)
					.attr("viewBox", "0,0," + origW + "," + origH);

				// var records = $scope.BurnDatas;
				$scope.$watch('BurnDatas', function (newValue, oldValue) {
					if (newValue) {
						console.log("BurnDatas $watch");
						angular.forEach(newValue, function (record) {
							highlightPart(record.BurnBodyPart.name, record.BurnLevelId, "#svgBurn");
						});
						$scope.burnPercentage = calculatePercentage(newValue);
					}
				});
			})
		};
		//呈現燒燙傷資訊

		//播放歷史影像
		$scope.showVideo = function (index) {
			$scope.historyPath = vitalSignVideoServer + historyVideoPath;
			$scope.historyVideo = historyVideoList[index];
			console.log("$scope.historyVideo", $scope.historyVideo)
			videoModal.$promise.then(videoModal.show);
		};
		//播放歷史影像

		//歷史影像下載
		$scope.downloadVideo = function (index) {
			var videoData = historyVideoList[index];
			var downloadPath = vitalSignVideoServer + historyVideoPath + videoData.id + '?download=true'
			$window.open(downloadPath, '_blank');
		};
		//AP輸入之VitalSgins
		function getAppVitalSigns() {
			return new NgTableParams({
				sorting: { datetime: 'desc' }
			}, {
				filterDelay: 300,
				pages: [],
				counts: [],
				getData: function (params) {
					var deferred = $q.defer();
					$scope.anyPageBusy = deferred.promise;
					// console.log(params.sorting())
					var url = params.url();
					var limit = url.count,
						skip = url.count * (url.page - 1);
					var sortString;
					var measureStatuses;
					// 如果使用 epilogue 免費 api sort需要做調整
					// 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
					// sortString = params.sorting();

					return $http.get('/MeasureStatuses', {})
						.then(function (response) {
							measureStatuses = _.keyBy(response.data, 'id');
							return $http.get('/VitalSignSets', {
								params: {
									PcrUuid: pcrUuid
								},
								paramSerializer: '$httpParamSerializerJQLike'
							})
						})
						.then(function (response) {
							var appVitalSignsRaw = response.data;
							var vitalTemplate = {
								uuid: null,
								Awareness: null,
								RespiratoryRate: null,
								Pulse: null,
								SystolicBP: null,
								DiastolicBP: null,
								temp: null,
								SpO2: null,
								GCS_E: null,
								GCS_V: null,
								GCS_M: null,
								'替代測量': null
							}
							var appVitalSigns = [];
							angular.forEach(appVitalSignsRaw, function (appVitalSign) {
								var vitalItem = angular.copy(vitalTemplate);
								angular.forEach(appVitalSign.VitalSigns, function (item) {

									if (vitalTemplate.hasOwnProperty(item.VitalSignType.name)) {
										if (item.MeasureStatusId > 1) {
											vitalItem[item.VitalSignType.name] = measureStatuses[item.MeasureStatusId].name;
										} else {
											vitalItem[item.VitalSignType.name] = item.value;
										}

										// vitalSignInfo
										if (!_.isNil(item.VitalSignInfos) && !_.isEmpty(item.VitalSignInfos)) {
											for (var idx in item.VitalSignInfos) {
												if (vitalItem[item.VitalSignType.name] == '') {
													vitalItem[item.VitalSignType.name] = item.VitalSignInfos[idx].name;
												} else {
													vitalItem[item.VitalSignType.name] = vitalItem[item.VitalSignType.name] + ' ' + item.VitalSignInfos[idx].name;
												}
											}
										}

										// console.log(vitalItem);
									}
								})
								vitalItem["uuid"] = appVitalSign.uuid;
								vitalItem["datetime"] = appVitalSign.datetime;
								appVitalSigns.push(vitalItem);
							})


							deferred.resolve()
							return appVitalSigns;
						})
						.catch(function (err) {
							deferred.resolve();
							console.log('vitalSignInit err =', err)
						})
				}
			})
		}
		//生命徵象
		var vitalSignSearchParams = {};
		var vitalSignList = [];

		function vitalSignInit() {
			return new NgTableParams({
				sorting: {
					EndTime: 'desc'
				}
			}, {
				filterDelay: 300,
				pages: [],
				counts: [],
				getData: function (params) {
					var deferred = $q.defer();
					$scope.anyPageBusy = deferred.promise;
					// console.log(params.sorting())
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

					var query = {
						sort: sortString,
						time: new Date().getTime()
					}

					if (!_.isEmpty(vitalSignSearchParams)) {
						for (var key in vitalSignSearchParams) {
							query[key] = vitalSignSearchParams[key];
						}
					}
					console.log("query", query)

					return $http.get(vitalSignVideoServer + '/trendings', {
						params: query,
						paramSerializer: '$httpParamSerializerJQLike'
					})
						.then(function (response) {
							vitalSignList = response.data;
							deferred.resolve()
							return vitalSignList
						})
						.catch(function (err) {
							deferred.resolve();
							console.log('vitalSignInit err =', err)
						})
				}
			})
		};
		//生命徵象

		//事件
		var eventSearchParams = {};
		var eventList = [];

		function eventInit() {
			return new NgTableParams({
				sorting: {
					Timestamp: 'desc'
				}
			}, {
				filterDelay: 300,
				pages: [],
				counts: [],
				getData: function (params) {
					var deferred = $q.defer();
					$scope.anyPageBusy = deferred.promise;
					console.log(params.sorting())
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

					var query = {
						sort: sortString,
						time: new Date().getTime()
					}

					if (!_.isEmpty(eventSearchParams)) {
						for (var key in eventSearchParams) {
							query[key] = eventSearchParams[key];
						}
					}
					console.log("query", query)

					return $http.get(vitalSignVideoServer + '/events', {
						params: query,
						paramSerializer: '$httpParamSerializerJQLike'
					})
						.then(function (response) {
							eventList = response.data;
							deferred.resolve()
							return eventList
						})
						.catch(function (err) {
							deferred.resolve();
							console.log('eventInit err =', err)
						})
				}
			})
		};
		//事件

		//歷史影像
		var historyVideoSearchParams = {};
		var historyVideoList = [];

		function historyVideoInit() {
			return new NgTableParams({
				sorting: {
					generatedAt: 'desc'
				}
			}, {
				filterDelay: 300,
				pages: [],
				counts: [],
				getData: function (params) {
					var deferred = $q.defer();
					$scope.anyPageBusy = deferred.promise;
					console.log(params.sorting())
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

					var query = {
						sort: sortString,
						time: new Date().getTime()
					}

					if (!_.isEmpty(historyVideoSearchParams)) {
						for (var key in historyVideoSearchParams) {
							query[key] = historyVideoSearchParams[key];
						}
					}
					console.log("query", query)

					return $http.get(vitalSignVideoServer + '/VideoData', {
						params: query,
						paramSerializer: '$httpParamSerializerJQLike'
					})
						.then(function (response) {
							console.log("historyVideoList", response.data)
							historyVideoList = response.data;
							deferred.resolve()
							return historyVideoList
						})
						.catch(function (err) {
							deferred.resolve();
							console.log('historyVideoInit err =', err)
						})
				}
			})
		};
		//歷史影像



		// =============================================================================================
		var PcrCategoryId = 25;

		function backtrackingInit() {
			$scope.vm = {};
			$scope.vm.model = {};
			$scope.vm.fields = [];

			$http.get('/pcrbundles', {
				params: {
					PcrUuid: pcrUuid,
					PcrCategoryId: PcrCategoryId
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
				.then(function (pcrbundles) {
					if (pcrbundles && !_.isEmpty(pcrbundles.data)) {
						console.log('have bundle', pcrbundles.data[0]);
						$scope.versionId = pcrbundles.data[0].PcrVersionId;
						$scope.vm.model = formatFormlyModel(pcrbundles.data[0].PcrRecords);
						return PcrQuestionService.getJson(PcrCategoryId, $scope.versionId);
					} // if
					else {
						console.log('no bundle', pcrbundles.data);
						return PcrQuestionService.getVersion()
							.then(function (versionId) {
								$scope.versionId = versionId;
								return PcrQuestionService.getJson(PcrCategoryId, versionId);
							});
					} // else
				})
				.then(function (questions) {
					$scope.vm.fields = questions;
					// console.log('fields', $scope.vm.fields);
					// console.log('model', $scope.vm.model);
				})
				.catch(function (err) {
					console.log('backtrackingInit err ', err);
				});
		} // backtrackingInit()


		// ---------------------------------------------------------------------------------------------
		$scope.backtrackingSave = function (input) {
			// console.log('model', input.model);
			// console.log('fields', input.fields);
			var pcrBundles = {
				PcrUuid: pcrUuid,
				PcrVersionId: $scope.versionId,
				PcrCategoryId: PcrCategoryId,
				PcrRecords: []
			};

			angular.forEach(input.model, function (item, key) {
				var pcrRecord = {};
				var fields = _.find(input.fields, function (o) {
					return o.key == key;
				});
				pcrRecord['PcrQuestionId'] = fields.data.QuestionSN;
				pcrRecord['PcrAnswerRecords'] = [];

				console.log('fields', fields);
				switch (fields.type) {
					case 'String':
						var pcrAnswer = {
							freeTypingValue: item,
							PcrAnswerId: fields.data.answerSN
						};
						console.log('pcrAnswer', pcrAnswer);
						pcrRecord.PcrAnswerRecords.push(pcrAnswer);
						break;
					case 'Select':
						var pcrAnswer = {
							PcrAnswerId: _.find(fields.templateOptions.options, function (o) {
								return o.value == item;
							}).answerID
						};
						console.log('pcrAnswer', pcrAnswer);
						pcrRecord.PcrAnswerRecords.push(pcrAnswer);
						break;
				} // switch
				pcrBundles.PcrRecords.push(pcrRecord);
				// console.log('PcrAnswerRecords', pcrBundles.PcrRecords);
			});

			// console.log(input);
			$http.get('/pcrbundles', {
				params: {
					PcrUuid: pcrUuid,
					PcrCategoryId: PcrCategoryId,
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
				.then(function (pcrbundles) {
					if (_.isEmpty(pcrbundles.data)) {
						console.log('Fin pcrBundles', pcrBundles);
						return $http.post('/pcrbundles', pcrBundles);
					} // if
					else {
						pcrBundles['uuid'] = pcrbundles.data[0].uuid;
						console.log('Fin pcrBundles', pcrBundles);
						return $http.post('/pcrbundles/updateTo', pcrBundles);
					} // else
				})
				.then(function (response) {
					console.log('response', response);
					backtrackingInit();
				})
				.catch(function (err) {
					console.log('backtrackingSave err ', err);
				});
		};
		// ---------------------------------------------------------------------------------------------
		function formatFormlyModel(pcrRecords) {
			var model = {};
			angular.forEach(pcrRecords, function (pcrRecord) {
				switch (pcrRecord.PcrQuestion.PcrQuestionType.questionType) {
					case 'Text':
						model[pcrRecord.PcrQuestion.code] = pcrRecord.PcrAnswerRecords[0].freeTypingValue;
						break;
					case 'Select':
						model[pcrRecord.PcrQuestion.code] = pcrRecord.PcrAnswerRecords[0].PcrAnswer.code;
						break;
					// case 'Int':
					// 	model[pcrRecord.PcrQuestion.code] = _.toNumber(pcrRecord.PcrAnswerRecords[0].freeTypingValue);
					// 	break;
				} // switch
			});

			console.log('model', model);
			return model;
		} // formatFormlyModel()

		function getDoctorInstruction(recordUuid) {
			return $http.get(doctorServer + '/Instructions', {
				params: {
					recordUuid: recordUuid
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
				.then(function (response) {
					return response.data;
				});
		}

		function getVoiceData(recordUuid) {
			return $http.get(doctorServer + '/VoiceData', {
				params: {
					recordUuid: recordUuid
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
				.then(function (response) {
					return response.data;
				})
		}

		function setupDoctorInstrunction(recordUuid) {
			return getDoctorInstruction(recordUuid)
				.then(function (instructions) {
					$scope.DoctorInstructionList = instructions;
				});
		}

		function setupVoiceData(recordUuid) {
			return getVoiceData(recordUuid)
				.then(function (results) {
					$scope.VoiceDataList = results;
					$scope.VoiceDataUrl = doctorServer + '/VoiceData/getFile'
				});
		}


		function getAssistantRecords(pcrUuid) {
			return $http.get('/AssistantRecords', {
				params: {
					PcrUuid: pcrUuid
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
				.then(function (response) {
					$scope.assistantRecords = response.data;
				})
		}

		function checkMerCase(hasMER, recordUuid) {
			$scope.hasMerCase = hasMER;
			if ($scope.hasMerCase) {
				$scope.merCaseUrl = config.merServer + '/Views/CaseDetailView.aspx?ID=' + recordUuid;
				$scope.merServer = config.merServer;
			}
		}
		/* 新增補述欄功能 */
		$scope.editCaseDescription = {}
		function addCaseDescription(PcrUuid, description) {
			var caseDescription = {
				description: description,
				PcrUuid: PcrUuid
			}
			return $http.post('/caseDescriptions', caseDescription)
		}

		$scope.addCaseDescription = function (description) {
			$scope.anyPageBusy = addCaseDescription(pcrUuid, description)
				.then(function (result) {
					$scope.editCaseDescription.description = null;
					return getPcrsData()
				})
				.catch(function (error) {
					console.log(error);
					alert('無法新增補述欄');
				})
			return $scope.anyPageBusy;
		}

		/* 修改受案單位 */
		function saveCaseRecipient(CaseRecordId, CaseRecipientId) {
			return $http.put('/CaseRecords/' + CaseRecordId, {
				CaseRecipientId: CaseRecipientId
			})
		}

		$scope.caseDataEdit = {
			editMode: false,
			edit: function () {
				$scope.caseDataEdit.editMode = true;
				$scope.caseDataEdit.CaseRecipientId = $scope.CaseRecordData.CaseRecipientId;
			},
			cancel: function () {
				$scope.caseDataEdit.editMode = false;
			},
			save: function (CaseRecordId, CaseRecipientId) {
				return saveCaseRecipient(CaseRecordId, CaseRecipientId)
					.then(function () {
						$scope.CaseRecordData.CaseRecipientId = CaseRecipientId;
						var idx = _.findIndex($scope.caseRecipientList, {
							id: CaseRecipientId
						});
						if (idx != -1) {
							$scope.CaseRecordData.CaseRecipient = $scope.caseRecipientList[idx];
						}
						$scope.caseDataEdit.editMode = false;
					})
					.catch(function (error) {
						console.log(error);
						alert("無法儲存受案單位");
					});
			},
			CaseRecipientId: null
		}


		getPcrsData();

		initData()
			.then(function () {
				deferred.resolve();
			})
			.then(function () {
				// After DOM render complete, $timeout will invoke.
				// callPhantom means it is now ok to take screen shot.
				$timeout(function () {
					if (typeof window.callPhantom === 'function') {
						console.log('callPhantom takeShot');
						window.callPhantom('takeShot');
					}
				});
			})
			.catch(function (err) {
				console.log(err)
			})

		if (!$scope.isHospital) backtrackingInit();

	});
