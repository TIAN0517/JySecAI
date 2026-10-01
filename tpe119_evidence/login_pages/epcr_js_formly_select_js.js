angular.module('formlyCustomSelect', [])
.config(function(formlyConfigProvider) {
  formlyConfigProvider.setType({
      name: 'Select',
      templateUrl: 'templates/formly/select.html',
      defaultOptions(options) {
          /* jshint maxlen:195 */
          let ngOptions = options.templateOptions.ngOptions || `option[to.valueProp || 'value'] as option[to.labelProp || 'name'] group by option[to.groupProp || 'group'] for option in to.options`;
          return {
              ngModelAttrs: {
                  [ngOptions]: {
                      value: options.templateOptions.optionsAttr || 'ng-options'
                  }
              }
          };
      },
      apiCheck: check => ({
          templateOptions: {
              options: check.arrayOf(check.object),
              optionsAttr: check.string.optional,
              labelProp: check.string.optional,
              valueProp: check.string.optional,
              groupProp: check.string.optional
          }
      }),
      controller: function($scope, FormlyExtensionService){
        $scope.nextQuestionFilter = function(value, index, array){
          return angular.isArray(value.nextQuestions);
        }

        function EXTFUNC(func, args) {
            return FormlyExtensionService[func](args);
        }
        $scope.EXTFUNC = EXTFUNC;
      }
  });
});