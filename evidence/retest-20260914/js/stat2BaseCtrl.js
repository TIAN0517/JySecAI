app.controller('statBase2Ctrl', function ($scope, $state, NgTableParams, $http, $timeout, $q) {

  function getYScale(yDomain, yRange) {
    return d3.scale.linear().range(yRange).domain(yDomain);
  }

  function getYDomainFromData(data) {
    if (data.length > 0) {
      var min = _.minBy(data, 'number')
      var max = _.maxBy(data, 'number')
      return [min.number, max.number];
    } else {
      return [0, 0];
    }
  }

  function removeLine(diagramId, id) {
    var line = d3.select('#' + diagramId).select('svg').select('#' + id);
    line.remove();
  }

  function addLine(diagramId, id, yValue, yDomain, options, color) {
    var diagram = d3.select('#' + diagramId).select('svg');
    var diagramWidth = diagram.node().getBBox().width;
    // var yDomain = getYDomainFromData(data);
    var yScale = getYScale(yDomain, [options.chart.height - options.chart.margin.top - options.chart.margin.bottom, 0]);
    var covertedY = yScale(yValue) + options.chart.margin.top;
    diagram.append('line')
      .attr('id', id)
      .attr('x1', options.chart.margin.left)
      .attr('x2', diagramWidth)
      .attr('y1', covertedY)
      .attr('y2', covertedY)
      .style('stroke', color)
      .style('stroke-width', 3)
      .style('stroke-dasharray', '2')
  }

  function setupLine(diagramId, id, yValue, yDomain, options, color) {
    removeLine(diagramId, id);
    addLine(diagramId, id, yValue, yDomain, options, color);
  }

  var largestDataIdx = 0;

  function showStat(search) {
    $scope.fields = [];
    $scope.tableData = [];
    $scope.diagramData = [];
    $scope.tableClass = null;
    var deferred = $q.defer();
    $scope.anyPageBusy = deferred.promise;
    return $scope.getStat(search)
      .then(function (results) {
        $scope.fields = results.fields;
        $scope.dataFields = results.dataFields ? results.dataFields : results.fields[results.fields.length - 1];
        $scope.tableData = results.data;
        $scope.tableClass = results.tableClass;
        $scope.diagramEnable = !(results.diagramDisable);
        if ($scope.diagramEnable && results.diagram) {
          $scope.diagramOptions = results.diagram.options;
          $scope.diagramData = results.diagram.data;
        } // if
        else {
          $scope.diagramEnable = false;
          $scope.diagramOptions = null;
          $scope.diagramData = null;
        } // else

        deferred.resolve();
      })
      .catch(function (error) {
        deferred.resolve();
        console.log(error);
        // EPCRServices.failAlert('錯誤', '取得統計結果時發生錯誤');
        alert('取得統計結果時發生錯誤');
      });
  }

  if (_.isNil($scope.base)) {
    $scope.base = {};
  }
  $scope.base.showStat = showStat;

});


app.config(function ($stateProvider) {
  $stateProvider
    .state('statBase2', {
      url: '/statBase2',
      abstract: true,
      template: '' +
        '<div>' +
        '  <div ng-include="\'templates/menu/statMenuTop.html\'"></div>' +
        '  <ui-view></ui-view>' +
        '</div>',
      controller: function () { },
      data: {
        requiresLogin: true
      }
    })
    .state('statBase2.default', {
      url: '/default',
      template: '',
      controller: 'epcr106StatBaseCtrl',
      data: {
        requiresLogin: true
      }
    })
});
