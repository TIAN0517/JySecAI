#!/usr/bin/env node
// Socket.IO 完整客户端探测 4000 EPCRServer
const { io } = require('socket.io-client');

const URL = 'https://epcr.tpf.gov.tw:4000';

console.log('=== Starting socket.io-client probe ===');
console.log(`Target: ${URL}`);

const socket = io(URL, {
  transports: ['polling'],
  reconnection: true,
  reconnectionAttempts: 3,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 2000,
  timeout: 10000,
  forceNew: true,
  autoConnect: true,
});

let connectCount = 0;
let disconnectCount = 0;
let allEvents = [];

socket.on('connect', () => {
  connectCount++;
  console.log(`[CONNECT #${connectCount}] sid=${socket.id} transport=${socket.io.engine.transport.name}`);
  allEvents.push({type:'connect', sid: socket.id, t: Date.now()});

  // Try subscribe
  console.log('Sending client.subscribe (roomName=dispatch)');
  socket.emit('client.subscribe', {roomName: 'dispatch'}, (ack) => {
    console.log(`[ACK subscribe] ${JSON.stringify(ack)}`);
    allEvents.push({type:'subscribe_ack', ack, t: Date.now()});
  });

  // Try unsubscribe
  setTimeout(() => {
    console.log('Sending client.unsubscribe');
    socket.emit('client.unsubscribe', {roomName: 'dispatch'}, (ack) => {
      console.log(`[ACK unsubscribe] ${JSON.stringify(ack)}`);
    });
  }, 1500);

  // Try generic events
  setTimeout(() => {
    console.log('Sending ping (generic)');
    socket.emit('ping', {}, (ack) => {
      console.log(`[ACK ping] ${JSON.stringify(ack)}`);
    });
  }, 2500);

  setTimeout(() => {
    console.log('Sending hello (generic)');
    socket.emit('hello', {msg:'hello'}, (ack) => {
      console.log(`[ACK hello] ${JSON.stringify(ack)}`);
    });
  }, 3000);
});

socket.on('disconnect', (reason, details) => {
  disconnectCount++;
  console.log(`[DISCONNECT #${disconnectCount}] reason=${reason} details=${JSON.stringify(details||{})}`);
  allEvents.push({type:'disconnect', reason, t: Date.now()});
});

socket.on('connect_error', (err) => {
  console.log(`[CONNECT_ERROR] ${err.message}`);
  allEvents.push({type:'connect_error', msg: err.message, t: Date.now()});
});

socket.on('reconnect_attempt', (n) => {
  console.log(`[RECONNECT_ATTEMPT #${n}]`);
});

socket.on('reconnect', (n) => {
  console.log(`[RECONNECT #${n}]`);
});

socket.onAny((event, ...args) => {
  console.log(`[EVENT ${event}] ${JSON.stringify(args).slice(0,200)}`);
  allEvents.push({type:'event', name:event, args: args.map(a => typeof a === 'string' ? a.slice(0,100) : a).slice(0,3), t: Date.now()});
});

// Keep alive
setTimeout(() => {
  console.log('=== Summary ===');
  console.log(`Total connects: ${connectCount}`);
  console.log(`Total disconnects: ${disconnectCount}`);
  console.log(`Total events: ${allEvents.length}`);
  console.log('All events:');
  console.log(JSON.stringify(allEvents, null, 2));
  process.exit(0);
}, 25000);
