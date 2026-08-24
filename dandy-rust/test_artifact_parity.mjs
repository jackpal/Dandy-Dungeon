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
const { DandyApp, PlayerAction, Difficulty, net_get_protocol_version, net_get_app_id } = glue;

assert(DandyApp, "DandyApp export missing");
assert(PlayerAction, "PlayerAction export missing");
assert(Difficulty, "Difficulty export missing");
assert.strictEqual(Difficulty.Trivial, 0);
assert.strictEqual(Difficulty.Easy, 1);
assert.strictEqual(Difficulty.Hard, 2);
assert.strictEqual(Difficulty.Deadly, 3);

// Protocol & App ID verification
assert.strictEqual(net_get_protocol_version(), 1, "Top-level net_get_protocol_version must return 1");
assert.strictEqual(net_get_app_id(), "dandy-dungeon", "Top-level net_get_app_id must return 'dandy-dungeon'");
console.log("✓ Module compiled and exports verified (including 4-level Difficulty enum and Protocol v1 metadata).");

// 2. Route Introspection & Build Metadata Check (OP-ROUTE)
const app = new DandyApp();
assert.strictEqual(app.net_get_protocol_version(), 1, "DandyApp.net_get_protocol_version must return 1");
assert.strictEqual(app.net_get_app_id(), "dandy-dungeon", "DandyApp.net_get_app_id must return 'dandy-dungeon'");

// Binary handshake packet verification
const handshakePkt = app.net_encode_handshake_packet();
assert.strictEqual(handshakePkt.length, 5, "Handshake packet must be 5 bytes");
assert.strictEqual(handshakePkt[0], 0x00, "Handshake opcode must be 0x00");
assert.strictEqual(handshakePkt[1], 0x44, "Magic byte 0 must be 'D' (0x44)");
assert.strictEqual(handshakePkt[2], 0x44, "Magic byte 1 must be 'D' (0x44)");
assert.strictEqual(app.net_validate_handshake_packet(handshakePkt), true, "Handshake packet must validate");
assert.strictEqual(app.net_decode_handshake_version(handshakePkt), 1, "Handshake version must decode to 1");

// Corrupted / mismatch handshake rejection tests
const invalidHandshake = new Uint8Array([0x00, 0x44, 0x44, 0x00, 0x63]); // v99
assert.strictEqual(app.net_validate_handshake_packet(invalidHandshake), false, "v99 handshake must fail validation");
assert.strictEqual(app.net_decode_handshake_version(invalidHandshake), 99, "v99 handshake version must decode to 99");

const corruptMagicHandshake = new Uint8Array([0x00, 0x58, 0x44, 0x00, 0x01]);
assert.strictEqual(app.net_validate_handshake_packet(corruptMagicHandshake), false, "Corrupt magic handshake must fail validation");
assert.strictEqual(app.net_decode_handshake_version(corruptMagicHandshake), -1, "Corrupt magic handshake must return -1");
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

// 3b. 4-Level Difficulty System APIs
console.log("\nTesting 4-Level Difficulty APIs...");
assert.strictEqual(app.get_difficulty(), Difficulty.Easy, "Default difficulty must be Easy (1)");
app.set_difficulty(Difficulty.Deadly);
assert.strictEqual(app.get_difficulty(), Difficulty.Deadly, "Difficulty must update to Deadly (3)");
app.set_difficulty(Difficulty.Trivial);
assert.strictEqual(app.get_difficulty(), Difficulty.Trivial, "Difficulty must update to Trivial (0)");
app.set_difficulty(Difficulty.Hard);
assert.strictEqual(app.get_difficulty(), Difficulty.Hard, "Difficulty must update to Hard (2)");
app.set_difficulty(Difficulty.Easy); // Reset to default Easy
console.log("✓ 4-Level Difficulty System APIs verified.");

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

    // Check 32-bit state checksum parity on every frame
    assert.strictEqual(simA.get_state_checksum(), simB.get_state_checksum(), `State checksum mismatch on frame ${frame}: A=0x${simA.get_state_checksum().toString(16)}, B=0x${simB.get_state_checksum().toString(16)}`);

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
console.log(`✓ Lockstep Parity & State Checksums verified across 1000 frames (Final Checksum: 0x${simA.get_state_checksum().toString(16)}): 100% bit-identical.`);

