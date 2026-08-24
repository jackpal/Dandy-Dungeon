import fs from 'fs';
import path from 'path';
import assert from 'assert';

console.log("=== Running Dandy Dungeon WASM Built-Artifact Parity Suite ===");

const distDir = './dist';
if (!fs.existsSync(distDir)) {
    console.error("ERROR: dist/ directory not found. Please run 'bash build.sh' first.");
    process.exit(1);
}

const files = fs.readdirSync(distDir);
const jsFile = files.find(f => f.endsWith('.js') && !f.includes('bench'));
const wasmFile = files.find(f => f.endsWith('.wasm'));

if (!jsFile || !wasmFile) {
    console.error("ERROR: Missing .js glue or .wasm binary in dist/");
    process.exit(1);
}

const wasmPath = path.join(distDir, wasmFile);
const wasmBytes = fs.readFileSync(wasmPath);
console.log(`[Artifact] Loaded ${wasmFile} (${wasmBytes.length} bytes)`);

// 1. Instantiation check
const wasmModule = await WebAssembly.compile(wasmBytes);
const glue = await import(path.resolve(distDir, jsFile));
const wasmInstance = await glue.default({ module_or_path: wasmModule });
const { DandyApp, PlayerAction } = glue;

assert(DandyApp, "DandyApp export missing");
assert(PlayerAction, "PlayerAction export missing");
console.log("✓ Module compiled and exports verified.");

// 2. Route Introspection & Build Metadata Check (OP-ROUTE)
const app = new DandyApp();
const buildInfo = app.get_build_info();
const routeInfo = app.get_route_info();
console.log(`[Route Info] ${routeInfo}`);
console.log(`[Build Info] ${buildInfo}`);
assert(buildInfo.includes("wasm32"), "Build info must indicate wasm32");
assert(routeInfo.includes("sm-pie"), "Route info must indicate sm-pie");
assert(routeInfo.includes("parity=tier-2"), "Route info must indicate parity tier");
console.log("✓ Route introspection (OP-ROUTE) verified.");

// 3. Determinism & Parity Test (OP-PAR / Tier 1/2 Parity)
// Two separate DandyApp instances given identical input sequences must produce bit-identical states & framebuffers
console.log("\nTesting Determinism & Multi-Instance Lockstep Parity (1000 frames)...");
const simA = new DandyApp();
const simB = new DandyApp();

