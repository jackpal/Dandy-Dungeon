import fs from 'fs';
import path from 'path';
import assert from 'assert';

console.log("=== Running Dandy Dungeon WASM Built-Artifact Parity & Netcode Suite ===");

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
assert(routeInfo.includes("rollback-4p"), "Route info must indicate rollback netcode");
console.log("✓ Route introspection & capabilities verified.");

// 3. 4-Player Slot & Character Metadata Introspection
console.log("\nTesting 4-Player Character Slot APIs...");
assert.strictEqual(app.get_player_class_name(0), "Ruby");
assert.strictEqual(app.get_player_class_name(1), "Sapphire");
assert.strictEqual(app.get_player_class_name(2), "Topaz");
assert.strictEqual(app.get_player_class_name(3), "Emerald");
assert.strictEqual(app.is_player_active(0), true, "P1 should start active");
assert.strictEqual(app.is_player_active(1), false, "P2 should start inactive");

app.spawn_player(2); // Spawn P3 Topaz
assert.strictEqual(app.is_player_active(2), true, "P3 should now be active");
app.remove_player(2);
assert.strictEqual(app.is_player_active(2), false, "P3 should now be inactive");
console.log("✓ 4-Player Character Slot APIs verified.");

// 4. Determinism & Parity Test (OP-PAR / Tier 1/2 Parity)
// Two separate DandyApp instances given identical input sequences must produce bit-identical states & framebuffers
console.log("\nTesting Determinism & Multi-Instance Lockstep Parity (1000 frames)...");
const simA = new DandyApp();
const simB = new DandyApp();

for (let frame = 0; frame < 1000; frame++) {
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

    // Dynamic P2 & P3 join with concurrent inputs
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

    if (frame === 400) {
        simA.set_action(2, PlayerAction.Down, true);
        simB.set_action(2, PlayerAction.Down, true);
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

// 5. State Snapshot Binary Serialization & Restoration
console.log("\nTesting Full State Snapshot Serialization & Roundtrip...");
const snapBytes = simA.save_state_bytes();
assert(snapBytes.length > 1800, `Snapshot size ${snapBytes.length} bytes expected > 1800`);
const restoredSim = new DandyApp();
const ok = restoredSim.load_state_bytes(snapBytes);
assert(ok, "load_state_bytes must succeed");
assert.strictEqual(restoredSim.get_level(), simA.get_level());

const restoredStats = new Int32Array(wasmInstance.memory.buffer, restoredSim.get_stats_ptr(), restoredSim.get_stats_len());
const simAStats = new Int32Array(wasmInstance.memory.buffer, simA.get_stats_ptr(), simA.get_stats_len());
for (let i = 0; i < restoredSim.get_stats_len(); i++) {
    assert.strictEqual(restoredStats[i], simAStats[i], `Snapshot restored stats mismatch at ${i}`);
}
console.log(`✓ Full State Snapshot roundtrip verified (${snapBytes.length} bytes).`);

// 6. Rollback Netcode Engine & Jitter Recovery Verification
console.log("\nTesting Rollback Netcode Prediction & Late Packet Re-simulation...");
const hostPeer = new DandyApp();
hostPeer.net_init(0); // Host as P1 Ruby
hostPeer.net_set_player_joined(1, true); // P2 Sapphire joined

const joinerPeer = new DandyApp();
joinerPeer.net_init(1); // Joiner as P2 Sapphire
joinerPeer.net_set_player_joined(0, true);

// Step 15 frames on host with P2 input delayed (predicting 0 on host)
for (let f = 0; f < 15; f++) {
    hostPeer.net_set_local_action(PlayerAction.Right, true);
    hostPeer.net_step();
}
assert.strictEqual(hostPeer.net_get_current_frame(), 15);
assert.strictEqual(hostPeer.net_get_rollback_count(), 0, "No rollback before packet arrival");

// Joiner produced action Up at frame 5
joinerPeer.net_set_local_action(PlayerAction.Up, true);
const joinerPktFrame5 = joinerPeer.net_encode_local_input_packet(5);

// Late arrival of Joiner's packet at frame 5 into Host (which is currently at frame 15)
const didRollback = hostPeer.net_receive_remote_packet(joinerPktFrame5);
assert.strictEqual(didRollback, true, "Host must execute rollback upon late packet arrival with differing input");
assert.strictEqual(hostPeer.net_get_rollback_count(), 1, "Rollback count must increment to 1");
assert.strictEqual(hostPeer.net_get_resimulated_frames() >= 10, true, "Host must have resimulated at least 10 frames");
console.log(`✓ Rollback Netcode verified: Host rewound from frame 15 -> 5 and resimulated cleanly.`);

// Test: Packet arrival where input matches prediction must NOT trigger unnecessary rollback
const matchingPkt = hostPeer.net_encode_local_input_packet(15);
const didMatchRollback = hostPeer.net_receive_remote_packet(matchingPkt);
assert.strictEqual(didMatchRollback, false, "Packet matching local slot or current state must not trigger rollback");
console.log("✓ Zero-rollback prediction match confirmed.");

// Test: Out-of-order network packet delivery (Frame 8 arrives, then delayed Frame 6 arrives)
const peerA = new DandyApp();
peerA.net_init(0);
peerA.net_set_player_joined(1, true);
for (let f = 0; f < 12; f++) {
    peerA.net_set_local_action(PlayerAction.Right, true);
    peerA.net_step();
}

const peerB = new DandyApp();
peerB.net_init(1);
peerB.net_set_player_joined(0, true);

// Send frame 8 first
peerB.net_set_local_action(PlayerAction.Up, true);
const pktFrame8 = peerB.net_encode_local_input_packet(8);
const rb1 = peerA.net_receive_remote_packet(pktFrame8);
assert.strictEqual(rb1, true, "Frame 8 packet must trigger rollback");

// Now send frame 6 AFTER frame 8 (out-of-order packet arrival)
peerB.net_set_local_action(PlayerAction.Left, true);
const pktFrame6 = peerB.net_encode_local_input_packet(6);
const rb2 = peerA.net_receive_remote_packet(pktFrame6);
assert.strictEqual(rb2, true, "Out-of-order Frame 6 packet must trigger rollback even after Frame 8 arrived");
assert.strictEqual(peerA.net_get_rollback_count(), 2, "Rollback count should be 2 after handling out-of-order packet");
console.log("✓ Out-of-order packet rollback recovery verified.");

// 7. Boundary extraction zero-copy view validity
const fbPtr = app.get_framebuffer_ptr();
const fbSize = app.get_framebuffer_size();
const fbBytes = new Uint8ClampedArray(wasmInstance.memory.buffer, fbPtr, fbSize);
assert.strictEqual(fbBytes.length, 320 * 160 * 4, "Framebuffer byte length must be 320*160*4");
console.log("✓ Zero-Copy Framebuffer ABI view verified.");

console.log("\n=== ALL BUILT-ARTIFACT PARITY & MULTIPLAYER TESTS PASSED ===");
