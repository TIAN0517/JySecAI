app.factory('homeService', function(baseHttp) {
	return {
		queryHome: function(params, callback) {
			return baseHttp.service('api_backend/queryHome', params, callback);
		},
		queryNewsList: function(params, callback) {
			return baseHttp.service('api_backend/queryNewsList', params, callback);
		},
		queryPostList: function(params, callback) {
			return baseHttp.service('api_backend/queryPostList', params, callback);
		},
		queryCourseList: function(params, callback) {
			return baseHttp.service('api_backend/queryCourseList', params, callback);
		},
		queryAllList: function(params, callback) {
			return baseHttp.service('api_backend/queryAllList', params, callback);
		},
		queryAbout: function(params, callback) {
			return baseHttp.service('api_backend/queryAbout', params, callback);
		},
		queryFriendlyLinkList: function(params, callback) {
			return baseHttp.service('api_backend/queryFriendlyLinkList', params, callback);
		},

	}
})
app.controller('homeController', function($rootScope, $scope, $window, $location, $http, $filter, $state, $modal, homeService, util, $sce) {

	$scope.home = [];
	$scope.news = [];
	$scope.post = [];
	$scope.course = [];
	$scope.all = [];

	// var queryAll = function () {

	//     var All = $filter('orderBy')(AllList, 'postTime');
	//     console.log(All);
	//     for (var i = 0; i < 5; i++) {
	//         // 顯示表格資料 
	//         $scope.all.push(All[i]);
	//     }
	// }

	$scope.queryAllList = function() {

		var param = {
			'isOnApp': 1
		};
		homeService.queryAllList(param, function(data, status, headers, config) {
			if (data.result) {
				$scope.allList = data.data;
				// $scope.allList = $scope.allList.sort(function (a, b) {
				//     return a.allDate - b.allDate;
				// });

				// $scope.allList.sort(function (a, b) {
				//     return a.allDate - b.allDate;
				// });

				var resultArray = $.map($scope.allList, function(value, index) {
					return [value];
				});
				let resultArrayList = [...resultArray[0], ...resultArray[1], ...resultArray[2], ...resultArray[3]]
				// resultArrayList.sort();


				resultArrayList.sort(function(a, b) {
					return b.allDate - a.allDate;
				});
				// $scope.allList = $filter('orderBy')($scope.allList, $scope.allList.allDate)

				// $scope.allList = orderBy($scope.allList, $scope.allList.allDate);


				for (var i = 0; i < 5; i++) {
					// 顯示表格資料 
					$scope.all.push(resultArrayList[i]);
				}
			}
		})
	};
	$scope.queryAllList();

	$scope.queryHome = function() {

		var param = {
			"homeId": 1
		};
		homeService.queryHome(param, function(data, status, headers, config) {
			if (data.result) {
				$scope.homeList = data.data;

				// 顯示表格資料 
				$scope.home = $scope.homeList;

				let regexp = /https?:\/\/(?:[0-9A-Z-]+\.)?(?:youtu\.be\/|youtube(?:-nocookie)?\.com\S*?[^\w\s-])([\w-]{11})(?=[^\w-]|$)(?![?=&+%\w.-]*(?:['"][^<>]*>|<\/a>))[?=&+%\w.-]*/ig;
				$scope.videoId = $scope.home.mainVideo.replace(regexp, '$1');
				$scope.Video1 = "https://www.youtube.com/embed/" + $scope.home.mainVideo.replace(regexp, '$1');
				if ($scope.home.mainVideo2 != null && $scope.home.mainVideo2 != '') {
					$scope.videoId2 = $scope.home.mainVideo2.replace(regexp, '$1');
					$scope.Video2 = "https://www.youtube.com/embed/" + $scope.home.mainVideo2.replace(regexp, '$1');
				} else {
					$scope.Video2 = null;
					$scope.home.mainVideo2 = null;
				}
				if ($scope.home.mainVideo3 != null && $scope.home.mainVideo3 != '') {
					$scope.videoId3 = $scope.home.mainVideo3.replace(regexp, '$1');
					$scope.Video3 = "https://www.youtube.com/embed/" + $scope.home.mainVideo3.replace(regexp, '$1');
				} else {
					$scope.videoId3 = null;
					$scope.Video3 = null;
					$scope.home.mainVideo3 = null;
			}
		}})
	};
	$scope.queryHome();

	// 輪播畫面
	$('#carouselExampleIndicators').carousel({
		interval: 8000 // 跳轉時間
	});
	$('#carouselExampleIndicators').on('slid.bs.carousel.from', function() {

		let pageIndex = $('div.active').index(); // 當前頁碼
		let iframes1 = document.getElementById('youtubeVideo');
		let iframes2 = document.getElementById('youtubeVideo2');
		let iframes3 = document.getElementById('youtubeVideo3');
		if (iframes1 === null && iframes2 === null && iframes3 === null) { // 沒影片
			console.log('No video set.')
		} else if (iframes1 !== null && iframes2 === null && iframes3 === null) { // 0
			console.log(iframes1.contentWindow.length)
			if (pageIndex === 0) { // 當目前頁碼為0(第一頁)時
				iframes1.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'playVideo' }), '*'); 	// 播放影片
			} else { // 反之 都關
				iframes1.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'pauseVideo' }), '*'); 	// 暫停影片
			}
		} else if (iframes1 !== null && iframes2 !== null && iframes3 === null) { // 0, 1
			if (pageIndex === 0) { // 當目前頁碼為0(第一頁)時
				iframes1.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'playVideo' }), '*'); 	// 播放影片
				iframes2.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'pauseVideo' }), '*'); // 暫停影片
			} else if (pageIndex === 1) {
				iframes1.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'pauseVideo' }), '*'); // 暫停影片
				iframes2.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'playVideo' }), '*'); 	// 播放影片
			} else { // 反之 都關
				iframes1.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'pauseVideo' }), '*'); 	// 暫停影片
				iframes2.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'pauseVideo' }), '*'); // 暫停影片
			}
		} else if (iframes1 !== null && iframes2 !== null && iframes3 !== null) { // 0, 1, 2
			if (pageIndex === 0) { // 當目前頁碼為0(第一頁)時
				iframes1.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'playVideo'}), '*'); 	// 播放影片
				iframes2.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'pauseVideo'}), '*'); // 暫停影片
				iframes3.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'pauseVideo'}), '*'); // 暫停影片
			} else if (pageIndex === 1) {
				iframes1.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'pauseVideo'}), '*'); 	// 播放影片
				iframes2.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'playVideo'}), '*'); // 暫停影片
				iframes3.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'pauseVideo'}), '*'); // 暫停影片
			} else if (pageIndex === 2) {
				iframes1.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'pauseVideo'}), '*'); 	// 播放影片
				iframes2.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'pauseVideo'}), '*'); // 暫停影片
				iframes3.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'playVideo'}), '*'); // 暫停影片
			} else { // 反之 都關
				iframes1.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'pauseVideo'}), '*'); 	// 暫停影片
				iframes2.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'pauseVideo'}), '*'); // 暫停影片
				iframes3.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'pauseVideo'}), '*'); // 暫停影片
			}
		}
	});

	$scope.queryNewsList = function() {
		var param = {
			'isOnApp': 1
		};
		homeService.queryNewsList(param, function(data, status, headers, config) {
			if (data.result) {
				$scope.newsList = data.data;

				for (var i = 0; i < 10; i++) {
					// 顯示表格資料 
					$scope.news.push($scope.newsList[i]);
				}
			}
		})
	};
	$scope.queryNewsList();

	$scope.queryPostList = function() {
		var param = {
			'isOnApp': 1
		};
		homeService.queryPostList(param, function(data, status, headers, config) {
			if (data.result) {
				$scope.postList = data.data;

				for (var i = 0; i < 3; i++) {
					// 顯示表格資料 
					$scope.post.push($scope.postList[i]);
				}
			}
		})
	};
	$scope.queryPostList();

	$scope.queryCourseList = function() {
		var param = {
			'isOnApp': 1
		};
		homeService.queryCourseList(param, function(data, status, headers, config) {
			if (data.result) {
				$scope.courseList = data.data;

				for (var i = 0; i < 3; i++) {
					// 顯示表格資料 
					$scope.course.push($scope.courseList[i]);
				}
			}
		})
	};
	$scope.queryCourseList();

	$scope.openArticle = function(fn, id) {
		$state.go('article', {
			fn: fn,
			id: id
		});

	}

	$scope.openCoursePage = function(id) {
		$state.go('coursepage', {
			id: id
		});

	}
	$scope.goSearch = function(str) {
		if (str != null && str != undefined && str != '') {
			$state.go('searchresult', {
				str: str
			});
		} else {
			alert("請輸入搜尋值!");
		}

	}

	$scope.queryAbout = function() {

		var param = {
			"aboutId": 1
		};
		homeService.queryAbout(param, function(data, status, headers, config) {
			if (data.result) {
				$scope.about = data.data;


			}
		})
	};
	$scope.queryAbout();

	$(document).ready(function() {
		$("masonry").masonry({
			itemSelector: '.masonry-item',
			percentPosition: true,
			animate: true
		}).imagesLoaded(function() {
			$('masonry').masonry('reload');
		});
	})

	$scope.queryFriendlyLinkList = function(param) {
		homeService.queryFriendlyLinkList(param, function(data, status, headers, config) {
			if (data.result) {
				$scope.friendlyLinkList = data.data;
				setTimeout(function() {
					$scope.owlCarousel();
				}, 1000);
			}
		})
	};
	$scope.queryFriendlyLinkList();

	$scope.owlCarousel = function() {
		var owl = $('.owl-carousel');
		if (typeof owl.data('owlCarousel') != 'undefined') {
			owl.data('owlCarousel').destroy();
			owl.removeClass('owl-carousel');
		}
		$('.owl-carousel').owlCarousel({
			margin: 8,
			loop: true,
			nav: true,
			dots: false,
			lazyLoad: true,
			navText: ["<img src='./assets/img/btn_arrow_l.png'></img>", "<img src='./assets/img/btn_arrow_r.png'></img>"],
			responsive: {
				0: {
					items: 1
				},
				992: {
					items: 4
				}
			}
			// center: true,
		});
	};
});
app.filter('trusted', ['$sce', function($sce) {
	return function(url) {
		return $sce.trustAsResourceUrl(url);
	};
}]);