app.factory('courseRecordService', function (baseHttp) {
    return {
    	queryCourseApplicationList: function (params, callback) {
            return baseHttp.service('api_backend/queryCourseApplicationList', params, callback);
        }
    }
})
app.controller('courseRecordController', function ($rootScope, $scope, $window, $location, $http, $filter, $state, $modal, courseRecordService, util, $sce) {

	var currentUser = $rootScope.currentUser;
	$scope.courseApplicationList = [];
	
	// 查詢報名紀錄
    let queryCourseApplicationList = function(){
        let param = {
        	'userInfoId': currentUser.usi
        };
        courseRecordService.queryCourseApplicationList(param, function (data, status, headers, config) {
            if (data.result) {
            	$scope.courseApplicationList = data.data;

            	//- 分頁
            	// 分頁元件 必須變數
                $scope.currentPage = 0; // 當前頁 （請求資料）
                $scope.pageSize = 4; // 每頁記錄數 （請求資料）
                $scope.totalCount = 0; // 總記錄數 （回應資料）
                $scope.totalPages = 0; // 總頁數 （根據 總記錄數、每頁記錄數 計算 ）

                //載入上一頁
                $scope.prev = function () {
                    $scope.selectPage($scope.currentPage - 1);
                }
                //載入下一頁
                $scope.next = function () {
                    $scope.selectPage($scope.currentPage + 1);
                }
                //載入指定頁
                $scope.selectPage = function (page) {
                    // page 超出範圍
                    if ($scope.totalPages != 0 && (page < 1 || page > $scope.totalPages)) {
                        return;
                    }
                    // 要在分頁工具條顯示所有頁碼 
                    $scope.pageList = [];
                    // 顯示表格資料 
                    $scope.courseApplication = $scope.courseApplicationList;
                    //先根據總記錄數去計算總頁數
                    $scope.totalCount = $scope.courseApplication.length; //總記錄數
                    $scope.totalPages = Math.ceil($scope.totalCount / $scope.pageSize); //總頁數
                    // 更新當前顯示頁碼 
                    $scope.currentPage = page;
                    //顯示分頁工具條中間碼
                    var begin; // 顯示第一個頁碼
                    var end; // 顯示最後一個頁碼 
                    // 如果每頁顯示10頁,理論上 begin 是當前頁 -5 
                    begin = $scope.currentPage - 2;
                    if (begin < 1) { //begin不能小於1
                        begin = 1;
                    }
                    // 顯示10個頁碼，理論上end 是 begin + 9
                    end = begin + 4;
                    if (end > $scope.totalPages) {
                        //最後一頁不能大於總頁數
                        end = $scope.totalPages;
                    }
                    // 修正begin 的值, 理論上 begin 是 end - 9
                    begin = end - 4;
                    if (begin < 1) { //begin不能小於1
                        begin = 1;
                    }
                    // 將頁碼加入 PageList集合
                    for (var i = begin; i <= end; i++) {
                        $scope.pageList.push(i);
                    }

                }
                //判斷是否是當前頁
                $scope.isActivePage = function (page) {
                    return page === $scope.currentPage;
                }
                // 初始化，選中第一頁
                $scope.selectPage(1);
            	
            } else {
            	alert("課程報名查詢失敗!");
            }
        });
    }
    
    if(currentUser != null ){
        queryCourseApplicationList();
    }else{
    	alert("請先登入!");
    	$state.go("login");
    }
    
    //分頁按鈕
    
    
})
app.filter('startFrom', function () {
    return function (input, start) {
         if (!input || !input.length ) { return ; }
        start = +start; //parse to int   
        return input.slice(start);
    }
})
app.filter('noexist', function () {
    return function (str) {
        if (str == undefined || str == null) {
            str = '此課程已不存在';
            return str
        } else {
            return str
        }
    };
})