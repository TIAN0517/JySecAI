angular.module('formlyCustomDate', [])
    .config(function(formlyConfigProvider) {
        formlyConfigProvider.setType({
            name: 'Date',
            templateUrl: 'templates/formly/date.html',
            defaultOptions: {
                templateOptions: {}
            },
            controller: function($scope, FormlyExtensionService) {
                $scope.moment = moment;

                function EXTFUNC(func, args) {
                    return FormlyExtensionService[func](args);
                }
                $scope.EXTFUNC = EXTFUNC;
            }

        });
    });