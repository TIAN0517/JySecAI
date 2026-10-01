(function () {
	angular.module('locationConfigModule', [])
		// dev
	  // .value("locationIP","http://localhost:8080/")
	  // .value("serviceName","LongtermCareService")
	  // .value("backendName","LongtermCareBackend");

	
		// test
	   // .value("locationIP","http://localhost:8080/")
//	   .value("serviceName","LongtermCareService")
//	   .value("backendName","LongtermCareBackend");
	
	// test
//	   .value("locationIP","http://35.229.209.191/")
//		.value("locationIP","https://www.sctw.app/")
//	   .value("serviceName","LongtermCareService")
//	   .value("backendName","LongtermCareBackend");
	
	// 慈濟正式機
	   .value("locationIP","https://ltc.tzuchi.org.tw/")
	   .value("serviceName","LongtermCareService")
	   .value("backendName","LongtermCareBackend");

})();