for (let frame = 0; frame < 1000; frame++) {
    // Scripted pseudo-random multi-action input sequence across all PlayerAction variants
    const r = frame % 29;
    if (r === 0) {
        simA.set_action(0, PlayerAction.Right, true);
        simB.set_action(0, PlayerAction.Right, true);
    } else if (r === 4) {
        simA.set_action(0, PlayerAction.Right, false);
        simB.set_action(0, PlayerAction.Right, false);
    } else if (r === 7) {
        simA.set_action(0, PlayerAction.Down, true);
        simB.set_action(0, PlayerAction.Down, true);
    } else if (r === 11) {
        simA.set_action(0, PlayerAction.Down, false);
        simB.set_action(0, PlayerAction.Down, false);
    } else if (r === 14) {
        simA.set_action(0, PlayerAction.Left, true);
        simB.set_action(0, PlayerAction.Left, true);
    } else if (r === 17) {
        simA.set_action(0, PlayerAction.Left, false);
        simB.set_action(0, PlayerAction.Left, false);
    } else if (r === 20) {
        simA.set_action(0, PlayerAction.Up, true);
        simB.set_action(0, PlayerAction.Up, true);
    } else if (r === 23) {
        simA.set_action(0, PlayerAction.Up, false);
        simB.set_action(0, PlayerAction.Up, false);
    }

    if (frame % 13 === 0) {
        simA.set_action(0, PlayerAction.Shoot, true);
        simB.set_action(0, PlayerAction.Shoot, true);
    } else if (frame % 13 === 6) {
        simA.set_action(0, PlayerAction.Shoot, false);
        simB.set_action(0, PlayerAction.Shoot, false);
    }

    if (frame === 150 || frame === 450 || frame === 750) {
        simA.set_action(0, PlayerAction.Bomb, true);
        simB.set_action(0, PlayerAction.Bomb, true);
    } else if (frame === 152 || frame === 452 || frame === 752) {
        simA.set_action(0, PlayerAction.Bomb, false);
        simB.set_action(0, PlayerAction.Bomb, false);
    }

    // Dynamic P2 join at frame 200 with concurrent inputs
    if (frame === 200) {
        simA.set_action(1, PlayerAction.Right, true);
        simB.set_action(1, PlayerAction.Right, true);
    }
    if (frame > 200 && frame % 19 === 0) {
        simA.set_action(1, PlayerAction.Up, true);
        simB.set_action(1, PlayerAction.Up, true);
    } else if (frame > 200 && frame % 19 === 8) {
        simA.set_action(1, PlayerAction.Up, false);
        simB.set_action(1, PlayerAction.Up, false);
    }
    if (frame > 200 && frame % 23 === 0) {
        simA.set_action(1, PlayerAction.Shoot, true);
        simB.set_action(1, PlayerAction.Shoot, true);
    } else if (frame > 200 && frame % 23 === 10) {
        simA.set_action(1, PlayerAction.Shoot, false);
        simB.set_action(1, PlayerAction.Shoot, false);
    }

    simA.tick();
    simB.tick();

    // Check level parity
    assert.strictEqual(simA.get_level(), simB.get_level(), `Level mismatch at frame ${frame}`);

    // Check stats buffer byte parity
    const statsPtrA = simA.get_stats_ptr();
    const statsPtrB = simB.get_stats_ptr();
    const statsLenA = simA.get_stats_len();
    const statsArrayA = new Int32Array(wasmInstance.memory.buffer, statsPtrA, statsLenA);
    const statsArrayB = new Int32Array(wasmInstance.memory.buffer, statsPtrB, statsLenA);

    for (let i = 0; i < statsLenA; i++) {
        if (statsArrayA[i] !== statsArrayB[i]) {
            throw new Error(`Stats buffer mismatch at index ${i} on frame ${frame}: A=${statsArrayA[i]}, B=${statsArrayB[i]}`);
        }
    }

    // Check framebuffer pixel byte parity every 50 frames
    if (frame % 50 === 0) {
        const fbPtrA = simA.get_framebuffer_ptr();
        const fbPtrB = simB.get_framebuffer_ptr();
        const fbSizeA = simA.get_framebuffer_size();
        const fbBytesA = new Uint8Array(wasmInstance.memory.buffer, fbPtrA, fbSizeA);
        const fbBytesB = new Uint8Array(wasmInstance.memory.buffer, fbPtrB, fbSizeA);

        for (let j = 0; j < fbSizeA; j++) {
            if (fbBytesA[j] !== fbBytesB[j]) {
                throw new Error(`Framebuffer pixel mismatch at byte offset ${j} on frame ${frame}: A=${fbBytesA[j]}, B=${fbBytesB[j]}`);
            }
        }
    }
}
console.log("✓ Lockstep Parity verified across 1000 frames: 100% bit-identical.");

// 4. Boundary extraction zero-copy view validity
const fbPtr = app.get_framebuffer_ptr();
const fbSize = app.get_framebuffer_size();
const fbBytes = new Uint8ClampedArray(wasmInstance.memory.buffer, fbPtr, fbSize);
assert.strictEqual(fbBytes.length, 320 * 160 * 4, "Framebuffer byte length must be 320*160*4");
console.log("✓ Zero-Copy Framebuffer ABI view verified.");

console.log("\n=== ALL BUILT-ARTIFACT PARITY TESTS PASSED ===");
