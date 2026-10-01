const {io} = require('socket.io-client');
const opts = {transports:['polling','websocket'], reconnection:false, timeout:8000, extraHeaders:{}};
const s = io('https://epcr.tpf.gov.tw:4000/', {transports:['websocket'], reconnection:false, forceNew:true});
let done=false;
s.on('connect', ()=>{console.log('CONNECTED', s.id);
  // 尝试订阅业务房间
  s.emit('client.subscribe','caseList', (ack)=>{console.log('ack caseList:', JSON.stringify(ack).slice(0,150));});
  s.emit('join','caseList');
  s.emit('subscribe','caseList');
});
s.on('message',(d)=>console.log('MSG',JSON.stringify(d).slice(0,150)));
['caseList','dispatch','hospital','branch','vitalsign','message','notification','data','update'].forEach(ev=>{
  s.on(ev,(d)=>console.log('EV:'+ev, JSON.stringify(d).slice(0,200)));
});
s.on('connect_error',(e)=>{console.log('ERR',e.message); done=true;});
setTimeout(()=>{console.log('TIMEOUT-DONE'); s.close(); process.exit(0);},9000);
