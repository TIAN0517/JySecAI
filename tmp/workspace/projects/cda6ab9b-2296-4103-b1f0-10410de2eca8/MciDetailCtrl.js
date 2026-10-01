CONTROLLERS.controller('MciDetailCtrl', function($q, $modal, $scope, $state,
NgTableParams, $http, $element, EPCRServices, $stateParams,
AuthService) {

 $scope.tabs = [
   {
     title: '案件內容',
     tp: 'templates/tp/mciContent.html'
   },
   {
     title: '大傷數據',
     tp: 'templates/tp/mciStatistics.html'
   }
 ]

 var CaseRecordId = $stateParams.CaseRecordId
 $scope.token = AuthService.getToken();
 $scope.datetime = new Date().getTime();

 function mciTableInit(CaseRecordId){
   return new NgTableParams({
     sorting: { triagedAt: 'desc' }
   }, {
     pages: [],
     counts: [],
     filterDelay: 300,
     getData: function(params){
       var deferred = $q.defer();
       $scope.myPromise = deferred.promise;

       var sortString;
       // 如果使用 epilogue 免費 api sort需要做調整
       // 如果是自費項目，可以直接將 params.sorting() 給 server處理 sort
       // sortString = params.sorting();
       for(var key in params.sorting()){
         if(params.sorting()[key] == 'desc'){
           sortString = '-' + key;
         }else{
           sortString = key;
         }
       }

       return $http.get('/MciPcrs', {
         params: {
           CaseRecordId: CaseRecordId,
           sort: sortString
         },
         paramSerializer: '$httpParamSerializerJQLike'
       })
       .then(function(response){
         $scope.mciSum = response.data.length;
         if(response.data.length > 0){
           $scope.caseRecord = response.data[0].CaseRecord;
         }

         deferred.resolve();
         return response['data'];
       })
       .catch(function(err){
         deferred.resolve();
         EPCRServices.failAlert('錯誤！', '清單取得失敗！', null)
         console.log('mciTableInit err =', err)
       })
     }
   })
 }
 $scope.mciTableParams = mciTableInit(CaseRecordId)

 var MciLevelsMap = {}
 function statisticsInit(){
   return $http.get('/MciLevels')
   .then(function(response){
     MciLevelsMap = _.keyBy(response.data, 'id')

     return $http.get('/MciPcrs/statisticsSex/' + CaseRecordId)
   })
   .then(function(response){
     $scope.statisticsSex = response.data;
     return $http.get('/MciPcrs/statisticsMciLevel/' + CaseRecordId)
   })
   .then(function(response){
     $scope.statisticsMciLevel = angular.copy(MciLevelsMap)
     angular.forEach(response.data, function(data){
       $scope.statisticsMciLevel[data.MciLevel.id]['MciLevelSum'] = data.MciLevelSum
     })

     return $http.get('/MciPcrs/hospital/' + CaseRecordId)
   })
   .then(function(response){
     $scope.statisticsHospital = response.data
   })
 }
 statisticsInit()

});
