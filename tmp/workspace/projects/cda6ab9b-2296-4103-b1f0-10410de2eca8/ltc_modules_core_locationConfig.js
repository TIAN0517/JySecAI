/**
 * ※ 注意: 此檔需置於appConfig.js前或有做(var app = angular.module(...))之前
 * 
 */
(function () {
	angular
		.module('localConfig', [])
		.service("urlSetting", function () {
			//本地端
			// this.localUrl = 'http://localhost:8080/';
			//Sc測試機
//			this.localUrl = 'http://35.229.209.191/';
//			this.localUrl = 'https://www.sctw.app/';
			//慈濟正式機
           this.localUrl = 'https://ltc.tzuchi.org.tw/';
           //  this.frontend = this.localUrl;
			this.serviceUrl = this.localUrl + 'LongtermCareService/';
			this.backendUrl = this.localUrl + 'LongtermCareBackend/';
//			this.imageLoadUrl = this.serviceUrl + 'api_backend/imageFile';
		});

})();

