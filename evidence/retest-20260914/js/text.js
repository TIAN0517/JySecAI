angular.module('formlyCustomText',[])
.config(function(formlyConfigProvider){
	formlyConfigProvider.setType({
      name: 'Text',
      templateUrl: 'templates/formly/text.html',
      controller: function($scope, FormlyExtensionService) {
      	function EXTFUNC(func, args){
      		return FormlyExtensionService[func](args);
      	}
      	$scope.EXTFUNC = EXTFUNC;
      }

    });
});