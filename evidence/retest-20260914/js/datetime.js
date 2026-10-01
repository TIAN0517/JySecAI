angular.module('formlyCustomDateTime', [])
    .config(function(formlyConfigProvider) {
        formlyConfigProvider.setType({
            name: 'DateTime',
            templateUrl: 'templates/formly/datetime.html',
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