CONTROLLERS.controller('EmtCtrl',
	function($q, $modal, $scope, $state, $alert, $http, $element,
		NgTableParams, EPCRServices, upload, AuthService) {

		var emtId;
		var currentUser = AuthService.getCurrentUser();
		console.log('CURRENT USER', currentUser);
    if (currentUser.role != 'EMT') {
      $scope.isEmt = false;
      emtId = null;
    } // if
    else {
      $scope.isEmt = true;
      emtId = currentUser.customData;
    } // else

		$scope.tabs = [{
				title: '個人資料',
				tp: 'templates/tp/emtInformation.html'
			},
			{
				title: '教學歷程',
				tp: 'templates/tp/emtTraining.html'
			},
			{
				title: '救護數據',
				tp: 'templates/tp/emtCaseRecordStatistics.html'
			}
		]

		var emtAddModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/emtAdd.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			onHide: refreshList
		})
		var emtDeleteModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/emtDelete.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			onHide: refreshList
		})
		var emtDetailModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/emtDetail.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			onHide: refreshList
		});
		var emtAddLevelModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/emtAddLevel.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			onHide: EmtDetailRefreshList
		});
		var emtLevelDetailModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/emtLevelDetailModal.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			onHide: EmtDetailRefreshList
		});
		var emtDeleteLevelModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/emtDeleteLevel.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			onHide: EmtDetailRefreshList
		});
		var emtAddTrainingModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/emtAddTraining.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			onHide: EmtTrainingRefreshList
		});
		var emtEditTrainingModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/emtEditTraining.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			onHide: EmtTrainingRefreshList
		});
		var emtDeleteTrainingModal = $modal({
			scope: $scope,
			templateUrl: 'templates/modal/emtDeleteTraining.html',
			animation: 'no-animation',
			placement: 'center',
			backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
			show: false,
			onHide: EmtTrainingRefreshList
		});

		function failAlertToModal2(title, content, time) {
			var alert = $alert({
				title: title,
				content: content,
				container: '#alerts-tag-2',
				placement: 'alert-floater-modal alert-center-top font-size-18',
				duration: !_.isNil(time) ? time : 3,
				type: 'danger',
				show: true
			})
			return alert.$promise;
		}

		var getEMTData = function(id) {
			return $http.get('/emts/' + id)
				.then(function(response) {
					return response.data;
				})
		}
		var getImageData = function(EmtId) {
			return $http.get('/ImageDatas', {
					params: {
						EmtId: EmtId,
						ImageTypeId: 5
					},
					paramSerializer: '$httpParamSerializerJQLike'
				})
				.then(function(response) {
					return response.data
				})
		}
		var getTrainingData = function() {
			return $http.get('/Trainings')
				.then(function(response) {
					return response.data
				})
		}
		var getStatisticsPcrType = function(id) {
			return $http.get('/emts/statisticsPcrType/' + id)
				.then(function(response) {
					return response.data;
				})
		}
		var getStatisticsPcrAnswer = function(id) {
			return $http.get('/emts/statisticsPcrAnswer/' + id)
				.then(function(response) {
					return response.data;
				})
		}
		var getStatisticsPcrTypeForMCI = function(id) {
			return $http.get('/emts/statisticsPcrTypeForMCI/' + id)
				.then(function(response) {
					return response.data;
				})
		}

		var statSkillByAssess = function(id) {
			// I-GEL/氣管內管插管成功件數 OHCA22_2 OHCA22_3
			return $http.get('/emts/statSkillByAssess/' + id)
				.then(function(response) {
					return response.data;
				})
		}
		var statSkillByAnswer = function(id) {
			// AED電擊 CRT10(AED電擊次數) >0
			return $http.get('/emts/statSkillByAnswer/' + id)
				.then(function(response) {
					return response.data;
				})
		}
		var statSkillByQuestion = function(id) {
			// 處置題目
			return $http.get('/emts/statSkillByQuestion/' + id)
				.then(function(response) {
					return response.data;
				})
		}
		var statSkillByCPSS = function(id) {
			// 辛辛那提測試
			return $http.get('/emts/statSkillByCPSS/' + id)
				.then(function(response) {
					return response.data;
				})
		}
		var statSkillByIV = function(id) {
			// 靜脈建立成功件數
			return $http.get('/emts/statSkillByIV/' + id)
				.then(function(response) {
					return response.data;
				})
		}


		function sumPcrType(types) {
			var timeSum = 0;
			var typeSum = 0;

			angular.forEach(types, function(value) {
				typeSum += value.PcrTypeSum;
				timeSum += value.duration ? value.duration:0;
			})

			$scope.caseRecordSum = {
				count: typeSum,
				duration: timeSum
			}
		}

		function getSelectedEmtInfo(EmtId) {
			return getImageData(EmtId)
				.then(function(theImageData) {
					if (theImageData.length > 0) {
						$scope.isUpdate = true;
						$scope.editData.ImageData = theImageData;
					} else {
						$scope.isUpdate = false
					}

					return getStatisticsPcrType(EmtId)
				})
				.then(function(thePcrType) {
					$scope.statisticsPcrType = thePcrType;

					sumPcrType(thePcrType);

					var idx = _.findIndex($scope.statisticsPcrType, {
						name: 'OHCA'
					})
					$scope.OHCASum = idx != -1 ? $scope.statisticsPcrType[idx] : 0;
// 有關EMT個人救護歷程的統計，隨著案件量的增加需要很長的時間執行
// 同時統計所用的Question code也只存在於105年版的題目，故先跳過不執行相關的統計
/*
					return getStatisticsPcrAnswer(EmtId)
				})
				.then(function(thePcrAnswer) {
					$scope.statisticsPcrAnswer = thePcrAnswer;
					return statSkillByAssess(EmtId)
				})
				.then(function(theSkill) {
					$scope.statSkillByAssess = theSkill;
					return statSkillByQuestion(EmtId)
				})
				.then(function(theSkill) {
					$scope.statSkillByQuestion = theSkill;
					return statSkillByCPSS(EmtId)
				})
				.then(function(theSkill) {
					$scope.statSkillByCPSS = theSkill;
					return statSkillByAnswer(EmtId)
				})
				.then(function(theSkill) {
					$scope.statSkillByAnswer = theSkill;
					return statSkillByIV(EmtId)
				})
				.then(function(theSkill) {
					$scope.statSkillByIV = theSkill;
				})
				.then(function() {
*/
					return getTrainingData()
				})
				.then(function(theTraining) {
					$scope.trainingList = _.keyBy(theTraining, 'id');
					emtDetailModal.$promise.then(emtDetailModal.show)
				})
		}
		$scope.showEditModal = function(idx) {
			var EmtId = responseList[idx].id;
			$scope.authToken = AuthService.getToken();

			getEMTData(EmtId)
				.then(function(theEmt) {
					if (theEmt) {
						$scope.editData = theEmt;
						$scope.postImageParams = {
							EmtId: EmtId,
							ImageTypeId: 5 //emt大頭照
						}

						$scope.tableEMTDetail = tableEMTDetail(EmtId)
						$scope.tableTrainingParams = tableTrainingParams(EmtId)

						return getSelectedEmtInfo(EmtId)
					}
				})
				.catch(function(err) {
					console.log('EMT showEditModal fails=', err)
					EPCRServices.failAlert('錯誤！', '取得EMT資訊失敗！', null)
					refreshList()
				})
		}
		$scope.updateEmt = function(EmtId, updateData) {
			delete updateData['Branch'];
			$http.put('/emts/' + EmtId, updateData)
				.then(function(response) {
					console.log('updateEmt success!', response.data)
					EPCRServices.successAlertToModal('通知！', '存檔成功！', null)
				})
				.catch(function(err) {
					console.log('updateEmt fails err=', err)
					EPCRServices.failAlertToModal('錯誤！', '無法存檔！', null)
				})
		}

		$scope.showAddModal = function() {
			$scope.add = {
				isLocal: true
			};
			emtAddModal.$promise.then(emtAddModal.show)
		}
		$scope.onShowImage = function() {
			var EmtImage = angular.element(document.getElementById("EmtImage"));
			var fileReader = new FileReader();

			fileReader.onload = function() {
				var imageUrl = fileReader.result
				var output = angular.element(document.getElementById("localImageData"));
				output[0].src = imageUrl;
			}
			fileReader.readAsDataURL(EmtImage[0].files[0]);
		}

		$scope.toAdd = function(addData) {
			var deferred = $q.defer();
			$scope.myPromise = deferred.promise;

			//  $http.post('/emts', addData)
			// 檢查此帳號是否已使用
			$http.get('/emts/find/' + addData.account)
				.then(function(result) {
					console.log('emt', result.data);
					if (!_.isEmpty(result.data)) {
						EPCRServices.failAlert('錯誤！', '帳號重複！', null);
						throw '帳號重複！';
					} // if
					else {
						return $http.post('/emts/add', addData);
					} // else
				})
				.then(function(response) {
					console.log(response);
					var EmtId = response.data.id;
					var EmtImage = angular.element(document.getElementById("EmtImage"));
					var filesLength = EmtImage[0].files.length

					if (filesLength > 0) {
						return upload({
								url: '/ImageDatas/upload',
								method: 'POST',
								data: {
									EmtId: EmtId,
									imageFile: EmtImage,
									ImageTypeId: 5
								}
							})
							.then(function(response) {
								console.log('ImageData upload success!')
							})
					} else {
						return $q.when();
					}
				})
				.then(function() {
					deferred.resolve();
					emtAddModal.$promise.then(emtAddModal.hide)
				})
				.catch(function(err) {
					console.log('Emt toAdd fails=', err)
					deferred.resolve()
					EPCRServices.failAlertToModal('錯誤！', '新增失敗！', null);
				});
		};

		$scope.showDeleteModal = function(idx) {
			$scope.deleteInfo = {
				EmtId: responseList[idx].id
			}
			emtDeleteModal.$promise.then(emtDeleteModal.show)
		}
		$scope.toDeleteEmt = function(EmtId) {
			$http.delete('/emts/' + EmtId)
				.then(function(response) {
					console.log('toDeleteEmt success!')
					emtDeleteModal.$promise.then(emtDeleteModal.hide)
				})
				.catch(function(err) {
					console.log('toDeleteEmt fails=', err)
					EPCRServices.failAlertToModal('錯誤！', '無法刪除！', null)
				})
		}



		$scope.showAddEmtLevelModal = function(EmtId) {
			$scope.add = {
				EmtId: EmtId
			}
			emtAddLevelModal.$promise.then(emtAddLevelModal.show)
		}
		$scope.toAddEmtLevel = function(isOk, addData) {
			if (isOk) {
				if (addData.beginDate > addData.endDate) {
					return failAlertToModal2('錯誤！', '起迄時間錯誤！', null)
				}
				var deferred = $q.defer()
				$scope.myPromise2 = deferred.promise;

				$http.post('/emts/addToLevel', addData)
					.then(function(response) {
						console.log('toAddEmtLevel success!')
						$scope.editData = response.data;
						deferred.resolve()
						emtAddLevelModal.$promise.then(emtAddLevelModal.hide)
					})
					.catch(function(err) {
						console.log('toAddEmtLevel fails=', err)
						deferred.resolve()
						failAlertToModal2('錯誤！', '新增失敗！', null)
					})
			} else {
				failAlertToModal2('警告！', '有欄位未填寫！', null)
			}
		}

		$scope.showDeleteEmtLevelModal = function(idx) {
			var EmtLevel = $scope.tableEMTDetail.data[idx]
			$scope.deleteInfo = {
				emtId: EmtLevel.EmtLevelMap.EmtId,
				emtLevelMapId: EmtLevel.EmtLevelMap.id,
			}
			emtDeleteLevelModal.$promise.then(emtDeleteLevelModal.show)
		}
		$scope.toDeleteEmtLevel = function(data) {
			var deferred = $q.defer()
			$scope.myPromise2 = deferred.promise;

			$http.post('/emts/deleteLevel', {
					EmtId: data.emtId,
					EmtLevelMapId: data.emtLevelMapId
				})
				.then(function(response) {
					console.log('toDeleteEmtLevel success!')
					$scope.editData = response.data;
					deferred.resolve()
					emtDeleteLevelModal.$promise.then(emtDeleteLevelModal.hide)
				})
				.catch(function(err) {
					console.log('toDeleteEmtLevel fails=', err)
					deferred.resolve()
					failAlertToModal2('錯誤！', '刪除失敗！', null)
				})
		}

		$scope.showEditEmtLevelDetailModal = function(index) {
			var data = $scope.tableEMTDetail.data[index];
			$scope.editEmtLevel = {
				EmtId: data.EmtLevelMap.EmtId,
				endDate: data.EmtLevelMap.endDate,
				beginDate: data.EmtLevelMap.beginDate,
				EmtLevelId: data.EmtLevelMap.EmtLevelId,
				EmtLevelMapId: data.EmtLevelMap.id
			}
			emtLevelDetailModal.$promise.then(emtLevelDetailModal.show);
		};
		$scope.toEditEmtLevelDetail = function(valid, editEmtLevel) {
			if (!valid) {
				return EPCRServices.failAlertToModal('錯誤!', '請輸入EMT證照時間', null)
			} // if

			var deferred = $q.defer()
			$scope.myPromise2 = deferred.promise;

			$http.put('/emts/updateLevel/' + editEmtLevel.EmtId, editEmtLevel)
				.then(function(response) {
					console.log('toEditEmtLevelDetail success!')
					$scope.editData = response.data;
					deferred.resolve()
					emtLevelDetailModal.$promise.then(emtLevelDetailModal.hide);
				})
				.catch(function(err) {
					console.log('toEdit err =', err)
					deferred.resolve()
					EPCRServices.failAlertToModal('錯誤!', "修改EMT證照時間失敗", null);
				});
		};



		$scope.showAddEmtTrainingModal = function(EmtId) {
			$scope.add = {
				EmtId: EmtId
			}
			emtAddTrainingModal.$promise.then(emtAddTrainingModal.show)
		}
		$scope.toAddEmtTraining = function(isOk, addData) {
			if (isOk) {
				var deferred = $q.defer()
				$scope.myPromise2 = deferred.promise;

				$http.post('/emts/addToTraining', addData)
					.then(function(response) {
						deferred.resolve()
						emtAddTrainingModal.$promise.then(emtAddTrainingModal.hide)
					})
					.catch(function(err) {
						console.log('toAddEmtTraining fails=', err)
						deferred.resolve()
						failAlertToModal2('錯誤！', '新增失敗！', null)
					})

			} else {
				failAlertToModal2('警告！', '有欄位未填寫！', null)
			}
		}

		$scope.showEditEmtTrainingModal = function(idx) {
			$scope.editTraining = {
				emtTrainingMapId: $scope.tableTrainingParams.data[idx].EmtTrainingMap.id,
				hours: $scope.tableTrainingParams.data[idx].EmtTrainingMap.hours
			}
			$scope.showTraining = $scope.tableTrainingParams.data[idx];
			emtEditTrainingModal.$promise.then(emtEditTrainingModal.show)
		}
		$scope.toEditEmtTraining = function(isOk, editData) {
			if (isOk) {
				var deferred = $q.defer()
				$scope.myPromise2 = deferred.promise;
				var id = editData.emtTrainingMapId
				$http.put('/emtTrainingMaps/' + id, editData)
					.then(function(response) {
						deferred.resolve()
						emtEditTrainingModal.$promise.then(emtEditTrainingModal.hide)
					})
					.catch(function(err) {
						console.log('toEditEmtTraining fails=', err)
						deferred.resolve()
						failAlertToModal2('錯誤！', '修改失敗！', null)
					})

			} else {
				failAlertToModal2('警告！', '有欄位未填寫！', null)
			}
		}

		$scope.showDeleteEmtTrainingModal = function(idx) {
			$scope.deleteInfo = {
				emtTrainingMapId: $scope.tableTrainingParams.data[idx].EmtTrainingMap.id
			}
			emtDeleteTrainingModal.$promise.then(emtDeleteTrainingModal.show)
		}
		$scope.toDeleteEmtTraining = function(data) {
			$http.delete('/emtTrainingMaps/' + data.emtTrainingMapId)
				.then(function(response) {
					emtDeleteTrainingModal.$promise.then(emtDeleteTrainingModal.hide)
				})
				.catch(function(err) {
					console.log('toDeleteEmtTraining fails=', err)
					failAlertToModal2('錯誤！', '刪除失敗！', null)
				})
		}

		// upload image & upadet image
		$scope.urlDatetime = new Date().getTime()
		$scope.uploadSuccess = function(response, EmtId) {
			console.log(response.data)
			console.log('Upload ImageData EmtId Success!!')
			EPCRServices.successAlertToModal('通知！', '照片新增成功！', null)

			getImageData(EmtId)
				.then(function(response) {
					$scope.editData.ImageData = response;
					$scope.isUpdate = true;
					$scope.urlDatetime = new Date().getTime()
				})
		}
		$scope.updateSuccess = function(response, EmtId) {
			console.log(response.data)
			console.log('Update ImageData EmtId Success!!')
			EPCRServices.successAlertToModal('通知！', '照片已更新成功！', null)

			getImageData(EmtId)
				.then(function(response) {
					$scope.editData.ImageData = response;
					$scope.urlDatetime = new Date().getTime()
				})
		}
		// upload image & upadet image


		$scope.customSearch = function(search) {
			searchParams = {}
			for (var key in search) {
				if (search[key] && search[key] != '') {
					searchParams[key] = search[key]
				}
			}
			$scope.tableParams = tableInit();
		}
		$scope.clearCondition = function() {
			clearAndTableInit()
		}
		$scope.refreshList = function() {
			clearAndTableInit()
		}

		function clearAndTableInit() {
			$scope.search = {}
			searchParams = {}
			$scope.tableParams = tableInit();
		}

		var searchParams = {}
		var responseList = []

		function tableInit() {
			return new NgTableParams({
				page: 1, // show first page
				count: 10, // count per page,
				sorting: {
					BranchId: 'asc'
				}
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
						sort: sortString,
						offset: skip,
						count: limit,
						time: new Date().getTime()
					}

					if (!_.isEmpty(searchParams)) {
						for (var key in searchParams) {
							conditions[key] = searchParams[key];
						}
					}

          if (emtId) {
            conditions['id'] = emtId;
          } // if

					return $http.get('/emts', {
							params: conditions,
							paramSerializer: '$httpParamSerializerJQLike'
						})
						.then(function(response) {
							var range = contentRange.parse(response.headers('Content-Range'));
							var count = range.length;
							params.total(count);

							angular.forEach(response.data, function(data) {
								data.EmtLevels = _.keyBy(data.EmtLevels, 'id')
							})

							responseList = response.data;
							console.log('@@@responseList', responseList)

							deferred.resolve()
							return response.data
						})
						.catch(function(err) {
							deferred.resolve();
							console.log('tableInit err =', err)
							EPCRServices.failAlert('錯誤！', '清單取得失敗！', null)
						})

				}
			})
		}

		function refreshList() {
			$scope.tableParams.reload();
		}
		$scope.tableParams = tableInit();

		var defaultSorting = {};

		function tableEMTDetail(emtId) {
			return new NgTableParams({
				sorting: defaultSorting
			}, {
				pages: [],
				counts: [],
				filterDelay: 300,
				getData: function(params) {
					var deferred = $q.defer();
					$scope.anyPageBusy = deferred.promise;
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

					return getEMTData(emtId)
						.then(function(response) {
							deferred.resolve()
							return response.EmtLevels
						})
						.catch(function(err) {
							deferred.resolve();
							console.log('tableInit err =', err)
						})

				}
			})
		}

		function EmtDetailRefreshList() {
			$scope.tableEMTDetail.reload()
		}

		function EmtTrainingRefreshList() {
			$scope.tableTrainingParams.reload()
		}

		function tableTrainingParams(emtId) {
			return new NgTableParams({
				sorting: defaultSorting
			}, {
				pages: [],
				counts: [],
				filterDelay: 300,
				getData: function(params) {
					var deferred = $q.defer();
					$scope.anyPageBusy = deferred.promise;
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

					return getEMTData(emtId)
						.then(function(response) {
							deferred.resolve()
							return response.Trainings
						})
						.catch(function(err) {
							deferred.resolve();
							console.log('tableInit err =', err)
						})

				}
			})
		}

		function dataInit() {
			return $http.get('/Branches', {
					params: {
						disabled: false
					},
					paramSerializer: '$httpParamSerializerJQLike'
				})
				.then(function(response) {
					$scope.branchList = response.data;
					return $http.get('/EmtLevels')
				})
				.then(function(response) {
					$scope.emtLevelList = response.data;
				})
		}
		dataInit()

	});
