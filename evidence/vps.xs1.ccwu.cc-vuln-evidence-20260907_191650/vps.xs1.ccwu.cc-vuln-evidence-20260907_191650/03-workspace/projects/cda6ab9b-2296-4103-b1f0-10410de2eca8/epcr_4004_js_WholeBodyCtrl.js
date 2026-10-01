CONTROLLERS.controller('WholeBodyCtrl', function($scope, $rootScope){
	$scope.handleClick = function(){
		$rootScope.$emit('WholeBodyCtrl.userAlive');
	};
});
