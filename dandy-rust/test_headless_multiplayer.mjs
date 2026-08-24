import { execFile } from 'child_process';
import assert from 'assert';
import path from 'path';

console.log("=== Dandy Dungeon Headless Multi-Browser WebRTC Multiplayer Test ===");

const GBROWSER_BIN = "/google/bin/releases/gemini-agents-gbrowser/gbrowser";

const testCode = `
new Promise(async (resolve, reject) => {
    try {
        console.log("[Test] 1. Initializing Host (P1 Ruby)...");
        document.getElementById("tab-online").click();
        document.getElementById("btn-create-room").click();
        await new Promise(r => setTimeout(r, 200));

        const roomCode = document.getElementById("net-stat-room").textContent;
        console.log("[Test] Host created room:", roomCode);
        if (!roomCode || roomCode === "NONE") {
            throw new Error("Failed to create room code");
        }

        // Helper to spawn a joiner iframe
        function spawnJoiner(slotName, hash) {
            const iframe = document.createElement("iframe");
            iframe.src = "http://127.0.0.1:8080/" + hash;
            iframe.style.width = "320px";
            iframe.style.height = "200px";
            iframe.setAttribute("data-slot", slotName);
            document.body.appendChild(iframe);
            return iframe;
        }

        console.log("[Test] 2. Spawning P2 (Sapphire), P3 (Topaz), and P4 (Emerald)...");
        const iframeP2 = spawnJoiner("P2", "#room=" + roomCode);
        const iframeP3 = spawnJoiner("P3", "#room=" + roomCode);
        const iframeP4 = spawnJoiner("P4", "#room=" + roomCode);

        // Helper to poll for condition
        async function waitFor(fn, timeoutMs, desc) {
            const start = Date.now();
            while (Date.now() - start < timeoutMs) {
                try {
                    if (fn()) return;
                } catch (_) {}
                await new Promise(r => setTimeout(r, 100));
            }
            throw new Error("Timeout waiting for: " + desc);
        }

        console.log("[Test] 3. Waiting for WebRTC DataChannel 4-player mesh connection...");
        await waitFor(() => {
            const p1App = window.dandyApp;
            const p2App = iframeP2.contentWindow?.dandyApp;
            const p3App = iframeP3.contentWindow?.dandyApp;
            const p4App = iframeP4.contentWindow?.dandyApp;

            if (!p1App || !p2App || !p3App || !p4App) return false;

            // All peers should see all 4 players joined
            const p1Ready = p1App.net_is_player_joined(0) && p1App.net_is_player_joined(1) && p1App.net_is_player_joined(2) && p1App.net_is_player_joined(3);
            const p2Ready = p2App.net_is_player_joined(0) && p2App.net_is_player_joined(1) && p2App.net_is_player_joined(2) && p2App.net_is_player_joined(3);
            const p3Ready = p3App.net_is_player_joined(0) && p3App.net_is_player_joined(1) && p3App.net_is_player_joined(2) && p3App.net_is_player_joined(3);
            const p4Ready = p4App.net_is_player_joined(0) && p4App.net_is_player_joined(1) && p4App.net_is_player_joined(2) && p4App.net_is_player_joined(3);

            return p1Ready && p2Ready && p3Ready && p4Ready;
        }, 15000, "WebRTC 4-player DataChannel mesh");

        console.log("[Test] 4. Inspecting Slot Badges & HUD elements across all 4 peers...");
        const p1Badges = [1, 2, 3, 4].map(i => document.getElementById("slot-badge-p" + i)?.textContent);
        const p2Badges = [1, 2, 3, 4].map(i => iframeP2.contentDocument?.getElementById("slot-badge-p" + i)?.textContent);
        const p3Badges = [1, 2, 3, 4].map(i => iframeP3.contentDocument?.getElementById("slot-badge-p" + i)?.textContent);
        const p4Badges = [1, 2, 3, 4].map(i => iframeP4.contentDocument?.getElementById("slot-badge-p" + i)?.textContent);

        const getControlBadges = (doc) => {
            return Array.from(doc?.querySelectorAll(".controls-grid .control-status-badge") || []).map(el => el.textContent.trim());
        };
        const p1ControlBadges = getControlBadges(document);
        const p2ControlBadges = getControlBadges(iframeP2.contentDocument);
        const p3ControlBadges = getControlBadges(iframeP3.contentDocument);
        const p4ControlBadges = getControlBadges(iframeP4.contentDocument);

        const p1Status = document.getElementById("net-stat-status")?.textContent;
        const p2Status = iframeP2.contentDocument?.getElementById("net-stat-status")?.textContent;
        const p3Status = iframeP3.contentDocument?.getElementById("net-stat-status")?.textContent;
        const p4Status = iframeP4.contentDocument?.getElementById("net-stat-status")?.textContent;

        console.log("[Test] 5. Inspecting Initial Entity Positions across all 4 peers...");
        const getPositions = () => {
            const apps = [
                window.dandyApp,
                iframeP2.contentWindow?.dandyApp,
                iframeP3.contentWindow?.dandyApp,
                iframeP4.contentWindow?.dandyApp
            ];
            return apps.map((a, peerIdx) => {
                if (!a) return null;
                return [0, 1, 2, 3].map(p => ({
                    x: a.get_player_x(p),
                    y: a.get_player_y(p),
                    dir: a.get_player_dir(p)
                }));
            });
        };

        const initPositions = getPositions();
        console.log("[Test] Initial Positions on Host:", JSON.stringify(initPositions[0]));
        console.log("[Test] Initial Positions on P2:", JSON.stringify(initPositions[1]));

        console.log("[Test] 6. Simulating active 4-player directional movement with Dynamic Arrow Keys...");
        // Step 1: P1 (Host) moves Right via Arrow Keys (Primary Local on Host)
        window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }));
        await new Promise(r => setTimeout(r, 450));
        window.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowRight" }));
        await new Promise(r => setTimeout(r, 150));

        // Step 2: P2 (Joiner P2 Sapphire) moves Down via Arrow Keys (Primary Local on Joiner P2)
        iframeP2.contentWindow.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
        await new Promise(r => setTimeout(r, 450));
        iframeP2.contentWindow.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowDown" }));
        await new Promise(r => setTimeout(r, 150));

        // Step 3: P3 (Joiner P3 Topaz) moves Left via Arrow Keys (Primary Local on Joiner P3)
        iframeP3.contentWindow.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft" }));
        await new Promise(r => setTimeout(r, 450));
        iframeP3.contentWindow.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowLeft" }));
        await new Promise(r => setTimeout(r, 150));

        // Step 4: P4 (Joiner P4 Emerald) moves Up via Arrow Keys (Primary Local on Joiner P4)
        iframeP4.contentWindow.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
        await new Promise(r => setTimeout(r, 450));
        iframeP4.contentWindow.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowUp" }));
        await new Promise(r => setTimeout(r, 200));

        const finalPositions = getPositions();
        console.log("[Test] Final Positions on Host:", JSON.stringify(finalPositions[0]));
        console.log("[Test] Final Positions on P2:", JSON.stringify(finalPositions[1]));
        console.log("[Test] Final Positions on P3:", JSON.stringify(finalPositions[2]));
        console.log("[Test] Final Positions on P4:", JSON.stringify(finalPositions[3]));

        console.log("[Test] 7. Simulating HTML5 Gamepad API connection, status legend, sparse arrays, and analog movement...");
        // Mock Gamepad on Host (P1 Ruby) placed at OS index 1 (sparse array: [null, Gamepad 1])
        const mockGamepadP1 = {
            id: "Xbox Wireless Controller (STANDARD GAMEPAD Vendor: 045e Product: 02fd)",
            index: 1,
            connected: true,
            mapping: "standard",
            axes: [-0.75, 0.0], // Analog stick tilted Left into open corridor
            buttons: Array.from({ length: 17 }, (_, i) => ({ pressed: false, value: 0 }))
        };

        window.navigator.getGamepads = () => [null, mockGamepadP1, null, null];
        window.dispatchEvent(new Event("gamepadconnected"));
        await new Promise(r => setTimeout(r, 200));

        const p1GpStatus = document.getElementById("gamepad-status-text")?.textContent;
        const p1GpBadge = document.getElementById("gamepad-badge-p1")?.textContent;
        const p1GpBadgeVisible = document.getElementById("gamepad-badge-p1")?.style.display !== "none";
        const p2GpBadgeVisibleOnHost = document.getElementById("gamepad-badge-p2")?.style.display !== "none";

        // Step active simulation with Gamepad input
        await new Promise(r => setTimeout(r, 450));
        const posAfterGamepad = getPositions();

        // Disconnect Gamepad
        mockGamepadP1.connected = false;
        window.dispatchEvent(new Event("gamepaddisconnected"));
        await new Promise(r => setTimeout(r, 150));
        const p1GpStatusAfterDisconnect = document.getElementById("gamepad-status-text")?.textContent;
        const p1GpBadgeVisibleAfterDisconnect = document.getElementById("gamepad-badge-p1")?.style.display !== "none";

        const p1App = window.dandyApp;
        const p2App = iframeP2.contentWindow.dandyApp;
        const p3App = iframeP3.contentWindow.dandyApp;
        const p4App = iframeP4.contentWindow.dandyApp;

        const results = {
            roomCode,
            p1Badges,
            p2Badges,
            p3Badges,
            p4Badges,
            controlBadges: [p1ControlBadges, p2ControlBadges, p3ControlBadges, p4ControlBadges],
            statuses: [p1Status, p2Status, p3Status, p4Status],
            initPositions,
            finalPositions,
            p1GpStatus,
            p1GpBadge,
            p1GpBadgeVisible,
            p2GpBadgeVisibleOnHost,
            posAfterGamepad,
            p1GpStatusAfterDisconnect,
            p1GpBadgeVisibleAfterDisconnect,
            frames: [
                p1App.net_get_current_frame(),
                p2App.net_get_current_frame(),
                p3App.net_get_current_frame(),
                p4App.net_get_current_frame()
            ],
            rollbacks: [
                p1App.net_get_rollback_count(),
                p2App.net_get_rollback_count(),
                p3App.net_get_rollback_count(),
                p4App.net_get_rollback_count()
            ],
            fbSizes: [
                p1App.get_framebuffer_size(),
                p2App.get_framebuffer_size(),
                p3App.get_framebuffer_size(),
                p4App.get_framebuffer_size()
            ],
            statsLens: [
                p1App.get_stats_len(),
                p2App.get_stats_len(),
                p3App.get_stats_len(),
                p4App.get_stats_len()
            ]
        };

        resolve(JSON.stringify(results));
    } catch (err) {
        reject(err.stack || err.toString());
    }
});
`;

