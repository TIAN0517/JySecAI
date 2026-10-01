angular.module('formlyCustomInt', ['ui.utils.masks'])
    .config(function(formlyConfigProvider) {
        formlyConfigProvider.setType({
            name: 'Int',
            templateUrl: 'templates/formly/int.html',
            controller: function($scope, FormlyExtensionService) {
                $scope.moment = moment;

                function EXTFUNC(func, args) {
                    return FormlyExtensionService[func](args);
                }
                $scope.EXTFUNC = EXTFUNC;

            }
        });
    });