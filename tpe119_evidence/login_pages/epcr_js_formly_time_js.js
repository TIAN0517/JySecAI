angular.module('formlyCustomTime', [])
    .config(function(formlyConfigProvider) {
        formlyConfigProvider.setType({
            name: 'Time',
            templateUrl: 'templates/formly/time.html',
            defaultOptions: {
                templateOptions: {}
            },
            controller: function($scope, FormlyExtensionService) {
                function EXTFUNC(func, args) {
                    return FormlyExtensionService[func](args);
                }
                $scope.EXTFUNC = EXTFUNC;
            }

        });
    });