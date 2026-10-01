SERVICES.factory('SocketIoService', function($http, $state, $q) {

  var socket;
  var promise = init();
  var roomMap = {};

  function getConfig(){
    return $http.get('/config')
    .then(function(response){
      return response.data;
    });
  }

  function init(){
    return getConfig()
    .then(function(config){
      var serverUrl = config.SELF_URL;
      socket = io(serverUrl);
      socket.on('connect', function(){
        console.log('SocketIoService: connect');
        // rejoin all rooms
        for(var roomName in roomMap){
          joinRoom(roomName);
        }

      })
      socket.on('disconnect', function(){
        console.log('SocketIoService: disconnect');
      })

    });
  }

  function getSocket(){
    return promise.then(function(){
      return socket;
    });
  }

  function sendMessage(type, msg){
    return promise.then(function(){
      socket.emit(type, msg);
    });
  }

  function joinRoom(roomName) {
    return promise.then(function(){
      var deferred = $q.defer();
      socket.emit('client.subscribe', {
          roomName: roomName
      }, function(response) {
        console.log('@@@ room SUBSCRIBED. @@@')
        console.log('Result =', response.result, ', join roomName =', roomName)
        roomMap[roomName] = true;
        if(response.result){
          deferred.resolve()
        }else{
          deferred.reject(new Error('Failed to subscribe socket.io room.'));
        }
      });
      return deferred.promise;
    });
  }

  function leaveRoom(roomName) {
    return promise.then(function(){
      var deferred = $q.defer();
      socket.emit('client.unsubscribe', {
          roomName: roomName
      }, function(response) {
        console.log('@@@ room SUBSCRIBED. @@@')
        console.log('Result =', response.result, ', join roomName =', roomName)
        delete roomMap[roomName];
        if(response.result){
          deferred.resolve()
        }else{
          deferred.reject(new Error('Failed to unsubscribe socket.io room.'));
        }
      });
      return deferred.promise;
    });
  }

  function leaveAll(){
    for(var roomName in roomMap){
      leaveRoom(roomName);
    }
  }


  return {
    sendMessage: sendMessage,
    getSocket: getSocket,
    joinRoom: joinRoom,
    leaveRoom: leaveRoom,
    leaveAll: leaveAll
  }
})