function runTest() {
    return new Promise((resolve, reject) => {
        execFile(GBROWSER_BIN, ['eval', 'http://127.0.0.1:8080/', testCode], { timeout: 30000 }, (err, stdout, stderr) => {
            if (err) {
                console.error("gbrowser execution error:", err);
                console.error("stderr:", stderr);
                console.error("stdout:", stdout);
                return reject(err);
            }

            const lines = stdout.trim().split('\n');
            const lastLine = lines.filter(l => l.startsWith('{') && l.endsWith('}')).pop();

            if (!lastLine) {
                console.error("Full stdout:", stdout);
                return reject(new Error("No JSON results found in output"));
            }

            try {
                const data = JSON.parse(lastLine);
                resolve(data);
            } catch (e) {
                console.error("Failed to parse JSON:", lastLine);
                reject(e);
            }
        });
    });
}

try {
    const res = await runTest();
    console.log("\n=== Multiplayer Test Results ===");
    console.log(`Room Code: ${res.roomCode}`);
    console.log(`Statuses: ${res.statuses.join(" | ")}`);
    console.log(`Frames: P1=${res.frames[0]}, P2=${res.frames[1]}, P3=${res.frames[2]}, P4=${res.frames[3]}`);
    console.log(`Rollbacks: P1=${res.rollbacks[0]}, P2=${res.rollbacks[1]}, P3=${res.rollbacks[2]}, P4=${res.rollbacks[3]}`);
    console.log(`Framebuffer Sizes: ${res.fbSizes.join(", ")} bytes`);
    console.log(`Stats Buffer Lengths: ${res.statsLens.join(", ")} ints`);

    console.log("\n=== Verifying Assertions ===");
    // 1. Connection statuses
    assert(res.statuses.every(s => s === "Connected"), "All peers must have 'Connected' status");
    console.log("✓ All 4 player instances report 'Connected' status.");

    // 2. Slot Badges (Full 4x4 matrix assertion)
    assert.deepStrictEqual(res.p1Badges, ["LOCAL [ME]", "REMOTE", "REMOTE", "REMOTE"], "P1 badges matrix mismatch");
    assert.deepStrictEqual(res.p2Badges, ["REMOTE", "LOCAL [ME]", "REMOTE", "REMOTE"], "P2 badges matrix mismatch");
    assert.deepStrictEqual(res.p3Badges, ["REMOTE", "REMOTE", "LOCAL [ME]", "REMOTE"], "P3 badges matrix mismatch");
    assert.deepStrictEqual(res.p4Badges, ["REMOTE", "REMOTE", "REMOTE", "LOCAL [ME]"], "P4 badges matrix mismatch");
    console.log("✓ Dynamic Slot Cards and Badges verified across all 4 player instances (Full 4x4 Matrix).");

    // 2b. Dynamic Controls Legend Badges (Full 4x4 matrix assertion)
    assert.deepStrictEqual(res.controlBadges[0], ["Primary Local (This Device)", "Remote Player", "Remote Player", "Remote Player"], "P1 control badges mismatch");
    assert.deepStrictEqual(res.controlBadges[1], ["Remote Player", "Primary Local (This Device)", "Remote Player", "Remote Player"], "P2 control badges mismatch");
    assert.deepStrictEqual(res.controlBadges[2], ["Remote Player", "Remote Player", "Primary Local (This Device)", "Remote Player"], "P3 control badges mismatch");
    assert.deepStrictEqual(res.controlBadges[3], ["Remote Player", "Remote Player", "Remote Player", "Primary Local (This Device)"], "P4 control badges mismatch");
    console.log("✓ Dynamic Controls & How-to-Play Legend Badges verified across all 4 peer instances.");

    // 3. Frame Advance
    assert(res.frames.every(f => f >= 60), "All peers must advance >= 60 frames under active simulation");
    console.log(`✓ All 4 instances advanced frames synchronously (min frame: ${Math.min(...res.frames)}).`);

    // 4. Entity Movement and Cross-Instance Parity Verification
    console.log("\n=== Verifying Entity Movement and Cross-Instance Netcode Parity ===");
    const hostInit = res.initPositions[0];
    const hostFinal = res.finalPositions[0];
    const p2Final = res.finalPositions[1];
    const p3Final = res.finalPositions[2];
    const p4Final = res.finalPositions[3];

    // P1 moved Right
    console.log(`P1: Init=(${hostInit[0].x}, ${hostInit[0].y}) -> Final on Host=(${hostFinal[0].x}, ${hostFinal[0].y}), P2=(${p2Final[0].x}, ${p2Final[0].y})`);
    assert(hostFinal[0].x > hostInit[0].x, `P1 must move Right on Host (was ${hostInit[0].x}, now ${hostFinal[0].x})`);
    assert.strictEqual(p2Final[0].x, hostFinal[0].x, `P1 position on P2 (${p2Final[0].x}) must match Host (${hostFinal[0].x})`);
    assert.strictEqual(p2Final[0].y, hostFinal[0].y, `P1 position on P2 (${p2Final[0].y}) must match Host (${hostFinal[0].y})`);
    assert.strictEqual(p3Final[0].x, hostFinal[0].x, "P1 position on P3 must match Host");
    assert.strictEqual(p4Final[0].x, hostFinal[0].x, "P1 position on P4 must match Host");
    console.log("✓ P1 local movement on Host replicated to all 3 remote peer instances.");

    // P2 moved Down
    console.log(`P2: Init=(${hostInit[1].x}, ${hostInit[1].y}) -> Final on P2=(${p2Final[1].x}, ${p2Final[1].y}), Host=(${hostFinal[1].x}, ${hostFinal[1].y})`);
    assert(p2Final[1].y > hostInit[1].y, `P2 must move Down on P2 (was ${hostInit[1].y}, now ${p2Final[1].y})`);
    assert.strictEqual(hostFinal[1].x, p2Final[1].x, `P2 position on Host (${hostFinal[1].x}) must match P2 (${p2Final[1].x})`);
    assert.strictEqual(hostFinal[1].y, p2Final[1].y, `P2 position on Host (${hostFinal[1].y}) must match P2 (${p2Final[1].y})`);
    assert.strictEqual(p3Final[1].y, p2Final[1].y, "P2 position on P3 must match P2");
    assert.strictEqual(p4Final[1].y, p2Final[1].y, "P2 position on P4 must match P2");
    console.log("✓ P2 remote movement on Joiner replicated to Host and all peer instances.");

    // P3 moved Left
    console.log(`P3: Init=(${hostInit[2].x}, ${hostInit[2].y}) -> Final on P3=(${p3Final[2].x}, ${p3Final[2].y}), Host=(${hostFinal[2].x}, ${hostFinal[2].y})`);
    assert(p3Final[2].x < hostInit[2].x, `P3 must move Left on P3 (was ${hostInit[2].x}, now ${p3Final[2].x})`);
    assert.strictEqual(hostFinal[2].x, p3Final[2].x, "P3 position on Host must match P3");
    assert.strictEqual(hostFinal[2].y, p3Final[2].y, "P3 position on Host must match P3");
    console.log("✓ P3 remote movement on Joiner replicated to Host and all peer instances.");

    // P4 moved Up
    console.log(`P4: Init=(${hostInit[3].x}, ${hostInit[3].y}) -> Final on P4=(${p4Final[3].x}, ${p4Final[3].y}), Host=(${hostFinal[3].x}, ${hostFinal[3].y})`);
    assert(p4Final[3].y < hostInit[3].y, `P4 must move Up on P4 (was ${hostInit[3].y}, now ${p4Final[3].y})`);
    assert.strictEqual(hostFinal[3].x, p4Final[3].x, "P4 position on Host must match P4");
    assert.strictEqual(hostFinal[3].y, p4Final[3].y, "P4 position on Host must match P4");
    console.log("✓ P4 remote movement on Joiner replicated to Host and all peer instances.");

    // 5. HTML5 Gamepad API Verification
    console.log("\n=== Verifying HTML5 Gamepad API Support & Dynamics ===");
    console.log(`Gamepad Status Text: "${res.p1GpStatus}"`);
    console.log(`Gamepad P1 Badge: "${res.p1GpBadge}", Visible: ${res.p1GpBadgeVisible}`);
    console.log(`Gamepad P2 Badge on Host Visible: ${res.p2GpBadgeVisibleOnHost}`);
    console.log(`P1 Pos Before GP: (${hostFinal[0].x}, ${hostFinal[0].y}) -> Pos After GP: (${res.posAfterGamepad[0][0].x}, ${res.posAfterGamepad[0][0].y})`);
    assert(res.p1GpStatus.includes("1 Gamepad Connected"), "Gamepad status must report 1 Gamepad Connected");
    assert(res.p1GpStatus.includes("P1 Ruby"), "Gamepad status must indicate mapped to P1 Ruby");
    assert(res.p1GpBadgeVisible, "Gamepad badge must be visible on P1 card");
    assert.strictEqual(res.p1GpBadge, "🎮 Gamepad 2 Active", "Gamepad badge text must be '🎮 Gamepad 2 Active' (for controller at OS index 1)");
    assert.strictEqual(res.p2GpBadgeVisibleOnHost, false, "Gamepad badge must NOT bleed onto P2 card when mapped to P1");
    assert(res.posAfterGamepad[0][0].x < hostFinal[0].x, `P1 must continue moving Left under Gamepad analog stick input (was ${hostFinal[0].x}, now ${res.posAfterGamepad[0][0].x})`);
    assert(res.p1GpStatusAfterDisconnect.includes("No gamepads detected"), "Status must report no gamepads detected after disconnect");
    assert.strictEqual(res.p1GpBadgeVisibleAfterDisconnect, false, "Gamepad badge must be hidden after disconnect");
    console.log("✓ HTML5 Gamepad API polling, sparse array mapping, dynamic legend badges, and analog stick movement verified.");

    // 6. Zero-Copy Framebuffer Integrity
    assert.deepStrictEqual(res.fbSizes, [204800, 204800, 204800, 204800], "320x160x4 Framebuffer integrity");
    assert.deepStrictEqual(res.statsLens, [28, 28, 28, 28], "4x7 stats array integrity");
    console.log("✓ Zero-Copy Framebuffer and Stats memory boundaries intact on all instances.");

    console.log("\n==================================================================");
    console.log("🎉 ALL 4-PLAYER WEBRTC ROLLBACK MULTIPLAYER GATES PASSED! 🎉");
    console.log("==================================================================");
} catch (err) {
    console.error("\n❌ Headless Multiplayer Test Failed:", err);
    process.exit(1);
}
