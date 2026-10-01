SERVICES.factory('FormlyExtensionService', function(AuthService) {
	function getAuthorName(){
		var currentUser = AuthService.getCurrentUser();
		return currentUser.name;
	}

	/*
		從某題 RepeatSection 裏的某題累加結果
		input:
		{
			model: object[], 	// RepeatSection 的內容, ex. model.OHCAQC4_3
			qCode: string 		// 在RepeatSection裏要累加的 question code ex. OHCAQC4_6
		}
		output:
			int
	*/
	function calFromRepeatSection(objInput){
		var total = 0;

		if(_.isNil(objInput) || _.isNil(objInput.model) || _.isNil(objInput.qCode)){
			return 0;
		}else{
			var key = objInput.qCode;

			for(var idx in objInput.model){
				var oneData = objInput.model[idx];

				if(!_.isNil(oneData[key])){
					total = total + parseInt(oneData[key])
				}
			}

			return total;
		}
	}

	/*
		(客製)N小時內出院則設為非必填，關連 model.$arrivedHospitalAt, model.OHCA29(出院日期)
		input:
		{
			model: object, 		// 整包 model
			field: object,      // 此題的 field，執行後可能會改變它的 required 值
			hours: int  		// 超過多個小時要變必填
		}
		output:
			null
	*/
	function notRequiredUnderHours(objInput){

		if(_.isNil(objInput) || 
			_.isNil(objInput.model) || 
			_.isNil(objInput.model.$arrivedHospitalAt) || 
			_.isNil(objInput.model.OHCA29) ||
			_.isNil(objInput.hours)){
			
			// donothing
		}else{
			var dtArrivedHospitalAt = objInput.model.$arrivedHospitalAt;
			var dischargeAt = objInput.model.OHCA29;
			var minsToCheck = objInput.hours * 60;
			// 去掉時間，若相差為小於等於24小時，則回傳 true
			var diffMins = moment(dischargeAt).startOf('day').diff(moment(dtArrivedHospitalAt).startOf('day'),'minutes');

			if(diffMins <= minsToCheck){	// 因為不含時間，所以需要等
				objInput.field.templateOptions.required = false;
			}else{
				objInput.field.templateOptions.required = true;
			}
		}
	}

	return {
		getAuthorName:getAuthorName,
		calFromRepeatSection:calFromRepeatSection,
		notRequiredUnderHours:notRequiredUnderHours
	}

	
})