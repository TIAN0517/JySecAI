#!/usr/bin/env node
// 用伪造 JWT token 尝试连接 4000 Socket.IO
const { io } = require('socket.io-client');

const URL = 'https://epcr.tpf.gov.tw:4000';

// 伪造一个 JWT (无签名校验，参考 4000 AuthService.js jwtHelper.decodeToken)
const fakeJwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6IkFETUlOIiwicGVybWlzc2lvbnMiOlsxLDJdLCJleHAiOjQ4OTg5NTYwMDB9.fake';

console.log(`Target: ${URL}`);
console.log(`Fake JWT: ${fakeJwt}`);

const socket = io(URL, {
  transports: ['polling'],
  reconnection: false,
  auth: { token: fakeJwt },
  extraHeaders: { 'Authorization': `Bearer ${fakeJwt}` },
  forceNew: true,
  autoConnect: true,
  timeout: 10000,
});

socket.on('connect', () => {
  console.log(`[CONNECT] sid=${socket.id}`);
});

socket.on('connect_error', (err) => {
  console.log(`[CONNECT_ERROR] ${err.message}`);
});

socket.on('disconnect', (reason) => {
  console.log(`[DISCONNECT] reason=${reason}`);
});

setTimeout(() => process.exit(0), 15000);
