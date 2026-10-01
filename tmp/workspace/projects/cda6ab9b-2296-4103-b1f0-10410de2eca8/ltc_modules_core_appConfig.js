'use strict';

var rootUrl = '';
var mainUrl = '';

var app = angular.module('app',
	['ui.router', 'ui.router.state.events', 'ngRoute', 'ngCookies', 'ui.bootstrap', 'ngSanitize', 'TreeWidget', 'toggle-switch', 'LocalStorageModule', 'localConfig']);

app.config(['$stateProvider', '$urlRouterProvider', '$locationProvider', function ($stateProvider, $urlRouterProvider, $locationProvider) {
	$locationProvider.hashPrefix('');

	$urlRouterProvider.otherwise(function ($injector, Ng1LocationServices) {
		var absUrl = Ng1LocationServices.$location.absUrl();
		var codeIndex = absUrl.indexOf('?code=');
		var stateIndex = absUrl.indexOf('&state=');
		if (codeIndex != -1 && stateIndex != -1 && absUrl.indexOf('#') == -1) {
			var parameter = absUrl.substring(codeIndex);
			var newAbsUrl = absUrl.replace('/' + parameter, '') + '/#/loginHandler' + parameter;
			window.open(newAbsUrl, '_self');
		}
		return '/home';
	});

	$stateProvider.state('404', {
		url: '/page-not-found',
		views: {
			"content": {
				templateUrl: 'modules/vc/home/view/page404.html?v=20210429'
			}
		}
	});

	$stateProvider.state('login', {
		url: '/login',
		views: {
			"content": {
				templateUrl: 'modules/vc/login/view/login.html?v=20210429',
				controller: 'loginController'
			}
		}
	}).state('forget', {
		url: '/forget',
		views: {
			"content": {
				templateUrl: 'modules/vc/login/view/forget.html?v=20210429',
				controller: 'forgetController'
			}
		}
	}).state('register', {
		url: '/register',
		views: {
			"content": {
				templateUrl: 'modules/vc/login/view/register.html?v=20210429',
				controller: 'registerController'
			}
		}
	}).state('loginHandler', {
		url: '/loginHandler?:code:state',
		views: {
			"content": {
				templateUrl: 'modules/vc/login/view/loginLoading.html?v=20210429',
				controller: 'loginHandlerController'
			}
		}
	});

	$stateProvider.state('home', {
		url: '/home',
		views: {
			"content": {
				templateUrl: 'modules/vc/home/view/home.html?v=20210429',
				controller: 'homeController'
			}
		}
	});

	$stateProvider.state('about', {
		url: '/about',
		views: {
			"content": {
				templateUrl: 'modules/vc/home/view/about.html?v=20210429',
				controller: 'aboutController'
			}
		}
	}).state('news', {
		url: '/news',
		views: {
			'content': {
				templateUrl: 'modules/vc/news/view/news.html?v=20210429'
			},
			'news@news': {
				templateUrl: 'modules/vc/news/view/lastnews.html?v=20210429',
				controller: 'lastnewsController'
			},
		},
	}).state('course', {
		url: '/course',
		views: {
			'content': {
				templateUrl: 'modules/vc/news/view/news.html?v=20210429'
			},
			'news@course': {
				templateUrl: 'modules/vc/news/view/course.html?v=20210429',
				controller: 'courseController'
			}
		},
		params: {
			id: null,
		},
		reload: true

	}).state('information', {
		url: '/information',
		views: {
			'content': {
				templateUrl: 'modules/vc/news/view/news.html?v=20210429'
			},
			'news@information': {
				templateUrl: 'modules/vc/news/view/information.html?v=20210429',
				controller: 'informationController'
			}
		}
	}).state('post', {
		url: '/post',
		views: {
			'content': {
				templateUrl: 'modules/vc/news/view/news.html?v=20210429'
			},
			'news@post': {
				templateUrl: 'modules/vc/news/view/post.html?v=20210429',
				controller: 'postController'
			}
		}

	});
	$stateProvider.state('serviceItem', {
		url: '/serviceItem',
		views: {
			"content": {
				templateUrl: 'modules/vc/service/view/serviceItem.html?v=20210429',
				controller: 'serviceItemController'
			}
		}
	});

	$stateProvider.state('story', {
		url: '/story',
		views: {
			"content": {
				templateUrl: 'modules/vc/service/view/story.html?v=20210429',
				controller: 'storyController'
			}
		}
	})

	$stateProvider.state('location', {
		url: '/location',
		views: {
			"content": {
				templateUrl: 'modules/vc/home/view/location.html?v=20210429',
				controller: 'locationController'
			}
		}
	})

	// multiviews
	$stateProvider.state('secondhand', {
		url: '/secondhand',
		views: {
			'content': {
				templateUrl: 'modules/vc/secondhand/view/secondhand.html?v=20210429',
				controller: 'secondhandController'
			},
		}
	});


	$stateProvider.state('activity', {
		url: '/activity',
		views: {
			"content": {
				templateUrl: 'modules/vc/service/view/activity.html?v=20210429',
				controller: 'activityController'
			}
		}
	});
	$stateProvider.state('homeGroup', {
		url: '/homeGroup',
		views: {
			'content': {
				templateUrl: 'modules/vc/join/view/homeGroup.html?v=20210429',
				controller: 'homeGroupController'
			}
		}
	})

	$stateProvider.state('recruit', {
		url: '/recruit',
		views: {
			"content": {
				templateUrl: 'modules/vc/join/view/recruit.html?v=20210429',
				controller: 'recruitController'
			}
		}
	}).state('join', {
		url: '/join',
		views: {
			'content': {
				templateUrl: 'modules/vc/join/view/join.html?v=20210429'
			},
			'join@join': {
				templateUrl: 'modules/vc/join/view/intern.html?v=20210429',
				controller: 'internController'
			},
		},

	}).state('visit', {
		url: '/visit',
		views: {
			'content': {
				templateUrl: 'modules/vc/join/view/join.html?v=20210429'
			},
			'join@visit': {
				templateUrl: 'modules/vc/join/view/visit.html?v=20210429',
				controller: 'visitController'
			}
		}

	}).state('volunteer', {
		url: '/volunteer',
		views: {
			'content': {
				templateUrl: 'modules/vc/join/view/join.html?v=20210429'
			},
			'join@volunteer': {
				templateUrl: 'modules/vc/join/view/volunteer.html?v=20210429',
				controller: 'volunteerController'
			}
		}

	});

	$stateProvider.state('qNa', {
		url: '/qNa',
		views: {
			"content": {
				templateUrl: 'modules/vc/footer/view/qNa.html?v=20210429',
				controller: 'qNaController'
			}
		}
	});
	$stateProvider.state('privacy', {
		url: '/privacy',
		views: {
			"content": {
				templateUrl: 'modules/vc/footer/view/privacy.html?v=20210429',
				controller: 'privacyController'
			}
		}
	});
	$stateProvider.state('link', {
		url: '/link',
		views: {
			"content": {
				templateUrl: 'modules/vc/footer/view/link.html?v=20210429',
				controller: 'linkController'
			}
		}
	});
	$stateProvider.state('serviceRule', {
		url: '/serviceRule',
		views: {
			"content": {
				templateUrl: 'modules/vc/footer/view/serviceRule.html?v=20210429',
				controller: 'serviceRuleController'
			}
		}
	});
	$stateProvider.state('article', {
		url: '/article?:fn:id',
		views: {
			"content": {
				templateUrl: 'modules/vc/home/view/article.html?v=20210429',
				controller: 'articleController'
			}
		},
		reload: true
	});
	$stateProvider.state('coursepage', {
		url: '/coursepage?:id',
		views: {
			'content': {
				templateUrl: 'modules/vc/news/view/coursepage.html?v=20210429',
				controller: 'coursepageController'
			}
		},
	});

	$stateProvider.state('applyCourse', {
		url: '/applyCourse?:courseId',
		views: {
			'content': {
				templateUrl: 'modules/vc/news/view/applyCourse.html?v=20210429',
				controller: 'applyCourseController'
			}
		},
	});

	$stateProvider.state('storypage', {
		url: '/storypage?:id',
		views: {
			'content': {
				templateUrl: 'modules/vc/service/view/storypage.html?v=20210429',
				controller: 'storypageController'
			}
		},
		reload: true

	});

	$stateProvider.state('internpage', {
		url: '/internpage?:fn:id',
		views: {
			'content': {
				templateUrl: 'modules/vc/join/view/internpage.html?v=20210429',
				controller: 'internpageController'
			}
		},
		reload: true
	});
	$stateProvider.state('activitypage', {
		url: '/activitypage?:id',
		views: {
			'content': {
				templateUrl: 'modules/vc/service/view/activitypage.html?v=20210429',
				controller: 'activitypageController'
			}
		},
		reload: true

	});
	$stateProvider.state('navigator', {
		url: '/navigator',
		views: {
			"content": {
				templateUrl: 'modules/vc/home/view/navigator.html?v=20210429',
				controller: 'navigatorController'
			}
		}
	});
	$stateProvider.state('signup', {
		url: '/signup',
		views: {
			"content": {
				templateUrl: 'modules/vc/home/view/signup.html?v=20210429',
				controller: 'signupController'
			}
		}
	});

	$stateProvider.state('userAccountDetail', {
		url: '/userAccountDetail',
		views: {
			"content": {
				templateUrl: 'modules/vc/account/view/userAccountDetail.html?v=20210429',
				controller: 'userAccountDetailController'
			}
		}
	}).state('messageCenter', {
		url: '/messageCenter',
		views: {
			'content': {
				templateUrl: 'modules/vc/account/view/messageCenter.html?v=20210429',
				controller: 'messageCenterController'
			}
		}

	})

	$stateProvider.state('courseRecord', {
		url: '/courseRecord',
		views: {
			'content': {
				templateUrl: 'modules/vc/account/view/courseRecord.html?v=20210429',
				controller: 'courseRecordController'
			}
		}
	}).state('secondhandRecord', {
		url: '/secondhandRecord',
		views: {
			'content': {
				templateUrl: 'modules/vc/account/view/secondhandRecord.html?v=20210429',
				controller: 'secondhandRecordController'
			}
		}

	});

	$stateProvider.state('casemanage', {
		url: '/casemanage',
		views: {
			'content': {
				templateUrl: 'modules/vc/service/view/casemanage.html?v=20210429',
				controller: 'casemanageController'
			}
		}

	});
	$stateProvider.state('homeservice', {
		url: '/homeservice',
		views: {
			'content': {
				templateUrl: 'modules/vc/service/view/homeservice.html?v=20210429',
				controller: 'homeserviceController'
			}
		}

	});
	$stateProvider.state('daytimecare', {
		url: '/daytimecare',
		views: {
			'content': {
				templateUrl: 'modules/vc/service/view/daytimecare.html?v=20210429',
				controller: 'daytimecareController'
			}
		}

	});
	$stateProvider.state('carelocation', {
		url: '/carelocation',
		views: {
			'content': {
				templateUrl: 'modules/vc/service/view/carelocation.html?v=20210429',
				controller: 'carelocationController'
			}
		}

	});

	$stateProvider.state('searchresult', {
		url: '/searchresult',
		views: {
			'content': {
				templateUrl: 'modules/vc/home/view/searchresult.html?v=20210429',
				controller: 'searchresultController'
			}
		},
		params: {
			str: null,
		}
	});

	$stateProvider.state('serviceApplication', {
		url: '/serviceApplication',
		views: {
			'content': {
				templateUrl: 'modules/vc/service/view/serviceApplication.html?v=20210429',
				controller: 'serviceApplicationController'
			}
		},
		reload: true

	});

}]);
