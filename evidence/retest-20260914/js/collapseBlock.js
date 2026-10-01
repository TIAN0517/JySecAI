angular.module('formlyCustomCollapseBlock',[])
.config(function(formlyConfigProvider){
    formlyConfigProvider.setWrapper({
      name: 'collapseBlock',
      templateUrl: 'templates/formly/collapseBlock.html',
    });
});