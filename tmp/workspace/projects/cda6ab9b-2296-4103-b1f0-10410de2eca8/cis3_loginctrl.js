angular.module('loginapp',	['ngAnimate', 'ui.bootstrap']);
var loginapp = angular.module('loginapp');
loginapp.controller('modalController', 
		['$scope', '$modalInstance', 'items',
		 function($scope, $modalInstance, items) {
	
	$scope.items = items;
			
	$scope.ok = function () {
		//alert('ok clicked');
		$modalInstance.close();
	};
}]);
loginapp.service('modalService', 
		['$modal',
		 function($modal) {
	   
	   this.open = function(size, modalItems) {
		    var modalInstance = $modal.open({
		      animation: true,
		      templateUrl: 'view_popup_Fail.html',
		      controller: 'modalController',
		      size: size,
		      resolve: {
		        items: function () {
		          return modalItems;
		        }
		      }
		    });
		    modalInstance.result.then(function (selectedItem) {
		      //alert('return ok');
		    }, function () {
			  //alert('return err');	    	
		    });
	   };
}]);
loginapp.service('qrcodeService', ['$q', '$http', '$log', function ($q, $http, $log) {
	this.getQrCode = function () {
		$log.log('getQrCode');
		var deferred = $q.defer();
		$http.get('https://tcit.tzuchi.net/LoginAuth/rs/Login/code')
			.success(function (data, status, headers, config) {
				deferred.resolve(data);
			})
			.error(function (data, status, headers, config) {
				deferred.reject(data);
			});
		return deferred.promise;
	};

	this.checkStatus = function (code) {
		$log.log('checkStatus');
		var deferred = $q.defer();

		/*
		$http.get('https://tcit.tzuchi.net/LoginAuth/rs/Login/status/'+code)
			.success(function (data, status, headers, config) {
				deferred.resolve(data);
			})
			.error(function (data, status, headers, config) {
				deferred.reject(data);
			});
		*/
		$http({
			url: 'https://tcit.tzuchi.net/LoginAuth/rs/Login/status/'+code,
			method: 'GET',
			transformResponse: [function (data) {
				// Do whatever you want!
				deferred.resolve(data);
			}]
		  });	
		return deferred.promise;
	};
}]);
loginapp.controller('loginController', ['$scope', 'modalService', 'qrcodeService',
		 function($scope, modalService, qrcodeService) {
	
			$scope.username = undefined;
			$scope.password = undefined;

			$scope.imageItem = undefined;
			$scope.interval = undefined;
			$scope.timeout= false;
			
			$scope.mysubmit = function() {
				if ($scope.username == undefined || $scope.password == undefined) {
					//alert('請先輸入帳號與密碼');
					$scope.modalItems = ['資料錯誤!', '請輸入正確的帳號及密碼，感恩'];
			    	modalService.open(null, $scope.modalItems);
			    	   
				} else if ($scope.username == undefined && $scope.password == undefined) {
					//alert('請先輸入帳號與密碼');
					$scope.modalItems = ['資料錯誤!', '請輸入帳號、密碼，感恩'];
			    	modalService.open(null, $scope.modalItems);
			    	   
				} else {
					$('#loginForm').submit();					
				}
			};
			$scope.searchKeyPress = function(e) {
				// look for window.event in case event isn't passed in
				if (typeof e == 'undefined' && window.event) {
					e = window.event;
				}
				if (e.keyCode == 13) {
					$scope.mysubmit();
				}
			};

			//Login.html初始化
			$scope.loginInit = function(){
				$scope.qrcodeInit();
				var url = window.location.href;						//lastIndexOf找不到 = -1
				if (url.lastIndexOf('error=login') != -1) {			
					//alert('請檢查您的帳號與密碼!');
					$scope.modalItems = ['資料錯誤!', '帳號、密碼錯誤，請重新輸入，感恩'];
			    	modalService.open(null, $scope.modalItems);
				} 
				
				//if (url.lastIndexOf('error=session') != -1) {
				//	$scope.modalItems = ['程式逾期!!!', '請重新登入系統，感恩'];
			    //	modalService.open(null, $scope.modalItems);					
				//}
				
				if (url.lastIndexOf('error=access') != -1) {
					$scope.modalItems = ['權限問題!', '您沒有使用權限，請與相關人員連絡，感恩'];
			    	modalService.open(null, $scope.modalItems);					
				}
				if (url.lastIndexOf('denied') != -1) {
					$scope.modalItems = ['權限問題!', '您沒有使用權限，請與相關人員連絡，感恩'];
			    	modalService.open(null, $scope.modalItems);					
				}
			};

			$scope.qrcodeInit = function() {
				$scope.timeout= false;
				qrcodeService.getQrCode().then (
					function(data) {
						$scope.imageItem = data;
						//$scope.imageItem.img = "data:image/png;base64,"+$scope.imageItem.img;
						$scope.interval = setInterval(() => {
							$scope.checkStatus();
						}, 1000);
						setTimeout(() => {
						  clearInterval($scope.interval);
						$scope.timeout = true;
						}, 60000);
				  })
			}

			$scope.checkStatus = function() {
				qrcodeService.checkStatus($scope.imageItem.code).then (
					function(data) {
						if(data!=''){
							clearInterval($scope.interval);
							$("#j_qrusername").val(data);
							$('#qrcodeForm').submit();	
						}
				  })
			}
			
}]);