// 5. State Snapshot Binary Serialization & Restoration
console.log("\nTesting Full State Snapshot Serialization & Roundtrip...");
const snapBytes = simA.save_state_bytes();
assert(snapBytes.length > 1800, `Snapshot size ${snapBytes.length} bytes expected > 1800`);
const restoredSim = new DandyApp();
const ok = restoredSim.load_state_bytes(snapBytes);
assert(ok, "load_state_bytes must succeed");
assert.strictEqual(restoredSim.get_level(), simA.get_level());
assert.strictEqual(restoredSim.get_state_checksum(), simA.get_state_checksum(), "Restored snapshot checksum must match original state");

const restoredStats = new Int32Array(wasmInstance.memory.buffer, restoredSim.get_stats_ptr(), restoredSim.get_stats_len());
const simAStats = new Int32Array(wasmInstance.memory.buffer, simA.get_stats_ptr(), simA.get_stats_len());
for (let i = 0; i < restoredSim.get_stats_len(); i++) {
    assert.strictEqual(restoredStats[i], simAStats[i], `Snapshot restored stats mismatch at ${i}`);
}
console.log(`✓ Full State Snapshot roundtrip verified (${snapBytes.length} bytes, Checksum: 0x${restoredSim.get_state_checksum().toString(16)}).`);

// 6. Rollback Netcode WASM Boundary & Desync Healing Verification
console.log("\nTesting Rollback Netcode WASM Boundary & Desync Healing...");
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

// Late arrival of Joiner's packet at frame 5 into Host (currently at frame 15)
const didRollback = hostPeer.net_receive_remote_packet(joinerPktFrame5);
assert.strictEqual(didRollback, true, "Host must execute rollback upon late packet arrival with differing input");
assert.strictEqual(hostPeer.net_get_rollback_count(), 1, "Rollback count must increment to 1");
assert.strictEqual(hostPeer.net_get_resimulated_frames() >= 10, true, "Host must have resimulated at least 10 frames");
console.log(`✓ Rollback Netcode WASM ABI verified: Host rewound from frame 15 -> 5 and resimulated cleanly.`);

// Test Authoritative State Sync & Automatic Desync Healing
const desyncHost = new DandyApp();
desyncHost.net_init(0);
desyncHost.net_set_player_joined(1, true);

const desyncJoiner = new DandyApp();
desyncJoiner.net_init(1);
desyncJoiner.net_set_player_joined(0, true);

for (let f = 0; f < 30; f++) {
    desyncHost.net_set_player_local_action(0, PlayerAction.Right, true);
    desyncJoiner.net_set_player_local_action(1, PlayerAction.Down, true);
    const pktH = desyncHost.net_encode_local_input_packet(f);
    const pktJ = desyncJoiner.net_encode_local_input_packet(f);
    desyncHost.net_receive_remote_packet(pktJ);
    desyncJoiner.net_receive_remote_packet(pktH);
    desyncHost.net_step();
    desyncJoiner.net_step();
}
assert.strictEqual(desyncHost.get_state_checksum(), desyncJoiner.get_state_checksum(), "Host and Joiner must share identical checksums in lockstep");

// Inject artificial desync on Joiner by advancing local ticks
desyncJoiner.tick();
desyncJoiner.tick();
assert.notStrictEqual(desyncHost.get_state_checksum(), desyncJoiner.get_state_checksum(), "Injected desync must be detected via checksum mismatch");

// Deliver Authoritative PKT_STATE_SYNC snapshot from Host to Joiner
const hostAuthSnap = desyncHost.save_state_bytes();
const healOk = desyncJoiner.net_load_sync_state(desyncHost.net_get_current_frame(), hostAuthSnap);
assert.strictEqual(healOk, true, "net_load_sync_state must succeed");
assert.strictEqual(desyncJoiner.get_state_checksum(), desyncHost.get_state_checksum(), "Authoritative state sync must restore 100% bit-identical checksum");
console.log(`✓ Desync successfully healed: Joiner restored to 100% bit-identical lockstep.`);

// 7. HTML5 Gamepad Action Bitmask Mapping & Determinism
console.log("\nTesting Gamepad Action Bitmask Mapping & Determinism (200 frames)...");
const gpSimA = new DandyApp();
const gpSimB = new DandyApp();

