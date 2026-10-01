CONTROLLERS.controller('HospitalCtrl', function($q, $modal, $scope, $state,
 NgTableParams, $http, $element, EPCRServices, $timeout) {

 var hospitalEditModal = $modal({
   scope: $scope,
   templateUrl: 'templates/modal/hospitalEdit.html',
   animation: 'no-animation',
   placement: 'center',
   backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
   show: false,
   onHide: refreshList
 });

 var getHospital = function(hospitalUuids){
   return $http.get('/Hospitals', {
     params: {
       uuid: { $notIn: hospitalUuids },
       sort: 'name',
       disabled: false
     },
     paramSerializer: '$httpParamSerializerJQLike'
   })
   .then(function(response){
     return response.data
   })
 }
 $scope.showEditModal = function(idx){
   var branch;
   $http.get('/Branches', {
     params: {
       id: responseList[idx]['id'],
       disabled: false
     },
     paramSerializer: '$httpParamSerializerJQLike'
   })
   .then(function(response){
     if(response.data.length > 0){
       branch = response.data[0];
       $scope.selectedBranch = branch;

       var hospitalUuids = []
       angular.forEach(branch.Hospitals, function(data){
         hospitalUuids.push(data.uuid)
       })


       return getHospital(hospitalUuids)
       .then(function(theHospitals){
         $scope.dragAndDropList = {
           selected: null,
           lists: {
             "後送醫院清單": branch.Hospitals,
             "醫院清單": theHospitals
           }
         }
         hospitalEditModal.$promise.then(hospitalEditModal.show)
       })
     }else{
       EPCRServices.failAlert('錯誤！', '分隊已被刪除！', null);
       refreshList()
     }
   })
 }
 $scope.addToHospital = function(){
   var hospitalUuids = [];
   angular.forEach($scope.selectedBranch.Hospitals, function(data){
     hospitalUuids.push(data.uuid);
   })

   var deferred = $q.defer()
   $scope.myPromise = deferred.promise

   $http.post('/Branches/addToHospital', {
     id: $scope.selectedBranch.id,
     hospitalUuids: hospitalUuids
   })
   .then(function(response){
     deferred.resolve()
     hospitalEditModal.$promise.then(hospitalEditModal.hide)
   })
   .catch(function(err){
     deferred.resolve()
     console.log('addToHospital err=', err)
   })
 }

 $scope.selectedBranchId = function(id){
   searchParams['id'] = id;
   $scope.tableParams = tableInit();
 }
 $scope.refreshList = function(){
   searchParams = {}
   $scope.search = {}
   $scope.tableParams = tableInit();
 }


 var searchParams = {}
 var responseList = []
 function tableInit(){
   return new NgTableParams({
     page: 1, // show first page
     count: 10, // count per page,
     sorting: {}
   }, {
     filterDelay: 300,
     getData: function(params){
       var deferred = $q.defer();
       $scope.anyPageBusy = deferred.promise;
       var url = params.url();
       var limit = url.count,
           skip = url.count * (url.page - 1);
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

       var conditions = {
         time: new Date().getTime(),
         sort: sortString,
         count: limit,
         offset: skip,
         disabled: false
       }

       if(!_.isEmpty(searchParams)){
         for(var key in searchParams){
           conditions[key] = searchParams[key]
         }
       }

       return $http.get('/Branches', {
         params: conditions,
         // paramSerializer: '$httpParamSerializerJQLike'
       })
       .then(function(response){
         var range = contentRange.parse(response.headers('Content-Range'));
         var count = range.length;
         params.total(count);

         responseList = response.data;

         deferred.resolve()
         return response.data
       })
       .catch(function(err){
         deferred.resolve();
         console.log('tableInit err =', err)
       })

     }
   })
 }

 function dataInit(){
   return $http.get('/Branches')
   .then(function(response){
     $scope.branchList = response.data;
   })
 }
 function refreshList(){
   $scope.tableParams.reload()
 }

 dataInit()
 $scope.tableParams = tableInit();

});
