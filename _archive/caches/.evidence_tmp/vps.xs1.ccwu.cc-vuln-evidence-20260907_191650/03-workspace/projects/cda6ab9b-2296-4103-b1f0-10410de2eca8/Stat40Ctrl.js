CONTROLLERS.controller('Stat40Ctrl',
	function($q, $modal, $scope, $state,
		NgTableParams, $http, $element, EPCRServices, AuthService) {
		// 40.	總表輸出
		$scope.search = {};
		// $scope.dateEnd = {};
		$scope.title = '總表輸出';

		// function getStat(search) {
		// 	return $http.get('/Stat/stat40', {
		// 			params: {
		// 				dateBegin: moment(search.dateBegin).startOf('day').format(),
		// 				dateEnd: moment(search.dateEnd).endOf('day').format()
		// 			},
		// 			paramSerializer: '$httpParamSerializerJQLike'
		// 		})
		// 		.then(function(response) {
		// 			return response.data;
		// 		});
		// } // getStat()
		//
		// // ---------------------------------------------------------------------------------------------
		//
		// function getQuestion() {
		// 	return $http.get('/pcrQuestions?count=1000')
		// 		.then(function(result) {
		// 			return result.data;
		// 		});
		// } // getQuestion()
		//
		// function getAmb() {
		// 	return $http.get('/ambs?count=1000')
		// 		.then(function(result) {
		// 			return result.data;
		// 		});
		// } // getAmb()

		// ---------------------------------------------------------------------------------------------

		function showStat(search, type) {
			// if (type == 'csv')
				window.open('/Stat/stat40?' +
					'dateBegin=' + moment(search.dateBegin).startOf('day').utc().format() +
					'&dateEnd=' + moment(search.dateEnd).endOf('day').utc().format() +
					'&type=' + type +
					'&token=' + AuthService.getToken());
			// $scope.fields = row;
			// $scope.tableData = [];
			// else {
			// 	return $http.get('/Stat/stat40', {
			// 			params: {
			// 				dateBegin: moment(search.dateBegin).startOf('day').format(),
			// 				dateEnd: moment(search.dateBegin).endOf('day').format(),
			// 				type: type
			// 			},
			// 			paramSerializer: '$httpParamSerializerJQLike'
			// 		})
			// 		.then(function(response) {
			// 			console.log(response);
			// 			// return response.data;
			// 		});
			// } // else
			// return $q.all({
			// 		ambs: getAmb(),
			// 		questions: getQuestion()
			// 	}).then(function(columns) {
			// 		// console.log('columns', columns);
			// 		angular.forEach(columns.ambs, function(amb) {
			// 			$scope.fields['amb_' + amb.id] = amb.desciption;
			// 		});
			// 		angular.forEach(columns.questions, function(question) {
			// 			$scope.fields[question.code] = question.displayLabel;
			// 		});
			//
			// 		return getStat(search);
			// 	})
			// 	.then(function(results) {
			// 		console.log(results);
			//
			// 		angular.forEach(results, function(pcr) {
			// 			var row = {};
			// 			row = setPcr(row, pcr);
			// 			row = setDispatchRecord(row, pcr.DispatchRecord);
			//
			//
			// 			$scope.tableData.push(row);
			// 		});
			// 	})
			// 	.catch(function(error) {
			// 		console.log(error);
			// 		EPCRServices.failAlert('錯誤', '取得統計結果時發生錯誤');
			// 	});
		} // showStat()

		// function setPcr(row, pcr) {
		// 	if (!_.isNil(pcr)) {
		// 		// datetime
		// 		row['pcrcontactedAt'] = format_datetime(pcr['contactedAt']); // '接觸病患時間'
		// 		row['pcrarrivedHospitalAt'] = format_datetime(pcr['arrivedHospitalAt']); // '抵達醫院時間'
		// 		row['pcrhandOverAt'] = format_datetime(pcr['handOverAt']); // '完成交接時間'
		// 		row['pcrleftHospitalAt'] = format_datetime(pcr['leftHospitalAt']); // '離開醫院時間'
		// 		// string
		// 		row['pcrname'] = pcr['name']; // '患者姓名'
		// 		row['pcridentityNo'] = pcr['identityNo']; // '患者身分證號'
		// 		row['pcrweight'] = pcr['weight']; // '患者體重'
		// 		row['pcrpatientAddress'] = pcr['patientAddress']; // '患者住址'
		// 		row['pcrtelephone'] = pcr['telephone']; // '患者電話'
		// 		row['pcrreasonOfUnableToSign'] = pcr['reasonOfUnableToSign']; // '患者無法簽名原因'
		// 		row['pcrsceneAddress'] = pcr['sceneAddress']; // '實際案發地址'
		// 		row['pcrlongitude'] = pcr['longitude']; // '實際經度'
		// 		row['pcrlatitude'] = pcr['latitude']; // '實際緯度'
		// 		row['pcrcustomRelationship'] = pcr['customRelationship']; // '與患者的關係'
		// 		row['pcrPcrType'] = _.isNil(pcr['PcrType']) ? '' : pcr['PcrType']['name']; // '案類'
		// 		row['pcrAwareness'] = _.isNil(pcr['Awareness']) ? '' : pcr['Awareness']['name']; // '意識'
		// 		row['pcrSymptom'] = _.isNil(pcr['Symptom']) ? '' : pcr['Symptom']['name']; // '症狀'
		// 		row['pcrDeathAssessment'] = _.isNil(pcr['DeathAssessment']) ? '' : pcr['DeathAssessment']['name']; // '明顯死亡原因'
		// 		row['pcrHospitalTriageLevel'] = _.isNil(pcr['HospitalTriageLevel']) ? '' : pcr['HospitalTriageLevel']['name']; // '檢傷分級'
		// 		row['pcrDesignatedHospitalReason'] = _.isNil(pcr['DesignatedHospitalReason']) ? '' : pcr['DesignatedHospitalReason']['name']; // '送醫分類'
		// 		row['pcrReasonToChooseFullHospital'] = _.isNil(pcr['ReasonToChooseFullHospital']) ? '' : pcr['ReasonToChooseFullHospital']['name']; // '滿床仍要送醫的理由'
		// 		row['pcrReasonOfRefuseToProvideTelephone'] = _.isNil(pcr['ReasonOfRefuseToProvideTelephone']) ? '' : pcr['ReasonOfRefuseToProvideTelephone']['name']; // '無法提供電話的理由'
		// 		// boolean
		// 		row['pcrunableToSign'] = format_boolean(pcr['unableToSign']); // '患者無法簽名'
		// 		row['pcrrefuseToProvideTelephone'] = format_boolean(pcr['refuseToProvideTelephone']); // '患者拒絕提供電話'
		// 		row['pcremtHaveExplained'] = format_boolean(pcr['emtHaveExplained']); // '有無解釋指定送醫的風險'
		// 		row['pcragreedToUsePersonalInfo'] = format_boolean(pcr['agreedToUsePersonalInfo']); // '同意個資使用'
		// 		row['pcrisEmergency'] = format_boolean(pcr['isEmergency']); // '是否危急'
		// 		row['pcrstrecherNotReturned'] = format_boolean(pcr['strecherNotReturned']); // '扣床'
		// 		// calculation
		// 		row['pcrage'] = !_.isNumber(pcr['age']) ? '' : Math.round(pcr['age'] / 12); // '患者年齡'
		//
		// 		row['pcrEmts'] = sethasMany(row['pcrEmts'], pcr['Emts'], 'name'); // 'EMT'
		// 		row['pcrCaseDescriptions'] = sethasMany(row['pcrCaseDescriptions'], pcr['CaseDescriptions'], 'description'); // '補述欄'
		//
		// 		row = setAmbs(row, pcr['Ambs']);
		// 		angular.forEach(pcr['PcrBundles'], function(pcrbundle) {
		// 			row = setPcrBundle(row, pcrbundle);
		// 		});
		// 	} // if
		//
		// 	return row;
		// } // setPcr()
		//
		// function setAmbs(row, ambs) {
		// 	angular.forEach(ambs, function(amb) {
		// 		row['amb_' + amb.id] = format_boolean(amb['AmbPcrMap']['answer']);
		// 	});
		//
		// 	return row;
		// } // setAmbs()
		//
		// function setDispatchRecord(row, dispatchrecord) {
		// 	if (!_.isNil(dispatchrecord)) {
		// 		// datetime
		// 		row['dispatchedAt'] = format_datetime(dispatchrecord['dispatchedAt']); // '派遣時間'
		// 		row['departedAt'] = format_datetime(dispatchrecord['departedAt']); // '出勤時間'
		// 		row['arrivedAt'] = format_datetime(dispatchrecord['arrivedAt']); // '抵達時間'
		// 		row['leftAt'] = format_datetime(dispatchrecord['leftAt']); // '離開現場時間'
		// 		row['returnedBaseAt'] = format_datetime(dispatchrecord['returnedBaseAt']); // '返隊時間'
		// 		row['canceledAt'] = format_datetime(dispatchrecord['canceledAt']); // '取消派遣時間'
		// 		// string
		// 		row['DispatchCancelReason'] = _.isNil(dispatchrecord['DispatchCancelReason']) ? '' : dispatchrecord['DispatchCancelReason']['name']; // '拒絕出勤原因'
		// 		// boolean
		// 		row['refusedAt'] = format_boolean(dispatchrecord['refusedAt']); // '拒絕出勤'
		// 		row['hasTP'] = format_boolean(dispatchrecord['hasTP']); // '有無TP'
		// 		row = setAmbulance(row, dispatchrecord['Ambulance']);
		// 		row = setCaseRecord(row, dispatchrecord['CaseRecord']);
		// 	} // if
		//
		// 	return row;
		// } // setDispatchRecord()
		//
		// function setAmbulance(row, ambulance) {
		// 	if (!_.isNil(ambulance)) {
		// 		row['ambulance'] = ambulance['code']; // '車號'
		// 		row = setBranch(row, ambulance['Branch']);
		// 	} // if
		//
		// 	return row;
		// } // setAmbulance()
		//
		// function setBranch(row, branch) {
		// 	if (!_.isNil(branch)) {
		// 		row['branch'] = branch['name']; // '分隊'
		// 		row = setBranchGroup(row, branch['BranchGroup']);
		// 	} // if
		//
		// 	return row;
		// } // setBranch()
		//
		// function setBranchGroup(row, branchgroup) {
		// 	if (!_.isNil(branchgroup)) {
		// 		row['branchgroup'] = branchgroup['name']; // '大隊'
		// 	} // if
		//
		// 	return row;
		// } // setBranchGroup()
		//
		// function setCaseRecord(row, caserecord) {
		// 	if (!_.isNil(caserecord)) {
		// 		// datetime
		// 		row['endedAt'] = format_datetime(caserecord['endedAt']); // '結案時間'
		// 		row['mciBeganAt'] = format_datetime(caserecord['mciBeganAt']); // '宣告大傷開始'
		// 		// string
		// 		row['recordUuid'] = caserecord['recordUuid']; // '案件號'
		// 		row['address'] = caserecord['address']; // '案發地址'
		// 		row['longitude'] = caserecord['longitude']; // '報案經度'
		// 		row['latitude'] = caserecord['latitude']; // '報案緯度'
		// 		row['reporterPhone'] = caserecord['reporterPhone']; // '報案電話'
		// 	} // if
		//
		// 	return row;
		// } // setCaseRecord()
		//
		// function setPcrBundle(row, pcrbundle) {
		// 	if (!_.isNil(pcrbundle)) {
		// 		angular.forEach(pcrbundle['PcrRecords'], function(pcrrecord) {
		// 			row = setPcrRecord(row, pcrrecord);
		// 		});
		// 	} // if
		//
		// 	return row;
		// } // setPcrBundle();
		//
		// function setPcrRecord(row, pcrrecord) {
		// 	if (!_.isNil(pcrrecord)) {
		// 		var key = pcrrecord['PcrQuestion']['code'];
		// 		var type = pcrrecord['PcrQuestion']['PcrQuestionType']['questionType'];
		// 		row[key] = getAnswerValue(pcrrecord['PcrAnswerRecords'], type);
		// 	} // if
		//
		// 	return row;
		// } // setPcrRecord()
		//
		// function getAnswerValue(pcranswerrecords, type) {
		// 	switch (type) {
		// 		case 'DateTime':
		// 			return format_datetime(pcranswerrecords[0]['freeTypingValue']);
		// 		case 'Int':
		// 		case 'Text':
		// 			return pcranswerrecords[0]['freeTypingValue'];
		// 		case 'Checkbox':
		// 		case 'Select':
		// 			var answers = null;
		// 			angular.forEach(pcranswerrecords, function(pcranswerrecord) {
		// 				if (!_.isNil(pcranswerrecord)) {
		// 					if (_.isNil(answers)) answers = pcranswerrecord['PcrAnswer']['displayLabel'];
		// 					else answers += '、' + pcranswerrecord['PcrAnswer']['displayLabel'];
		// 				} // if
		// 			});
		// 			return answers;
		// 		default:
		// 			return '';
		// 	} // switch
		// } // getAnswerValue()
		//
		// // ---------------------------------------------------------------------------------------------
		//
		// function sethasMany(column, datas, key) {
		// 	angular.forEach(datas, function(data) {
		// 		if (!_.isNil(data[key])) {
		// 			if (_.isNil(column)) column = data[key];
		// 			else column += '、' + data[key];
		// 		} // if
		// 	});
		//
		// 	return column;
		// } // sethasMany()
		//
		// function format_datetime(datetime) {
		// 	if (_.isNil(datetime)) return datetime;
		// 	else return moment(datetime).format('YYYY-MM-DD HH:mm:ss');
		// } // format_datetime()
		//
		// function format_boolean(boolean) {
		// 	if (_.isNil(boolean)) return boolean;
		// 	else return boolean ? '是' : '否';
		// } // format_boolean()
		//
		// // =============================================================================================

		$scope.showStat = showStat;

		$scope.datetimeCheck = function(search) {
			return !moment(search.dateBegin).isSameOrBefore(moment(search.dateEnd));
		};

		// =============================================================================================

		// var row = {
		// 	// caserecord
		// 	recordUuid: '案件號',
		// 	endedAt: '結案時間',
		// 	mciBeganAt: '宣告大傷開始',
		// 	address: '案發地址',
		// 	longitude: '報案經度',
		// 	latitude: '報案緯度',
		// 	reporterPhone: '報案電話',
		// 	// branchgroup, branch, ambulance
		// 	branchgroup: '大隊',
		// 	branch: '分隊',
		// 	ambulance: '車號',
		// 	// DispatchRecordController
		// 	dispatchedAt: '派遣時間',
		// 	departedAt: '出勤時間',
		// 	arrivedAt: '抵達時間',
		// 	leftAt: '離開現場時間',
		// 	returnedBaseAt: '返隊時間',
		// 	canceledAt: '取消派遣時間',
		// 	refusedAt: '拒絕出勤',
		// 	hasTP: '有無TP',
		// 	DispatchCancelReason: '拒絕出勤原因',
		// 	// Pcr
		// 	pcrcontactedAt: '接觸病患時間',
		// 	pcrarrivedHospitalAt: '抵達醫院時間',
		// 	pcrhandOverAt: '完成交接時間',
		// 	pcrleftHospitalAt: '離開醫院時間',
		// 	pcrname: '患者姓名',
		// 	pcridentityNo: '患者身分證號',
		// 	pcrage: '患者年齡',
		// 	pcrweight: '患者體重',
		// 	pcrpatientAddress: '患者住址',
		// 	pcrrefuseToProvideTelephone: '患者拒絕提供電話',
		// 	pcrtelephone: '患者電話',
		// 	pcrunableToSign: '患者無法簽名',
		// 	pcrreasonOfUnableToSign: '患者無法簽名原因',
		// 	pcremtHaveExplained: '有無解釋指定送醫的風險',
		// 	pcragreedToUsePersonalInfo: '同意個資使用',
		// 	pcrsceneAddress: '實際案發地址',
		// 	pcrlongitude: '實際經度',
		// 	pcrlatitude: '實際緯度',
		// 	pcrisEmergency: '是否危急',
		// 	pcrstrecherNotReturned: '扣床',
		// 	pcrcustomRelationship: '與患者的關係',
		// 	// Pcr BelongsTo
		// 	pcrPcrType: '案類',
		// 	pcrAwareness: '意識',
		// 	pcrSymptom: '症狀',
		// 	pcrDeathAssessment: '明顯死亡原因',
		// 	pcrHospitalTriageLevel: '檢傷分級',
		// 	pcrDesignatedHospitalReason: '送醫分類',
		// 	pcrReasonToChooseFullHospital: '滿床仍要送醫的理由',
		// 	pcrReasonOfRefuseToProvideTelephone: '無法提供電話的理由',
		// 	// Pcr HasMany
		// 	pcrEmts: 'EMT',
		// 	pcrCaseDescriptions: '補述欄',
		// 	// Pcr BelongsToMany
		// 	pcrAmbs: '垂片'
		// };

	});
