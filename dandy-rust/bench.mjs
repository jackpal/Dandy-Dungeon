import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const distDir = './dist';
const files = fs.readdirSync(distDir);
const jsFile = files.find(f => f.endsWith('.js'));
const wasmFile = files.find(f => f.endsWith('.wasm'));

if (!jsFile || !wasmFile) {
    console.error("Could not find js or wasm file in dist/");
    process.exit(1);
}

const wasmBytes = fs.readFileSync(path.join(distDir, wasmFile));
const wasmModule = await WebAssembly.compile(wasmBytes);

// Dynamic import the JS glue
const glue = await import(path.resolve(distDir, jsFile));
const wasm = await glue.default({ module_or_path: wasmModule });

const { DandyApp, PlayerAction } = glue;
const app = new DandyApp();

// Warm up
for (let i = 0; i < 50; i++) {
    app.tick();
}

const WARMUP_FRAMES = 100;
const BENCH_FRAMES = 5000;

// Benchmark 1: Pure Wasm tick() (physics + camera + framebuffer software blitting + stats update)
console.log(`Running pure tick() benchmark (${BENCH_FRAMES} frames)...`);
const startTick = performance.now();
for (let i = 0; i < BENCH_FRAMES; i++) {
    if (i % 10 === 0) {
        // simulate some movement input
        app.set_action(0, PlayerAction.Right, true);
    } else if (i % 10 === 5) {
        app.set_action(0, PlayerAction.Right, false);
    }
    app.tick();
}
const endTick = performance.now();
const totalTickMs = endTick - startTick;
const avgTickUs = (totalTickMs / BENCH_FRAMES) * 1000;
const fpsThroughput = (BENCH_FRAMES / (totalTickMs / 1000));

console.log(`Results:`);
console.log(`  Total time for ${BENCH_FRAMES} frames: ${totalTickMs.toFixed(2)} ms`);
console.log(`  Average time per frame: ${avgTickUs.toFixed(2)} µs`);
console.log(`  Throughput: ${fpsThroughput.toFixed(0)} FPS`);

// Benchmark 2: Boundary extraction (Uncached vs Cached views)
console.log(`\nBenchmarking JS boundary extraction over 5000 frames...`);

// Uncached (baseline): creates new TypedArrays every frame
const startUncached = performance.now();
for (let i = 0; i < BENCH_FRAMES; i++) {
    const fbPtr = app.get_framebuffer_ptr();
    const fbSize = app.get_framebuffer_size();
    const fbBytes = new Uint8ClampedArray(wasm.memory.buffer, fbPtr, fbSize);
    
    const statsPtr = app.get_stats_ptr();
    const statsLen = app.get_stats_len();
    const statsArray = new Int32Array(wasm.memory.buffer, statsPtr, statsLen);
    
    // access some data
    const p1Score = statsArray[3];
    const px0 = fbBytes[0];
}
const endUncached = performance.now();
const uncachedTimeMs = endUncached - startUncached;

// Cached (Transport Ladder G3): caches typed array views keyed by buffer identity
let cachedFbPtr = 0, cachedFbSize = 0, cachedMemoryBuffer = null, cachedFbBytes = null;
let cachedStatsPtr = 0, cachedStatsLen = 0, cachedStatsMemory = null, cachedStatsArray = null;

const startCached = performance.now();
for (let i = 0; i < BENCH_FRAMES; i++) {
    const fbPtr = app.get_framebuffer_ptr();
    const fbSize = app.get_framebuffer_size();
    if (fbPtr !== cachedFbPtr || fbSize !== cachedFbSize || wasm.memory.buffer !== cachedMemoryBuffer) {
        cachedFbPtr = fbPtr;
        cachedFbSize = fbSize;
        cachedMemoryBuffer = wasm.memory.buffer;
        cachedFbBytes = new Uint8ClampedArray(wasm.memory.buffer, fbPtr, fbSize);
    }
    
    const statsPtr = app.get_stats_ptr();
    const statsLen = app.get_stats_len();
    if (statsPtr !== cachedStatsPtr || statsLen !== cachedStatsLen || wasm.memory.buffer !== cachedStatsMemory) {
        cachedStatsPtr = statsPtr;
        cachedStatsLen = statsLen;
        cachedStatsMemory = wasm.memory.buffer;
        cachedStatsArray = new Int32Array(wasm.memory.buffer, statsPtr, statsLen);
    }
    
    // access some data
    const p1Score = cachedStatsArray[3];
    const px0 = cachedFbBytes[0];
}
const endCached = performance.now();
const cachedTimeMs = endCached - startCached;

console.log(`  Uncached boundary time (5000 frames): ${uncachedTimeMs.toFixed(2)} ms (${((uncachedTimeMs/BENCH_FRAMES)*1000).toFixed(2)} µs/frame)`);
console.log(`  Cached boundary time (5000 frames):   ${cachedTimeMs.toFixed(2)} ms (${((cachedTimeMs/BENCH_FRAMES)*1000).toFixed(2)} µs/frame)`);
console.log(`  Boundary speedup: ${(uncachedTimeMs / cachedTimeMs).toFixed(2)}x`);