for (let f = 0; f < 200; f++) {
    // Simulate Gamepad D-Pad & Analog stick inputs (Up, Down, Left, Right)
    const dpadMask = (f % 4 === 0) ? (1 << PlayerAction.Right) :
                     (f % 4 === 1) ? (1 << PlayerAction.Down) :
                     (f % 4 === 2) ? (1 << PlayerAction.Left) : (1 << PlayerAction.Up);
    
    // Simulate Fire Arrow (Button 0/7 -> Action Shoot)
    const fireMask = (f % 7 === 0) ? (1 << PlayerAction.Shoot) : 0;
    // Simulate Smart Bomb (Button 1/2 -> Action Bomb)
    const bombMask = (f === 50 || f === 100) ? (1 << PlayerAction.Bomb) : 0;

    const totalMask = dpadMask | fireMask | bombMask;
    gpSimA.set_player_input_mask(0, totalMask);
    gpSimB.set_player_input_mask(0, totalMask);

    gpSimA.tick();
    gpSimB.tick();

    assert.strictEqual(gpSimA.get_player_x(0), gpSimB.get_player_x(0), `Gamepad X parity failure at frame ${f}`);
    assert.strictEqual(gpSimA.get_player_y(0), gpSimB.get_player_y(0), `Gamepad Y parity failure at frame ${f}`);
    assert.strictEqual(gpSimA.get_level(), gpSimB.get_level(), `Gamepad Level parity failure at frame ${f}`);
}
console.log("✓ Gamepad Action Bitmask Mapping & Determinism verified.");

// 8. Boundary extraction zero-copy view validity & graphics rendering parity
console.log("\nTesting Zero-Copy Framebuffer ABI, Pixel Density, and Dynamic Graphics Rendering...");
const fbPtr = app.get_framebuffer_ptr();
const fbSize = app.get_framebuffer_size();
const fbBytes = new Uint8ClampedArray(wasmInstance.memory.buffer, fbPtr, fbSize);
assert.strictEqual(fbBytes.length, 320 * 160 * 4, "Framebuffer byte length must be 320*160*4");

let nonZeroRgbCount = 0;
const colorHistogram = new Map();
for (let i = 0; i < fbBytes.length; i += 4) {
    const r = fbBytes[i];
    const g = fbBytes[i + 1];
    const b = fbBytes[i + 2];
    const a = fbBytes[i + 3];
    assert.strictEqual(a, 255, `Alpha channel must always be 255 (found ${a} at pixel ${i/4})`);
    if (r !== 0 || g !== 0 || b !== 0) {
        nonZeroRgbCount++;
        const key = `${r},${g},${b}`;
        colorHistogram.set(key, (colorHistogram.get(key) || 0) + 1);
    }
}
// 320x160 = 51200 pixels. Level 1 rendering has active dungeon tiles (walls, player, floor features) covering thousands of pixels.
assert(nonZeroRgbCount > 10000, `Framebuffer must render non-zero RGB pixel graphics (found ${nonZeroRgbCount} / 51200 non-zero RGB pixels)`);
assert(colorHistogram.size >= 3, `Framebuffer must render multiple distinct colors (found ${colorHistogram.size} distinct colors)`);
console.log(`✓ Zero-Copy Framebuffer initial render verified (${nonZeroRgbCount} active RGB pixels, ${colorHistogram.size} distinct colors).`);

// Verify dynamic pixel animation upon player movement
const renderSim = new DandyApp();
const fbPtrRender = renderSim.get_framebuffer_ptr();
const fbBytesBefore = new Uint8Array(wasmInstance.memory.buffer.slice(fbPtrRender, fbPtrRender + fbSize));

// Move player right 10 frames
renderSim.set_action(0, PlayerAction.Right, true);
for (let f = 0; f < 10; f++) {
    renderSim.tick();
}
const fbBytesAfter = new Uint8Array(wasmInstance.memory.buffer.slice(fbPtrRender, fbPtrRender + fbSize));
let diffPixels = 0;
for (let i = 0; i < fbSize; i += 4) {
    if (fbBytesBefore[i] !== fbBytesAfter[i] || fbBytesBefore[i+1] !== fbBytesAfter[i+1] || fbBytesBefore[i+2] !== fbBytesAfter[i+2]) {
        diffPixels++;
    }
}
assert(diffPixels > 50, `Player movement must visually animate/update framebuffer pixels (found ${diffPixels} changed pixels)`);
console.log(`✓ Framebuffer dynamic movement animation verified (${diffPixels} pixels updated upon moving).`);

