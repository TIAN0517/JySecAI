angular.module('formlyCustomRepeatSection',[])
.config(function(formlyConfigProvider){
	var unique = 1;
  formlyConfigProvider.setType({
    name: 'RepeatSection',
    templateUrl: 'templates/formly/repeatSection.html',
    controller: /* @ngInject */ function($scope, FormlyExtensionService) {
	    $scope.formOptions = {formState: $scope.formState};
      $scope.addNew = addNew;
      $scope.remove = remove;
      
      $scope.cleanData = cleanData;
      $scope.autoCreated = autoCreated;

      $scope.copyFields = copyFields;


      function copyFields(fields) {
        fields = angular.copy(fields);
        addRandomIds(fields);
        return fields;
      }

      function addNew() {
        $scope.model[$scope.options.key] = $scope.model[$scope.options.key] || [];
        var repeatsection = $scope.model[$scope.options.key];
        var lastSection = repeatsection[repeatsection.length - 1];
        var newsection = {};
        repeatsection.push(newsection);
      }

      function addRandomIds(fields) {
        unique++;
        angular.forEach(fields, function(field, index) {
          if (field.fieldGroup) {
            addRandomIds(field.fieldGroup);
            return; // fieldGroups don't need an ID
          }

          if (field.templateOptions && field.templateOptions.fields) {
            addRandomIds(field.templateOptions.fields);
          }

          field.id = field.id || (field.key + '_' + index + '_' + unique + getRandomInt(0, 9999));
        });
      }

      function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min)) + min;
      }

      function remove(index){
        $scope.model[$scope.options.key].splice(index, 1)
        if($scope.model[$scope.options.key].length==0){
          delete $scope.model[$scope.options.key]
        }
      }

      function EXTFUNC(func, args) {
          return FormlyExtensionService[func](args);
      }
      $scope.EXTFUNC = EXTFUNC;
      
      function cleanData(){
      	delete $scope.model[$scope.options.key];
      }
      function autoCreated(){
      	addNew();
      }

    }
  })
})
