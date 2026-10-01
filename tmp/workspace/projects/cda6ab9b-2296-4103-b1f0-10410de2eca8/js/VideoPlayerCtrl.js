CONTROLLERS.controller('VideoPlayerCtrl', function ($q, $scope, $rootScope) {
    console.log('VIDEO PLAYER CTRL');

    $scope.init = init;
    $scope.player_load = player_load;
    var player;
    // ========================================================================
    function init() {
        setTimeout(player_load);
    } // init()

    function player_load() {
        console.log('isSupported: ' + mpegts.isSupported());

        var i;
        var mediaDataSource = {
            type: $scope.type,
            isLive: $scope.isLive,
            url: $scope.url
        }
        console.log('MediaDataSource', mediaDataSource);
        player_load_mds(mediaDataSource);
    }
    function player_load_mds(mediaDataSource) {
        var element = document.getElementById($scope.id);
        if (typeof player !== "undefined") {
            if (player != null) {
                player.unload();
                player.detachMediaElement();
                player.destroy();
                player = null;
            }
        }
        player = mpegts.createPlayer(mediaDataSource, {
            enableWorker: true,
            lazyLoadMaxDuration: 60,
            seekType: 'range',
        });
        player.attachMediaElement(element);
        player.load();
        player.play();
    }
});




app.directive('videoPlayer', function () {
    return {
        replace: true,
        restrict: 'E',
        scope: {
            id: '=',
            url: '=',
            type: '=',
            isLive: '='
        },
        templateUrl: '/templates/videoPlayer.html',
        link: function (scope, element, attrs, ngModel) {
            scope.init();
        },
        controller: 'VideoPlayerCtrl'
    };
});