// Verify arrow spawning visually renders into framebuffer
const fbBeforeShoot = new Uint8Array(wasmInstance.memory.buffer.slice(fbPtrRender, fbPtrRender + fbSize));
renderSim.set_action(0, PlayerAction.Right, false);
renderSim.set_action(0, PlayerAction.Shoot, true);
renderSim.tick();
const fbAfterShoot = new Uint8Array(wasmInstance.memory.buffer.slice(fbPtrRender, fbPtrRender + fbSize));
let diffArrowPixels = 0;
for (let i = 0; i < fbSize; i += 4) {
    if (fbBeforeShoot[i] !== fbAfterShoot[i] || fbBeforeShoot[i+1] !== fbAfterShoot[i+1] || fbBeforeShoot[i+2] !== fbAfterShoot[i+2]) {
        diffArrowPixels++;
    }
}
assert(diffArrowPixels > 0, `Spawning and rendering arrow must visually update framebuffer (found ${diffArrowPixels} changed pixels)`);
console.log(`✓ Arrow projectile framebuffer visual rendering verified (${diffArrowPixels} pixels updated).`);

// 9. POKEY Priority Audio Scheduler & Multi-Channel APIs
console.log("\nTesting POKEY Priority Audio Scheduler & Channel APIs...");
assert(DandyApp.get_sound_priority(3) > DandyApp.get_sound_priority(13), "Bomb priority must exceed Death");
assert(DandyApp.get_sound_priority(13) > DandyApp.get_sound_priority(2), "Death priority must exceed Shoot");
assert.strictEqual(DandyApp.get_sound_pokey_channel(3), 3, "Bomb Explode -> Channel 3");
assert.strictEqual(DandyApp.get_sound_pokey_channel(12), 2, "Monster Bite -> Channel 2");
assert.strictEqual(DandyApp.get_sound_pokey_channel(1), 1, "Hit Player -> Channel 1");
assert.strictEqual(DandyApp.get_sound_pokey_channel(2), 0, "Shoot -> Channel 0");

const audioSim = new DandyApp();
// On initial creation (Level 1 start), SOUND_WARP_IN (15) must be queued in sound events and active on Channel 3
const initEvents = audioSim.get_sound_events();
assert(initEvents.includes(15), "Initial Level 1 load must emit SOUND_WARP_IN (15)");
assert.strictEqual((audioSim.get_sound_mask() & (1 << 15)) !== 0, true, "Sound mask bit 15 must be set for Level 1 start");
assert.strictEqual(audioSim.get_audio_channel_sound(3), 15, "Channel 3 must play SOUND_WARP_IN upon Level 1 load");

// Single shoot action -> emits SOUND_SHOOT on frame 1
audioSim.set_action(0, PlayerAction.Shoot, true);
audioSim.tick();
const events = audioSim.get_sound_events();
assert(events.includes(2), "Sound events must contain SOUND_SHOOT (2)");
assert.strictEqual((audioSim.get_sound_mask() & (1 << 2)) !== 0, true, "Sound mask bit 2 must be set");
assert.strictEqual(audioSim.get_audio_channel_sound(0), 2, "Channel 0 must play SOUND_SHOOT");

// Player movement followed by immediate shoot action
const moveShootSim = new DandyApp();
moveShootSim.set_action(0, PlayerAction.Right, true);
moveShootSim.tick();
moveShootSim.set_action(0, PlayerAction.Right, false);
for (let i = 0; i < 8; i++) {
    moveShootSim.tick();
}
// Now fire arrow immediately after moving
moveShootSim.set_action(0, PlayerAction.Shoot, true);
moveShootSim.tick();
const moveShootEvents = moveShootSim.get_sound_events();
assert(moveShootEvents.includes(2), "Sound events after moving must contain SOUND_SHOOT (2)");
assert.strictEqual((moveShootSim.get_sound_mask() & (1 << 2)) !== 0, true, "Sound mask bit 2 must be set after moving");
assert.strictEqual(moveShootSim.get_audio_channel_sound(0), 2, "Channel 0 must play SOUND_SHOOT after moving");

console.log("✓ POKEY Priority Audio Scheduler & Multi-Channel APIs verified.");

console.log("\n=== ALL BUILT-ARTIFACT PARITY & MULTIPLAYER TESTS PASSED ===");
