SERVICES.factory('PcrQuestionService', function(jwtHelper, $http, $q){
	function getVersion(){
      return $http.get('/PcrVersions', {
                params: { isDefault: true },
                paramSerializer: '$httpParamSerializerJQLike'
            })
            .then(function(response){
              // There shall only be 1 default version
              return response.data[0].id;
            });
    }


    function getJson(categoryId, versionId) {
        var chain;
        if(versionId){
            chain = $q.when(versionId);
        }else{
            chain = getVersion();
        }
        return chain.then(function(versionId){
                var PcrCategory = "json/" + versionId + '-' + categoryId + ".json";
                return $http.get(PcrCategory)
            })
            .then(function(response){
              return response.data;
            });
    }

    return {
    	getVersion: getVersion,
    	getJson: getJson
    }
});
