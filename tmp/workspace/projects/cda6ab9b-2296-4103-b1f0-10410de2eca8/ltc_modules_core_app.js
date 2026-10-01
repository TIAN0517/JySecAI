app.run(function($rootScope, $location, $cookies, $http, $window, $state, urlSetting, util, baseHttp) {

	// $rootScope.mainUrl = urlSetting.frontend + "#/main";
	$rootScope.mainUrl = urlSetting.frontend;

	$rootScope.$on('$stateChangeSuccess', function() {

		$("html, body").animate({
			scrollTop: 0
		}, 200);

		$('html').removeClass('nav-open');

		if ($('nav').hasClass('navbar-absolute')) {
			$('html').removeClass('nav-open-absolute');
		}
		materialKit.misc.navbar_menu_visible = 0;
		$('#bodyClick').remove();
		setTimeout(function() {
			$('.navbar-toggler').removeClass('toggled');
		}, 550);
	});

	$rootScope.logout = function() {
		console.log("logout");
		$http.post(urlSetting.serviceUrl + 'api_app/tologout', null).then(
			function(data) {
				if (data.data.res == 1) {
					$rootScope.isLogin = false;
					$rootScope.currentUser = null;
					$state.go('home');
				} else {
					alert('登出失敗');
				}
			},
			function error(msg) {
				alert('登出失敗');
			}
		)
	}
})