angular.module('formlyCustomDisplay', [])
    .config(function(formlyConfigProvider) {
        formlyConfigProvider.setType({
            name: 'Display',
            templateUrl: 'templates/formly/display.html',
            controller: function($scope, FormlyExtensionService) {
                $scope.moment = moment;

                function EXTFUNC(func, args) {
                    return FormlyExtensionService[func](args);
                }
                $scope.EXTFUNC = EXTFUNC;

                function checkDatetime(value, format, postFix){
                    var _postFix = '';

                    if(!_.isNil(postFix)){
                        _postFix = postFix;
                    }

                    if(format && moment(value).isValid()){
                        return moment(value).format(format) + _postFix;
                    }else{
                        if(_.isNil(value)){
                            return '';
                        }else{
                            return value + _postFix;
                        }
                    }
                }
                $scope.checkDatetime = checkDatetime;

            }
        });
    });