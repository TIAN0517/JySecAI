// Existing Chromium via CDP pipe. No package install or public debugging port.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const base = new URL(process.argv[2]);
assert.equal(base.hostname, '127.0.0.1');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'jysec-xss-browser-'));
const chrome = spawn(process.env.XSS_CHROMIUM || '/usr/local/bin/chromium', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--disable-background-networking', '--disable-component-update', '--no-first-run',
  '--no-default-browser-check', '--disable-extensions', '--remote-debugging-pipe',
  '--user-data-dir=' + profile, 'about:blank'
], {stdio:['ignore','ignore','ignore','pipe','pipe']});
let sequence = 0, buffer = '', session;
const pending = new Map();
chrome.stdio[4].on('data', chunk => {
  buffer += chunk.toString();
  let split;
  while ((split=buffer.indexOf('\0'))>=0) {
    const message = JSON.parse(buffer.slice(0,split)); buffer=buffer.slice(split+1);
    if (message.id && pending.has(message.id)) {
      const {resolve,reject,timer} = pending.get(message.id); pending.delete(message.id); clearTimeout(timer);
      message.error ? reject(new Error(message.error.message)) : resolve(message.result);
    }
  }
});
function send(method, params={}, sessionId) {
  return new Promise((resolve,reject) => {
    const id=++sequence;
    const timer=setTimeout(()=>{pending.delete(id);reject(new Error('CDP timeout: '+method));},10000);
    pending.set(id,{resolve,reject,timer});
    chrome.stdio[3].write(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})})+'\0');
  });
}
async function evaluate(expression) {
  const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);
  if (r.exceptionDetails) throw new Error('Browser evaluation failed: '+JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
async function until(expression) {
  for(let i=0;i<100;i++){if(await evaluate(expression))return;await new Promise(r=>setTimeout(r,50));}
  throw new Error('Browser condition timeout');
}
(async()=>{
  try {
    await send('Browser.getVersion');
    const {targetId}=await send('Target.createTarget',{url:'about:blank'});
    session=(await send('Target.attachToTarget',{targetId,flatten:true})).sessionId;
    await send('Runtime.enable',{},session); await send('Page.enable',{},session);
    await send('Page.navigate',{url:new URL('/browser',base).href},session);
    await until("typeof XSS==='object' && typeof XSS.init==='function'");
    await evaluate("window.__initCount=0;const original=XSS.init;XSS.init=function(){window.__initCount++;window.__initPromise=original();return window.__initPromise;};switchPage('xss');window.__initPromise");
    assert.equal(await evaluate('window.__initCount'),1);
    assert.equal(await evaluate("document.querySelectorAll('#xss-payload-list tr').length"),1);
    assert.equal(await evaluate("document.querySelectorAll('#xss-capture-list tr').length"),1);
    await evaluate('XSS.showCapture('+JSON.stringify(process.argv[3])+')');
    assert.equal(await evaluate("document.querySelectorAll('#xss-detail-body img,#xss-detail-body svg,#xss-detail-body script,#xss-payload-list img,#xss-payload-list svg,#xss-payload-list script,#xss-capture-list img').length"),0);
    assert.equal(await evaluate('window.__xss || 0'),0);
    assert.equal(await evaluate("document.querySelector('#xss-detail-body').textContent.includes('jysec_test')"),true);
    assert.equal(await evaluate("document.querySelector('#xss-payload-list').textContent.includes('<img')"),true);
    await evaluate("XSS.closeModal('xss-detail-modal');XSS.openGenerateModal();document.getElementById('xss-generate-name').value='phase1a1-test-browser';document.getElementById('xss-generate-source').value='http://127.0.0.1/test';XSS.generatePayload()");
    assert.equal(await evaluate("document.querySelectorAll('#xss-payload-list tr').length"),2);
    assert.equal(await evaluate("document.getElementById('xss-script-text').value.includes('X-XSS-Token')"),true);
    await evaluate('XSS.showConfig()');
    assert.equal(await evaluate("document.getElementById('xss-config-enabled').disabled"),true);
    // Run only the newly generated synthetic callback inside the loopback fixture.
    await evaluate("document.cookie='jysec_test=1';(0,eval)(document.getElementById('xss-script-text').value);true");
    await new Promise(r=>setTimeout(r,1000)); await evaluate('XSS.loadCaptures()');
    assert.equal(await evaluate("document.querySelectorAll('#xss-capture-list tr').length>=2"),true);
    assert.equal(await evaluate('window.__xss || 0'),0);
    console.log('BROWSER_E2E_PASS: real DOM, authenticated API, generated synthetic callback, rich capture, text-only rendering, config/modal contract');
  } finally {
    await send('Browser.close').catch(()=>{}); chrome.kill('SIGTERM');
    await new Promise(r=>chrome.exitCode!==null?r():chrome.once('exit',r));
    // Only the exact directory returned by mkdtemp in this isolated test.
    fs.rmSync(profile,{recursive:true,force:true});
  }
})().catch(err=>{console.error(err.message);process.exitCode=1;});
