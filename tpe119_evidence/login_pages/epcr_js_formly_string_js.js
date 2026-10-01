angular.module('formlyCustomString',[])
.config(function(formlyConfigProvider){
	formlyConfigProvider.setType({
      name: 'String',
      templateUrl: 'templates/formly/string.html',
      controller: function($scope, FormlyExtensionService) {
      	function EXTFUNC(func, args){
      		return FormlyExtensionService[func](args);
      	}
      	$scope.EXTFUNC = EXTFUNC;
      }
    });
});