CONTROLLERS.controller('ResourceManagementCtrl', function($q, $modal, $scope, $state,
 NgTableParams, $http, $element, EPCRServices) {

// TODO: 接收socket.io訊息，更新ng-map上面的marker

 var exampleModal = $modal({
   scope: $scope,
   templateUrl: 'templates/modal/exampleModal.html',
   animation: 'no-animation',
   placement: 'center',
   backdrop: 'static', // 不能點擊背景就關閉 Modal 視窗
   show: false,
  //  onHide: refreshList
 });

var getCaseSampleSize=function(){
  var dateBegin = moment().subtract(24, 'hours').toDate()
  return $http.get('/CaseRecords/CaseSampleSize', {
           params: {
            isSimulation: false,
            // dispatchedAT:{
            //   $gte: dateBegin
            // },
            // returnedBaseAt:
            // {$lt: new Date()}
          },
    paramSerializer: '$httpParamSerializerJQLike'
  })
  .then(function(response){
    return response.data;
  })
  .catch(function(err){
    console.log('getCaseSampleSize err =', err.stack)
  })
}

var dataInit = function(){
  return getCaseSampleSize()
  .then(function(response){
    console.log('dataInit',response)
    if(response.length==0){
      return;
    }

    $scope.CaseSampleSize = response.CaseSampleSize
    $scope.AvgReactionTime = response.AvgReactionTime
    $scope.AvgWorkTime = response.duWorkTime

      return $http.get('/Branches/listBranchWithCaseRecordAndAmbulance', {
               paramSerializer: '$httpParamSerializerJQLike'
             })
        })
  .then(function(response){
    // 車輛使用率
    $scope.BranchSum = response.data.length
    var AmbulanceSum = 0
    var AmbulanceWorking = 0
    var UseAmbulance = 0
    for(var key in response.data){
      AmbulanceSum += response.data[key].Ambulancesum
      AmbulanceWorking+=response.data[key].DispatchRecordsum;

    }

    UseAmbulance =AmbulanceWorking / AmbulanceSum * 100
    $scope.AmbulanceSum =AmbulanceSum
    $scope.AmbulanceWorking = AmbulanceWorking
    $scope.UseAmbulance = UseAmbulance.toFixed(2) +'%'

    $scope.Ambulancedata = [
      {
          key: "已使用",
          y: UseAmbulance
      },
      {
          key: "未使用",
          y: 100-UseAmbulance
      }
    ];

    return BranchDispatchRecordsum()
  })
  .then(function(response){
    console.log('BranchDispatchRecordsum',response.length)
    //分隊使用率
    var BranchWorking = 0
    var UseBranch = 0

    BranchWorking=response.length
    UseBranch = BranchWorking / $scope.BranchSum * 100
    $scope.BranchWorking =BranchWorking
    $scope.UseBranch = UseBranch.toFixed(2) +'%'
        $scope.Branchdata = [
      {
          key: "已使用",
          y: UseBranch
      },
      {
          key: "未使用",
          y: 100-UseBranch
      }
    ];

     return AmbulanceAvailability()
  })
  .then(function(response){
    $scope.Availability = response.Availability +'%'
    $scope.PrCarSUseSum = response.PrCarSUseSum
    $scope.PrCarSum = response.PrCarSum
    var StopUse = 100 - response.Availability
    $scope.AmbulanceAvailabilitydata = [
      {
          key: "無法使用",
          y: StopUse.toFixed(2)
      },
      {
          key: "可使用",
          y: response.Availability
      }
    ];

  })
  .catch(function(err){
    console.log('dataInit err=',err)
  })
}

dataInit();



 $scope.Branchoptions = {
            chart: {
                type: 'pieChart',
                height: 200,
                x: function(d){return d.key;},
                y: function(d){return d.y;},
                color:['#77D1F6', '#27255F'],
                showLabels: true,
                duration: 200,
                labelThreshold: 0.01,
                labelSunbeamLayout: true,
                showLegend: false, // to hide legend
                showControls: false // to hide controls
            }
        };

$scope.Ambulanceoptions = {
            chart: {
                type: 'pieChart',
                height: 200,
                x: function(d){return d.key;},
                y: function(d){return d.y;},
                color:['#FFF33F', '#ED5603'],
                showLabels: true,
                duration: 200,
                labelThreshold: 0.01,
                labelSunbeamLayout: true,
                showLegend: false, // to hide legend
                showControls: false // to hide controls
            }
        };

  $scope.AmbulanceAvailabilityOptions = {
            chart: {
                type: 'pieChart',
                height: 200,
                x: function(d){return d.key;},
                y: function(d){return d.y;},
                color:['#FF6666', '#CC0000'],
                showLabels: true,
                duration: 200,
                labelThreshold: 0.01,
                labelSunbeamLayout: true,
                showLegend: false, // to hide legend
                showControls: false // to hide controls
            }
        };


 $scope.checkboxes = {
   checked: false,
   items: {}
 }
 var defaultSorting = {};
 var responseList = []

//執行中車輛
 function tableInit(){
   return new NgTableParams({
     sorting: defaultSorting
   }, {
    pages: [],
    counts: [],
     filterDelay: 300,
     getData: function(params){
       var deferred = $q.defer();
       $scope.anyPageBusy = deferred.promise;
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

        var dateBegin = moment().subtract(24, 'hours').toDate()
        return EPCRServices.getDispatchRecords(dateBegin)
       .then(function(response){

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

  $scope.tableParams = tableInit();

//各區域分隊車輛執行量
function tableExecuteParams(){
   return new NgTableParams({
     sorting: defaultSorting
   }, {
    pages: [],
    counts: [],
     filterDelay: 300,
     getData: function(params){
       var deferred = $q.defer();
       $scope.anyPageBusy = deferred.promise;
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

       return EPCRServices.getListBranchWithCaseRecordAndAmbulance()
       .then(function(response){
         deferred.resolve()
         return response.data
       })
       .catch(function(err){
         deferred.resolve();
         console.log('tableExecuteParams err =', err)
       })

     }
   })
 }

  $scope.tableExecuteParams = tableExecuteParams();

//派遣車輛座標
var DispatchDevicesCoords = function(){

return $http.get('/DispatchRecords/listDispatchDevicesCoords', {
         paramSerializer: '$httpParamSerializerJQLike'
       })
       .then(function(response){
        var carPositionMaps=[]
        var currentlatitude
        var currentlongitude
        var Coords
        var AmbulanceCode
        // console.log('DispatchRecords',response.data)
        for (var idx in response.data){
         if(response.data[idx].Ambulance.Devices.length>0){
           currentlatitude = response.data[idx].Ambulance.Devices[0].currentlatitude
           currentlongitude = response.data[idx].Ambulance.Devices[0].currentlongitude
           Coords = currentlatitude+','+currentlongitude
         }

         AmbulanceCode = response.data[idx].Ambulance.code

         carPositionMaps.push({'position':Coords,'lable':AmbulanceCode});
        }

        $scope.carPositionMaps = carPositionMaps
        return carPositionMaps
       })
       .catch(function(err){
         console.log('tableExecuteParams err =', err.stack)
       })

}
DispatchDevicesCoords()

//分隊使用率
var BranchDispatchRecordsum = function(){

  return $http.get('/DispatchRecords/branchDispatchRecordSum', {
       paramSerializer: '$httpParamSerializerJQLike'
     })
    .then(function(response){
      return response.data
    })
}


//計算妥善率
var  AmbulanceAvailability = function(){
  return $http.get('/Ambulances/calculateAmbulanceAvailability', {
         paramSerializer: '$httpParamSerializerJQLike'
       })
      .then(function(response){
        return response.data
      })

}

 // watch for check all checkbox
 $scope.$watch(function() {
     return $scope.checkboxes.checked;
 }, function(value) {
     angular.forEach(responseList, function(item) {
         $scope.checkboxes.items[item.id] = value;
     });
 });
 // watch for data checkboxes
 $scope.$watch(function() {
     return $scope.checkboxes.items;
 }, function(values) {
     var checked = 0,
         unchecked = 0,
         total = responseList.length;
     angular.forEach(responseList, function(item) {
         checked += ($scope.checkboxes.items[item.id]) || 0;
         unchecked += (!$scope.checkboxes.items[item.id]) || 0;
     });
     if (total > 0 && ((unchecked == 0) || (checked == 0))) {
         console.log('checked=', checked, 'total=', total);
         $scope.checkboxes.checked = (checked == total);
     }
     // grayed checkbox
     angular.element($element[0].getElementsByClassName("select-all")).prop("indeterminate", (checked != 0 && unchecked != 0));
 }, true);

});
