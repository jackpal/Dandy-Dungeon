import fs from 'fs';
import path from 'path';

const distDir = './dist';
const files = fs.readdirSync(distDir);
const jsFile = files.find(f => f.endsWith('.js'));
const wasmFile = files.find(f => f.endsWith('.wasm'));

const wasmBytes = fs.readFileSync(path.join(distDir, wasmFile));
const wasmModule = await WebAssembly.compile(wasmBytes);
const glue = await import(path.resolve(distDir, jsFile));
const wasm = await glue.default({ module_or_path: wasmModule });

const { DandyApp, PlayerAction } = glue;

console.log("=== Interleaved ABBA Benchmark Suite (Dandy Dungeon Rust WASM) ===");
console.log(`Artifact: ${wasmFile} (${wasmBytes.length} bytes)`);

const PAIRS = 10;
const FRAMES_PER_ARM = 2000;

// Arm A: Cold-cache / fresh game ticks
// Arm B: Active gameplay continuous ticks
const timesA = [];
const timesB = [];

for (let pair = 0; pair < PAIRS; pair++) {
    // ABBA sequence: A, B, B, A
    // 1. A1
    {
        const app = new DandyApp();
        const t0 = performance.now();
        for (let f = 0; f < FRAMES_PER_ARM; f++) {
            if (f % 8 === 0) app.set_action(0, PlayerAction.Right, true);
            else if (f % 8 === 4) app.set_action(0, PlayerAction.Right, false);
            app.tick();
        }
        const t1 = performance.now();
        timesA.push(t1 - t0);
    }

    // 2. B1
    {
        const app = new DandyApp();
        // Warm up and simulate multi-player active gameplay
        app.set_action(1, PlayerAction.Right, true); // join P2
        for (let w = 0; w < 100; w++) app.tick();
        const t0 = performance.now();
        for (let f = 0; f < FRAMES_PER_ARM; f++) {
            if (f % 6 === 0) app.set_action(0, PlayerAction.Shoot, true);
            else if (f % 6 === 3) app.set_action(0, PlayerAction.Shoot, false);
            if (f % 8 === 0) app.set_action(1, PlayerAction.Up, true);
            else if (f % 8 === 4) app.set_action(1, PlayerAction.Up, false);
            app.tick();
        }
        const t1 = performance.now();
        timesB.push(t1 - t0);
    }

    // 3. B2
    {
        const app = new DandyApp();
        app.set_action(1, PlayerAction.Right, true);
        for (let w = 0; w < 100; w++) app.tick();
        const t0 = performance.now();
        for (let f = 0; f < FRAMES_PER_ARM; f++) {
            if (f % 6 === 0) app.set_action(0, PlayerAction.Shoot, true);
            else if (f % 6 === 3) app.set_action(0, PlayerAction.Shoot, false);
            if (f % 8 === 0) app.set_action(1, PlayerAction.Up, true);
            else if (f % 8 === 4) app.set_action(1, PlayerAction.Up, false);
            app.tick();
        }
        const t1 = performance.now();
        timesB.push(t1 - t0);
    }

    // 4. A2
    {
        const app = new DandyApp();
        const t0 = performance.now();
        for (let f = 0; f < FRAMES_PER_ARM; f++) {
            if (f % 8 === 0) app.set_action(0, PlayerAction.Right, true);
            else if (f % 8 === 4) app.set_action(0, PlayerAction.Right, false);
            app.tick();
        }
        const t1 = performance.now();
        timesA.push(t1 - t0);
    }
}

function stats(arr) {
    arr.sort((a, b) => a - b);
    const sum = arr.reduce((acc, v) => acc + v, 0);
    const mean = sum / arr.length;
    const p50 = arr[Math.floor(arr.length / 2)];
    const min = arr[0];
    const max = arr[arr.length - 1];
    return { mean, p50, min, max, perFrameUs: (p50 / FRAMES_PER_ARM) * 1000, fps: FRAMES_PER_ARM / (p50 / 1000) };
}

const statsA = stats(timesA);
const statsB = stats(timesB);

console.log(`\nResults across ${PAIRS * 2} runs per arm (${FRAMES_PER_ARM} frames each):`);
console.log(`Arm A (Single-Player Solo):`);
console.log(`  p50: ${statsA.p50.toFixed(2)} ms | min: ${statsA.min.toFixed(2)} ms | max: ${statsA.max.toFixed(2)} ms`);
console.log(`  Per-frame latency (p50): ${statsA.perFrameUs.toFixed(2)} µs/frame | Throughput: ${statsA.fps.toFixed(0)} FPS`);

console.log(`Arm B (Two-Player Active Co-op with Projectiles & AI):`);
console.log(`  p50: ${statsB.p50.toFixed(2)} ms | min: ${statsB.min.toFixed(2)} ms | max: ${statsB.max.toFixed(2)} ms`);
console.log(`  Per-frame latency (p50): ${statsB.perFrameUs.toFixed(2)} µs/frame | Throughput: ${statsB.fps.toFixed(0)} FPS`);
