SERVICES.factory('PcrQuestionService', function(jwtHelper, $http) {
	function getVersion() {
		return $http.get('/PcrVersions', {
				params: {
					isDefault: true
				},
				paramSerializer: '$httpParamSerializerJQLike'
			})
			.then(function(response) {
				// There shall only be 1 default version
				return response.data[0].id;
			});
	}


	function getJson(categoryId, versionId) {
		if (_.isNil(versionId)) {
			return getVersion()
				.then(function(versionId) {
					var PcrCategory = "json/" + versionId + '-' + categoryId + ".json";
					return $http.get(PcrCategory)
				})
				.then(function(response) {
					return response.data;
				});
		} // if
		else {
			var PcrCategory = "json/" + versionId + '-' + categoryId + ".json";
			return $http.get(PcrCategory)
				.then(function(response) {
					return response.data;
				});
		} // else
	}

	return {
		getVersion: getVersion,
		getJson: getJson
	}
});
