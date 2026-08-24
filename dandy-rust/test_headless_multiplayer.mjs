import { execFile } from 'child_process';
import assert from 'assert';
import path from 'path';

console.log("=== Dandy Dungeon Headless Multi-Browser WebRTC Multiplayer Test ===");

const GBROWSER_BIN = "/google/bin/releases/gemini-agents-gbrowser/gbrowser";

const testCode = `
new Promise(async (resolve, reject) => {
    try {
        console.log("[Test] 0. Inspecting Initial Welcome Modal & Progressive Disclosure Diagnostics...");
        const welcomeModal = document.getElementById("welcome-modal");
        const initialWelcomeVisible = welcomeModal && window.getComputedStyle(welcomeModal).display !== "none";
        const btnWelcomeLocal = document.getElementById("btn-welcome-local");
        const btnWelcomeHost = document.getElementById("btn-welcome-host");
        const btnWelcomeJoin = document.getElementById("btn-welcome-join");
        const has3WelcomeOptions = Boolean(btnWelcomeLocal && btnWelcomeHost && btnWelcomeJoin);

        const diagPanel = document.getElementById("diagnostics-panel");
        const initialDiagCollapsed = diagPanel ? !diagPanel.open : true;

        // Test Switch Mode button opening, Escape key closing, and Close button
        const btnSwitchMode = document.getElementById("btn-switch-mode");
        const btnCloseWelcome = document.getElementById("btn-close-welcome");
        let switchModeTestPassed = false;
        let escapeKeyTestPassed = false;
        let optionCardClickTestPassed = false;

        if (btnSwitchMode && btnCloseWelcome) {
            // 1. Open via Switch Mode button
            btnSwitchMode.click();
            await new Promise(r => setTimeout(r, 100));
            const openedWithCloseBtn = window.getComputedStyle(welcomeModal).display !== "none" && window.getComputedStyle(btnCloseWelcome).display !== "none";

            // 2. Close via Escape key
            window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
            await new Promise(r => setTimeout(r, 100));
            const closedWithEscape = window.getComputedStyle(welcomeModal).display === "none";
            escapeKeyTestPassed = openedWithCloseBtn && closedWithEscape;

            // 3. Re-open and close via Close button (✕)
            btnSwitchMode.click();
            await new Promise(r => setTimeout(r, 100));
            btnCloseWelcome.click();
            await new Promise(r => setTimeout(r, 100));
            const closedAfterClick = window.getComputedStyle(welcomeModal).display === "none";
            switchModeTestPassed = escapeKeyTestPassed && closedAfterClick;
        }

        // Test option card click delegator (clicking mode-opt-host card body opens host mode)
        const modeOptHost = document.getElementById("mode-opt-host");
        btnSwitchMode.click();
        await new Promise(r => setTimeout(r, 100));
        if (modeOptHost) {
            modeOptHost.click();
            await new Promise(r => setTimeout(r, 300));
            optionCardClickTestPassed = window.getComputedStyle(welcomeModal).display === "none";
        } else {
            btnWelcomeHost.click();
            await new Promise(r => setTimeout(r, 300));
        }

        const hostWelcomeVisibleAfterHost = window.getComputedStyle(welcomeModal).display === "none";

        const roomCode = document.getElementById("net-stat-room").textContent;
        console.log("[Test] Host created room:", roomCode);
        if (!roomCode || roomCode === "NONE") {
            throw new Error("Failed to create room code");
        }

        const hostHash = window.location.hash;
        const btnShareLink = document.getElementById("btn-share-link");
        const btnShareLinkText = btnShareLink?.textContent;
        const btnShareLinkVisible = btnShareLink && window.getComputedStyle(btnShareLink).display !== "none";
        const btnShowQr = document.getElementById("btn-show-qr");
        const btnShowQrVisible = btnShowQr && window.getComputedStyle(btnShowQr).display !== "none";

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

        const getShareInfo = (doc) => {
            const btn = doc?.getElementById("btn-share-link");
            const qr = doc?.getElementById("btn-show-qr");
            return {
                btnVisible: btn && window.getComputedStyle(btn).display !== "none",
                btnText: btn?.textContent,
                qrVisible: qr && window.getComputedStyle(qr).display !== "none"
            };
        };
        const p1ShareInfo = getShareInfo(document);
        const p2ShareInfo = getShareInfo(iframeP2.contentDocument);
        const p3ShareInfo = getShareInfo(iframeP3.contentDocument);
        const p4ShareInfo = getShareInfo(iframeP4.contentDocument);

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

        console.log("[Test] 8. Testing Bidirectional Difficulty Synchronization (Host <-> Joiners)...");
        // Test A: Joiner P2 changes difficulty dropdown to Deadly (3)
        const p2DifficultySelect = iframeP2.contentDocument?.getElementById("select-difficulty");
        if (p2DifficultySelect) {
            p2DifficultySelect.value = "3";
            p2DifficultySelect.dispatchEvent(new Event("change"));
        }
        await waitFor(() => {
            const hostDiffVal = window.dandyApp?.get_difficulty();
            const hostSelectVal = document.getElementById("select-difficulty")?.value;
            const p3DiffVal = iframeP3.contentWindow?.dandyApp?.get_difficulty();
            const p3SelectVal = iframeP3.contentDocument?.getElementById("select-difficulty")?.value;
            const p4DiffVal = iframeP4.contentWindow?.dandyApp?.get_difficulty();
            const p4SelectVal = iframeP4.contentDocument?.getElementById("select-difficulty")?.value;
            return hostDiffVal === 3 && hostSelectVal === "3" &&
                   p3DiffVal === 3 && p3SelectVal === "3" &&
                   p4DiffVal === 3 && p4SelectVal === "3";
        }, 5000, "Joiner P2 difficulty change propagating to Host, P3, and P4");

        const diffAfterJoinerChange = {
            hostVal: document.getElementById("select-difficulty")?.value,
            hostApp: window.dandyApp?.get_difficulty(),
            p2Val: iframeP2.contentDocument?.getElementById("select-difficulty")?.value,
            p2App: iframeP2.contentWindow?.dandyApp?.get_difficulty(),
            p3Val: iframeP3.contentDocument?.getElementById("select-difficulty")?.value,
            p3App: iframeP3.contentWindow?.dandyApp?.get_difficulty(),
            p4Val: iframeP4.contentDocument?.getElementById("select-difficulty")?.value,
            p4App: iframeP4.contentWindow?.dandyApp?.get_difficulty()
        };

        // Test B: Host changes difficulty to Trivial (0)
        const hostDifficultySelect = document.getElementById("select-difficulty");
        if (hostDifficultySelect) {
            hostDifficultySelect.value = "0";
            hostDifficultySelect.dispatchEvent(new Event("change"));
        }
        await waitFor(() => {
            const p2DiffVal = iframeP2.contentWindow?.dandyApp?.get_difficulty();
            const p2SelectVal = iframeP2.contentDocument?.getElementById("select-difficulty")?.value;
            const p3DiffVal = iframeP3.contentWindow?.dandyApp?.get_difficulty();
            const p3SelectVal = iframeP3.contentDocument?.getElementById("select-difficulty")?.value;
            const p4DiffVal = iframeP4.contentWindow?.dandyApp?.get_difficulty();
            const p4SelectVal = iframeP4.contentDocument?.getElementById("select-difficulty")?.value;
            return p2DiffVal === 0 && p2SelectVal === "0" &&
                   p3DiffVal === 0 && p3SelectVal === "0" &&
                   p4DiffVal === 0 && p4SelectVal === "0";
        }, 5000, "Host difficulty change propagating to all joiners");

        const diffAfterHostChange = {
            hostVal: document.getElementById("select-difficulty")?.value,
            hostApp: window.dandyApp?.get_difficulty(),
            p2Val: iframeP2.contentDocument?.getElementById("select-difficulty")?.value,
            p2App: iframeP2.contentWindow?.dandyApp?.get_difficulty(),
            p3Val: iframeP3.contentDocument?.getElementById("select-difficulty")?.value,
            p3App: iframeP3.contentWindow?.dandyApp?.get_difficulty(),
            p4Val: iframeP4.contentDocument?.getElementById("select-difficulty")?.value,
            p4App: iframeP4.contentWindow?.dandyApp?.get_difficulty()
        };

        // Reset difficulty back to Easy (1)
        if (hostDifficultySelect) {
            hostDifficultySelect.value = "1";
            hostDifficultySelect.dispatchEvent(new Event("change"));
        }
        await waitFor(() => {
            return window.dandyApp?.get_difficulty() === 1 &&
                   iframeP2.contentWindow?.dandyApp?.get_difficulty() === 1 &&
                   iframeP3.contentWindow?.dandyApp?.get_difficulty() === 1 &&
                   iframeP4.contentWindow?.dandyApp?.get_difficulty() === 1;
        }, 5000, "Reset difficulty back to Easy");

        console.log("[Test] 8. Inspecting 32-bit state checksums across all 4 peers in mesh...");
        const commonFrame = Math.min(
            window.dandyApp.net_get_confirmed_frame(),
            iframeP2.contentWindow.dandyApp.net_get_confirmed_frame(),
            iframeP3.contentWindow.dandyApp.net_get_confirmed_frame(),
            iframeP4.contentWindow.dandyApp.net_get_confirmed_frame()
        );
        const initialChecksums = [
            window.dandyApp.net_get_checksum_at_frame(commonFrame),
            iframeP2.contentWindow.dandyApp.net_get_checksum_at_frame(commonFrame),
            iframeP3.contentWindow.dandyApp.net_get_checksum_at_frame(commonFrame),
            iframeP4.contentWindow.dandyApp.net_get_checksum_at_frame(commonFrame)
        ];

        console.log("[Test] 9. Simulating live desync injection and automatic healing via PKT_RESYNC_REQ and PKT_STATE_SYNC...");
        const p3JoinerApp = iframeP3.contentWindow?.dandyApp;
        const p3ChecksumBeforeDesync = p3JoinerApp?.net_get_checksum_at_frame(commonFrame);
        // Artificially desync P3 Joiner by ticking local app directly
        if (p3JoinerApp) {
            p3JoinerApp.set_action(2, 0, true);
            p3JoinerApp.tick();
            p3JoinerApp.tick();
            p3JoinerApp.set_action(2, 0, false);
        }
        const p3ChecksumAfterDesync = p3JoinerApp?.get_state_checksum();
        const hostChecksumDuringDesync = window.dandyApp?.get_state_checksum();

        // Wait for automatic resync healing (Host delivers authoritative state sync every 2s / 120 frames or via PKT_RESYNC_REQ)
        await waitFor(() => {
            const hF = window.dandyApp.net_get_confirmed_frame();
            const p3F = iframeP3.contentWindow.dandyApp.net_get_confirmed_frame();
            const targetF = Math.min(hF, p3F);
            if (targetF <= commonFrame) return false;
            const hCs = window.dandyApp.net_get_checksum_at_frame(targetF);
            const p3Cs = iframeP3.contentWindow.dandyApp.net_get_checksum_at_frame(targetF);
            return hCs !== 0 && hCs === p3Cs;
        }, 5000, "Automatic desync healing on Joiner P3");

        const latestConfirmedF = Math.min(
            window.dandyApp.net_get_confirmed_frame(),
            iframeP3.contentWindow.dandyApp.net_get_confirmed_frame()
        );
        const p3ChecksumAfterHeal = iframeP3.contentWindow.dandyApp.net_get_checksum_at_frame(latestConfirmedF);
        const hostChecksumAfterHeal = window.dandyApp.net_get_checksum_at_frame(latestConfirmedF);

        console.log("[Test] 8. Simulating 5th player join attempt against full 4/4 room...");
        const iframeP5 = spawnJoiner("P5_Attempt", "#room=" + roomCode);

        await waitFor(() => {
            const p5Doc = iframeP5.contentDocument;
            if (!p5Doc) return false;
            const roomFullOverlay = p5Doc.getElementById("room-full-overlay");
            const connectingOverlay = p5Doc.getElementById("connecting-overlay");
            const statusEl = p5Doc.getElementById("net-stat-status");
            const isFullOverlayVisible = roomFullOverlay && window.getComputedStyle(roomFullOverlay).display !== "none";
            const isConnectingHidden = connectingOverlay && window.getComputedStyle(connectingOverlay).display === "none";
            const isStatusRoomFull = statusEl && statusEl.textContent.includes("Room Full (4/4)");
            return isFullOverlayVisible && isConnectingHidden && isStatusRoomFull;
        }, 10000, "5th player room-full rejection and error state transition");

        const p5Doc = iframeP5.contentDocument;
        const p5RoomFullVisible = window.getComputedStyle(p5Doc.getElementById("room-full-overlay")).display !== "none";
        const p5ConnectingHidden = window.getComputedStyle(p5Doc.getElementById("connecting-overlay")).display === "none";
        const p5Status = p5Doc.getElementById("net-stat-status")?.textContent;
        const p5Role = p5Doc.getElementById("net-stat-role")?.textContent;
        const p5Message = p5Doc.getElementById("room-full-message")?.textContent;
        const p5Badges = [1, 2, 3, 4].map(i => p5Doc.getElementById("slot-badge-p" + i)?.textContent);

        const btnPlayLocal = p5Doc.getElementById("btn-full-play-local");
        const btnHostRoom = p5Doc.getElementById("btn-full-host-room");
        const btnTryAgain = p5Doc.getElementById("btn-full-try-again");
        const p5HasActionButtons = Boolean(btnPlayLocal && btnHostRoom && btnTryAgain);

        // Test clicking "Play Local" on rejected instance to ensure clean recovery
        btnPlayLocal.click();
        await new Promise(r => setTimeout(r, 200));
        const p5RecoveredToLocal = window.getComputedStyle(p5Doc.getElementById("room-full-overlay")).display === "none" &&
                                  p5Doc.getElementById("net-stat-role")?.textContent === "LOCAL" &&
                                  p5Doc.getElementById("net-stat-status")?.textContent === "Ready";
        const p5HashAfterLocal = iframeP5.contentWindow?.location.hash;

        console.log("[Test] 8b. Simulating Signaling and DataChannel Protocol Version Mismatch Guards...");
        // 1. Signaling layer: Host receives join_request with mismatched protocolVersion (v99)
        const mismatchPeerId = "MISMATCH_PEER_99";
        const sigBc = new BroadcastChannel("dandy_room_" + roomCode);
        let hostRejectionResponse = null;
        sigBc.onmessage = (e) => {
            if (e.data && e.data.type === "join_rejected" && (e.data.recipientId === mismatchPeerId || e.data.targetId === mismatchPeerId)) {
                hostRejectionResponse = e.data;
            }
        };
        sigBc.postMessage({
            roomId: roomCode,
            senderId: mismatchPeerId,
            type: "join_request",
            appId: "dandy-dungeon",
            protocolVersion: 99
        });
        await waitFor(() => hostRejectionResponse !== null, 5000, "Host rejecting version 99 join_request over signaling");

        const hostRejectionReason = hostRejectionResponse?.reason;
        const hostRejectionMsg = hostRejectionResponse?.message;
        const hostRejectionHostVer = hostRejectionResponse?.hostVersion;
        const hostRejectionClientVer = hostRejectionResponse?.clientVersion;

        // 2. Client UX: Joiner receives join_rejected with version_mismatch
        const iframeMismatch = spawnJoiner("Mismatch_Joiner", "#room=" + roomCode);
        await waitFor(() => {
            const doc = iframeMismatch.contentDocument;
            const win = iframeMismatch.contentWindow;
            return doc && doc.getElementById("connecting-overlay") !== null && win?.myPeerId && win?.dandyApp;
        }, 5000, "Mismatch Joiner iframe load");

        const mismatchDoc = iframeMismatch.contentDocument;
        const mismatchWin = iframeMismatch.contentWindow;

        // Send simulated version mismatch rejection to this iframe's peer
        sigBc.postMessage({
            roomId: roomCode,
            senderId: "HOST",
            recipientId: mismatchWin.myPeerId,
            targetId: mismatchWin.myPeerId,
            type: "join_rejected",
            reason: "version_mismatch",
            message: "Protocol version mismatch: Host is v1, Client is v99. Please reload to update.",
            hostVersion: 1,
            clientVersion: 99
        });

        await waitFor(() => {
            const overlay = mismatchDoc.getElementById("version-mismatch-overlay");
            const connecting = mismatchDoc.getElementById("connecting-overlay");
            const statusEl = mismatchDoc.getElementById("net-stat-status");
            const isOverlayVisible = overlay && window.getComputedStyle(overlay).display !== "none";
            const isConnectingHidden = connecting && window.getComputedStyle(connecting).display === "none";
            const isStatusMismatch = statusEl && statusEl.textContent === "Version Mismatch";
            return isOverlayVisible && isConnectingHidden && isStatusMismatch;
        }, 5000, "Version Mismatch overlay rendering on Joiner");

        const mismatchOverlayVisible = window.getComputedStyle(mismatchDoc.getElementById("version-mismatch-overlay")).display !== "none";
        const mismatchConnectingHidden = window.getComputedStyle(mismatchDoc.getElementById("connecting-overlay")).display === "none";
        const mismatchStatus = mismatchDoc.getElementById("net-stat-status")?.textContent;
        const mismatchRole = mismatchDoc.getElementById("net-stat-role")?.textContent;
        const mismatchHostText = mismatchDoc.getElementById("version-host-val")?.textContent;
        const mismatchClientText = mismatchDoc.getElementById("version-client-val")?.textContent;
        const mismatchMsgText = mismatchDoc.getElementById("version-mismatch-message")?.textContent;

        const btnMismatchReload = mismatchDoc.getElementById("btn-version-reload");
        const btnMismatchPlayLocal = mismatchDoc.getElementById("btn-version-play-local");
        const mismatchHasActionButtons = Boolean(btnMismatchReload && btnMismatchPlayLocal);

        // Test clicking "Play Local" on version mismatch instance to ensure clean recovery
        btnMismatchPlayLocal.click();
        await new Promise(r => setTimeout(r, 200));
        const mismatchRecoveredToLocal = window.getComputedStyle(mismatchDoc.getElementById("version-mismatch-overlay")).display === "none" &&
                                          mismatchDoc.getElementById("net-stat-role")?.textContent === "LOCAL" &&
                                          mismatchDoc.getElementById("net-stat-status")?.textContent === "Ready";

        // 9. Host and Joiner Refresh Persistence Tests
        console.log("[Test] 9. Simulating Host Refresh persistence with #host= hash...");
        const iframeHostRefresh = spawnJoiner("Host_Refresh", "#host=DANDY-7777");
        await waitFor(() => {
            const doc = iframeHostRefresh.contentDocument;
            if (!doc) return false;
            const roleEl = doc.getElementById("net-stat-role");
            const roomEl = doc.getElementById("net-stat-room");
            const shareBtn = doc.getElementById("btn-share-link");
            return roleEl && roleEl.textContent === "P1 RUBY (HOST)" &&
                   roomEl && roomEl.textContent === "DANDY-7777" &&
                   shareBtn && window.getComputedStyle(shareBtn).display !== "none";
        }, 10000, "Host refresh persistence on #host=DANDY-7777");

        const hostRefreshDoc = iframeHostRefresh.contentDocument;
        const hostRefreshRole = hostRefreshDoc.getElementById("net-stat-role")?.textContent;
        const hostRefreshRoom = hostRefreshDoc.getElementById("net-stat-room")?.textContent;
        const hostRefreshHash = iframeHostRefresh.contentWindow?.location.hash;
        const hostRefreshModalHidden = window.getComputedStyle(hostRefreshDoc.getElementById("welcome-modal")).display === "none";
        const hostRefreshP1Local = iframeHostRefresh.contentWindow?.dandyApp?.net_is_local_player(0);

        console.log("[Test] 10. Simulating Joiner Refresh persistence with #join= hash...");
        const iframeJoinerRefresh = spawnJoiner("Joiner_Refresh", "#join=DANDY-8888");
        await waitFor(() => {
            const doc = iframeJoinerRefresh.contentDocument;
            if (!doc) return false;
            const roleEl = doc.getElementById("net-stat-role");
            const roomEl = doc.getElementById("net-stat-room");
            return roleEl && roleEl.textContent === "CONNECTING..." &&
                   roomEl && roomEl.textContent === "DANDY-8888";
        }, 10000, "Joiner refresh persistence on #join=DANDY-8888");

        const joinerRefreshDoc = iframeJoinerRefresh.contentDocument;
        const joinerRefreshRole = joinerRefreshDoc.getElementById("net-stat-role")?.textContent;
        const joinerRefreshRoom = joinerRefreshDoc.getElementById("net-stat-room")?.textContent;
        const joinerRefreshHash = iframeJoinerRefresh.contentWindow?.location.hash;
        const joinerRefreshModalHidden = window.getComputedStyle(joinerRefreshDoc.getElementById("welcome-modal")).display === "none";
        const joinerRefreshShareInfo = getShareInfo(joinerRefreshDoc);

        console.log("[Test] 11. Simulating Bare Room Code URL Join (#DANDY-6666)...");
        const iframeBareJoin = spawnJoiner("Bare_Join", "#DANDY-6666");
        await waitFor(() => {
            const doc = iframeBareJoin.contentDocument;
            if (!doc) return false;
            const roleEl = doc.getElementById("net-stat-role");
            const roomEl = doc.getElementById("net-stat-room");
            return roleEl && roleEl.textContent === "CONNECTING..." &&
                   roomEl && roomEl.textContent === "DANDY-6666";
        }, 10000, "Bare room code URL join on #DANDY-6666");

        const bareJoinDoc = iframeBareJoin.contentDocument;
        const bareJoinRole = bareJoinDoc.getElementById("net-stat-role")?.textContent;
        const bareJoinRoom = bareJoinDoc.getElementById("net-stat-room")?.textContent;
        const bareJoinHash = iframeBareJoin.contentWindow?.location.hash;
        const bareJoinShareInfo = getShareInfo(bareJoinDoc);

        console.log("[Test] 12. Simulating Query-Style Host URL (#room=DANDY-9999&role=host)...");
        const iframeQueryHost = spawnJoiner("Query_Host", "#room=DANDY-9999&role=host");
        await waitFor(() => {
            const doc = iframeQueryHost.contentDocument;
            if (!doc) return false;
            const roleEl = doc.getElementById("net-stat-role");
            const roomEl = doc.getElementById("net-stat-room");
            return roleEl && roleEl.textContent === "P1 RUBY (HOST)" &&
                   roomEl && roomEl.textContent === "DANDY-9999";
        }, 10000, "Query-style host URL persistence on #room=DANDY-9999&role=host");

        const queryHostDoc = iframeQueryHost.contentDocument;
        const queryHostRole = queryHostDoc.getElementById("net-stat-role")?.textContent;
        const queryHostRoom = queryHostDoc.getElementById("net-stat-room")?.textContent;

        console.log("[Test] 13. Simulating Invalid #host=NONE Hash Filter...");
        const iframeInvalidNone = spawnJoiner("Invalid_None", "#host=NONE");
        await new Promise(r => setTimeout(r, 600));
        const invalidNoneDoc = iframeInvalidNone.contentDocument;
        const invalidNoneRoom = invalidNoneDoc?.getElementById("net-stat-room")?.textContent;
        const invalidNoneWelcomeVisible = window.getComputedStyle(invalidNoneDoc.getElementById("welcome-modal")).display !== "none";

        console.log("[Test] 14. Simulating Cross-Browser/Cross-Machine Isolated MQTT Signaling (BroadcastChannel and localStorage disabled)...");
        const mqttRoomCode = "DANDY-M" + Math.random().toString(36).substr(2, 4).toUpperCase();
        const iframeMqttHost = spawnJoiner("MQTT_Host", "?disable_local_sig=1#host=" + mqttRoomCode);
        const iframeMqttJoiner = spawnJoiner("MQTT_Joiner", "?disable_local_sig=1#room=" + mqttRoomCode);

        await waitFor(() => {
            const hostApp = iframeMqttHost.contentWindow?.dandyApp;
            const joinerApp = iframeMqttJoiner.contentWindow?.dandyApp;
            if (!hostApp || !joinerApp) return false;
            return hostApp.net_is_player_joined(0) && hostApp.net_is_player_joined(1) &&
                   joinerApp.net_is_player_joined(0) && joinerApp.net_is_player_joined(1);
        }, 20000, "Isolated MQTT 2-player WebRTC DataChannel connection over public broker");

        const mqttHostDoc = iframeMqttHost.contentDocument;
        const mqttJoinerDoc = iframeMqttJoiner.contentDocument;
        const mqttHostStatus = mqttHostDoc?.getElementById("net-stat-status")?.textContent;
        const mqttJoinerStatus = mqttJoinerDoc?.getElementById("net-stat-status")?.textContent;
        const mqttHostRole = mqttHostDoc?.getElementById("net-stat-role")?.textContent;
        const mqttJoinerRole = mqttJoinerDoc?.getElementById("net-stat-role")?.textContent;

        // Verify entity movement replication across the pure MQTT connection
        const mqttHostInitX = iframeMqttHost.contentWindow.dandyApp.get_player_x(0);
        iframeMqttHost.contentWindow.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }));
        await new Promise(r => setTimeout(r, 450));
        iframeMqttHost.contentWindow.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowRight" }));
        await new Promise(r => setTimeout(r, 200));

        const mqttHostFinalX = iframeMqttHost.contentWindow.dandyApp.get_player_x(0);
        const mqttJoinerSeenX = iframeMqttJoiner.contentWindow.dandyApp.get_player_x(0);

        const mqttCommonFrame = Math.min(
            iframeMqttHost.contentWindow.dandyApp.net_get_confirmed_frame(),
            iframeMqttJoiner.contentWindow.dandyApp.net_get_confirmed_frame()
        );
        const mqttHostChecksum = iframeMqttHost.contentWindow.dandyApp.net_get_checksum_at_frame(mqttCommonFrame);
        const mqttJoinerChecksum = iframeMqttJoiner.contentWindow.dandyApp.net_get_checksum_at_frame(mqttCommonFrame);

        const results = {
            initialWelcomeVisible,
            has3WelcomeOptions,
            initialDiagCollapsed,
            switchModeTestPassed,
            escapeKeyTestPassed,
            optionCardClickTestPassed,
            hostWelcomeVisibleAfterHost,
            roomCode,
            hostHash,
            btnShareLinkText,
            btnShareLinkVisible,
            btnShowQrVisible,
            p1ShareInfo,
            p2ShareInfo,
            p3ShareInfo,
            p4ShareInfo,
            joinerRefreshShareInfo,
            bareJoinShareInfo,
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
            diffAfterJoinerChange,
            diffAfterHostChange,
            initialChecksums,
            p3ChecksumBeforeDesync,
            p3ChecksumAfterDesync,
            hostChecksumDuringDesync,
            p3ChecksumAfterHeal,
            hostChecksumAfterHeal,
            p5RoomFullVisible,
            p5ConnectingHidden,
            p5Status,
            p5Role,
            p5Message,
            p5Badges,
            p5HasActionButtons,
            p5RecoveredToLocal,
            p5HashAfterLocal,
            hostRejectionReason,
            hostRejectionMsg,
            hostRejectionHostVer,
            hostRejectionClientVer,
            mismatchOverlayVisible,
            mismatchConnectingHidden,
            mismatchStatus,
            mismatchRole,
            mismatchHostText,
            mismatchClientText,
            mismatchMsgText,
            mismatchHasActionButtons,
            mismatchRecoveredToLocal,
            hostRefreshRole,
            hostRefreshRoom,
            hostRefreshHash,
            hostRefreshModalHidden,
            hostRefreshP1Local,
            joinerRefreshRole,
            joinerRefreshRoom,
            joinerRefreshHash,
            joinerRefreshModalHidden,
            bareJoinRole,
            bareJoinRoom,
            bareJoinHash,
            queryHostRole,
            queryHostRoom,
            invalidNoneRoom,
            invalidNoneWelcomeVisible,
            mqttRoomCode,
            mqttHostStatus,
            mqttJoinerStatus,
            mqttHostRole,
            mqttJoinerRole,
            mqttHostInitX,
            mqttHostFinalX,
            mqttJoinerSeenX,
            mqttHostChecksum,
            mqttJoinerChecksum,
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
        resolve(JSON.stringify({ error: err.stack || err.toString() }));
    }
});
`;

function runTest() {
    return new Promise((resolve, reject) => {
        execFile(GBROWSER_BIN, ['eval', 'http://127.0.0.1:8080/', testCode], { timeout: 60000 }, (err, stdout, stderr) => {
            const lines = (stdout || "").trim().split('\n');
            const lastLine = lines.filter(l => l.startsWith('{') && l.endsWith('}')).pop();

            if (lastLine) {
                try {
                    const data = JSON.parse(lastLine);
                    return resolve(data);
                } catch (e) {}
            }

            if (err) {
                console.error("gbrowser execution failed!");
                if (stderr) console.error("stderr:", stderr);
                if (stdout) console.error("stdout:", stdout);
                return reject(new Error(err.message || String(err)));
            }

            if (!lastLine) {
                console.error("Full stdout:", stdout);
                return reject(new Error("No JSON results found in output"));
            }
        });
    });
}

try {
    const res = await runTest();
    if (res.error) {
        console.error("Test code failed inside gbrowser:\n", res.error);
        process.exit(1);
    }
    console.log("\n=== Multiplayer Test Results ===");
    console.log(`Room Code: ${res.roomCode}`);
    console.log(`Statuses: ${res.statuses.join(" | ")}`);
    console.log(`Frames: P1=${res.frames[0]}, P2=${res.frames[1]}, P3=${res.frames[2]}, P4=${res.frames[3]}`);
    console.log(`Rollbacks: P1=${res.rollbacks[0]}, P2=${res.rollbacks[1]}, P3=${res.rollbacks[2]}, P4=${res.rollbacks[3]}`);
    console.log(`Framebuffer Sizes: ${res.fbSizes.join(", ")} bytes`);
    console.log(`Stats Buffer Lengths: ${res.statsLens.join(", ")} ints`);

    console.log("\n=== Verifying Assertions ===");
    // 0. Welcome Modal & Progressive Disclosure
    assert.strictEqual(res.initialWelcomeVisible, true, "Welcome modal must be visible on root load without room hash");
    assert.strictEqual(res.has3WelcomeOptions, true, "Welcome modal must contain Play Local, Host Online, and Join Online options");
    assert.strictEqual(res.initialDiagCollapsed, true, "Diagnostics details panel must be collapsed by default");
    assert.strictEqual(res.switchModeTestPassed, true, "Switch Mode button must open welcome modal with close button");
    assert.strictEqual(res.escapeKeyTestPassed, true, "Escape key must dismiss modal when close button is visible");
    assert.strictEqual(res.optionCardClickTestPassed, true, "Clicking option card body must trigger mode action");
    assert.strictEqual(res.hostWelcomeVisibleAfterHost, true, "Welcome modal must dismiss after hosting room");
    console.log("✓ Welcome Modal flow, 3-option play picker, Mode Switcher, Escape key, card delegators, and Progressive Diagnostics verified.");

    // 0b. Stateful URL & Host/Joiner Refresh Persistence Verification
    console.log("\n=== Verifying Stateful URL & Refresh Persistence ===");
    assert.strictEqual(res.hostHash, "#host=" + res.roomCode, "Host browser URL hash must be #host=DANDY-XXXX");
    assert.strictEqual(res.btnShareLinkVisible, true, "Share link button must be visible on Host");
    assert.strictEqual(res.btnShareLinkText, "📋 Copy Link (" + res.roomCode + ")", "Share link text must match room code");
    assert.strictEqual(res.btnShowQrVisible, true, "QR code button must be visible on Host");

    // Verify Copy Link and QR Code buttons across all Joiners in active 4-player mesh
    assert.strictEqual(res.p2ShareInfo.btnVisible, true, "Share link button must be visible on Joiner P2");
    assert.strictEqual(res.p2ShareInfo.btnText, "📋 Copy Link (" + res.roomCode + ")", "Share link text on P2 must match room code");
    assert.strictEqual(res.p2ShareInfo.qrVisible, true, "QR code button must be visible on Joiner P2");
    assert.strictEqual(res.p3ShareInfo.btnVisible, true, "Share link button must be visible on Joiner P3");
    assert.strictEqual(res.p3ShareInfo.btnText, "📋 Copy Link (" + res.roomCode + ")", "Share link text on P3 must match room code");
    assert.strictEqual(res.p4ShareInfo.btnVisible, true, "Share link button must be visible on Joiner P4");
    assert.strictEqual(res.p4ShareInfo.btnText, "📋 Copy Link (" + res.roomCode + ")", "Share link text on P4 must match room code");

    assert.strictEqual(res.hostRefreshRole, "P1 RUBY (HOST)", "Reloading with #host=DANDY-XXXX must resume Host role");
    assert.strictEqual(res.hostRefreshRoom, "DANDY-7777", "Host refresh must preserve room ID");
    assert.strictEqual(res.hostRefreshHash, "#host=DANDY-7777", "Host refresh must retain #host= URL hash");
    assert.strictEqual(res.hostRefreshModalHidden, true, "Welcome modal must be hidden when loading with #host= hash");
    assert.strictEqual(res.hostRefreshP1Local, true, "Host instance must assign P1 Ruby as local player");
    assert.strictEqual(res.joinerRefreshRole, "CONNECTING...", "Reloading with joiner hash must boot into Joiner role");
    assert.strictEqual(res.joinerRefreshRoom, "DANDY-8888", "Joiner refresh must preserve room ID");
    assert.strictEqual(res.joinerRefreshHash, "#room=DANDY-8888", "Joiner URL hash must be normalized to #room=DANDY-XXXX");
    assert.strictEqual(res.joinerRefreshModalHidden, true, "Welcome modal must be hidden when loading with joiner hash");
    assert.strictEqual(res.joinerRefreshShareInfo.btnVisible, true, "Share link button must be visible on Joiner Refresh");
    assert.strictEqual(res.joinerRefreshShareInfo.btnText, "📋 Copy Link (DANDY-8888)", "Share link text on Joiner Refresh must be DANDY-8888");
    assert.strictEqual(res.joinerRefreshShareInfo.qrVisible, true, "QR code button must be visible on Joiner Refresh");
    assert.strictEqual(res.bareJoinRole, "CONNECTING...", "Bare #DANDY-6666 URL must boot into Joiner role");
    assert.strictEqual(res.bareJoinRoom, "DANDY-6666", "Bare room code URL must connect to DANDY-6666");
    assert.strictEqual(res.bareJoinHash, "#room=DANDY-6666", "Bare room code URL must normalize hash to #room=DANDY-6666");
    assert.strictEqual(res.bareJoinShareInfo.btnVisible, true, "Share link button must be visible on Bare Join");
    assert.strictEqual(res.bareJoinShareInfo.btnText, "📋 Copy Link (DANDY-6666)", "Share link text on Bare Join must be DANDY-6666");
    assert.strictEqual(res.bareJoinShareInfo.qrVisible, true, "QR code button must be visible on Bare Join");
    assert.strictEqual(res.queryHostRole, "P1 RUBY (HOST)", "Query style #room=DANDY-9999&role=host must boot into Host role");
    assert.strictEqual(res.queryHostRoom, "DANDY-9999", "Query style host room must preserve room ID DANDY-9999");
    assert.strictEqual(res.invalidNoneRoom, "NONE", "Invalid #host=NONE hash must not set active room");
    assert.strictEqual(res.invalidNoneWelcomeVisible, true, "Invalid #host=NONE hash must default to showing Welcome modal");
    assert.strictEqual(res.p5HashAfterLocal, "", "Switching to Local mode must clear the URL hash");
    console.log("✓ Stateful URL hashing, #host= vs #room= role reflection, Share links, QR code, and Host/Joiner refresh persistence verified.");

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

    // 6. Bidirectional Difficulty Synchronization (Host <-> Joiners)
    console.log("\n=== Verifying Bidirectional Difficulty Synchronization ===");
    console.log(`Joiner P2 Change: Host UI=${res.diffAfterJoinerChange.hostVal} (app=${res.diffAfterJoinerChange.hostApp}), P2=${res.diffAfterJoinerChange.p2Val}, P3=${res.diffAfterJoinerChange.p3Val}, P4=${res.diffAfterJoinerChange.p4Val}`);
    assert.strictEqual(res.diffAfterJoinerChange.hostVal, "3", "Host select-difficulty value must update to '3' when Joiner changes to Deadly");
    assert.strictEqual(res.diffAfterJoinerChange.hostApp, 3, "Host app difficulty must update to 3 (Deadly) when Joiner changes");
    assert.strictEqual(res.diffAfterJoinerChange.p3Val, "3", "P3 select-difficulty must update to '3' via Host relay");
    assert.strictEqual(res.diffAfterJoinerChange.p3App, 3, "P3 app difficulty must update to 3 via Host relay");
    assert.strictEqual(res.diffAfterJoinerChange.p4Val, "3", "P4 select-difficulty must update to '3' via Host relay");
    assert.strictEqual(res.diffAfterJoinerChange.p4App, 3, "P4 app difficulty must update to 3 via Host relay");
    console.log("✓ Joiner difficulty change correctly updated Host UI and relayed across 4-player mesh.");

    console.log(`Host Change: Host UI=${res.diffAfterHostChange.hostVal} (app=${res.diffAfterHostChange.hostApp}), P2=${res.diffAfterHostChange.p2Val}, P3=${res.diffAfterHostChange.p3Val}, P4=${res.diffAfterHostChange.p4Val}`);
    assert.strictEqual(res.diffAfterHostChange.p2Val, "0", "P2 select-difficulty must update to '0' when Host changes to Trivial");
    assert.strictEqual(res.diffAfterHostChange.p2App, 0, "P2 app difficulty must update to 0 (Trivial)");
    assert.strictEqual(res.diffAfterHostChange.p3Val, "0", "P3 select-difficulty must update to '0' when Host changes to Trivial");
    assert.strictEqual(res.diffAfterHostChange.p3App, 0, "P3 app difficulty must update to 0 (Trivial)");
    assert.strictEqual(res.diffAfterHostChange.p4Val, "0", "P4 select-difficulty must update to '0' when Host changes to Trivial");
    assert.strictEqual(res.diffAfterHostChange.p4App, 0, "P4 app difficulty must update to 0 (Trivial)");
    console.log("✓ Host difficulty change correctly broadcast to all joiner peers.");

    // 7. Deterministic State Checksums and Automatic Desync Healing Verification
    console.log("\n=== Verifying Deterministic State Checksums and Automatic Desync Healing ===");
    console.log(`Initial Mesh Checksums: P1=0x${res.initialChecksums[0].toString(16)}, P2=0x${res.initialChecksums[1].toString(16)}, P3=0x${res.initialChecksums[2].toString(16)}, P4=0x${res.initialChecksums[3].toString(16)}`);
    assert.strictEqual(res.initialChecksums[0], res.initialChecksums[1], "P1 and P2 initial checksums must match");
    assert.strictEqual(res.initialChecksums[0], res.initialChecksums[2], "P1 and P3 initial checksums must match");
    assert.strictEqual(res.initialChecksums[0], res.initialChecksums[3], "P1 and P4 initial checksums must match");
    console.log("✓ Full 4-player mesh lockstep checksum parity verified (100% bit-identical).");

    console.log(`Injected Desync on P3: Host=0x${res.hostChecksumDuringDesync.toString(16)} vs P3=0x${res.p3ChecksumAfterDesync.toString(16)}`);
    assert.notStrictEqual(res.hostChecksumDuringDesync, res.p3ChecksumAfterDesync, "Injected desync on P3 must alter checksum");
    console.log(`Healed Checksum on P3: 0x${res.p3ChecksumAfterHeal.toString(16)} (Host: 0x${res.hostChecksumAfterHeal.toString(16)})`);
    assert.strictEqual(res.p3ChecksumAfterHeal, res.hostChecksumAfterHeal, "Authoritative state sync must restore P3 Joiner to 100% lockstep parity with Host");
    console.log("✓ Automatic desync detection and seamless state healing over WebRTC mesh verified.");

    // 8. Zero-Copy Framebuffer Integrity
    assert.deepStrictEqual(res.fbSizes, [204800, 204800, 204800, 204800], "320x160x4 Framebuffer integrity");
    assert.deepStrictEqual(res.statsLens, [28, 28, 28, 28], "4x7 stats array integrity");
    console.log("✓ Zero-Copy Framebuffer and Stats memory boundaries intact on all instances.");

    // 9. 5th Player Room-Full Rejection & Recovery
    console.log("\n=== Verifying 5th Player Room-Full Rejection & Recovery ===");
    console.log(`P5 Rejection: Visible=${res.p5RoomFullVisible}, ConnectingHidden=${res.p5ConnectingHidden}, Status="${res.p5Status}", Role="${res.p5Role}", Message="${res.p5Message}"`);
    assert.strictEqual(res.p5RoomFullVisible, true, "5th player must display #room-full-overlay when attempting to join a full 4/4 room");
    assert.strictEqual(res.p5ConnectingHidden, true, "5th player must transition out of 'Connecting...' spinner overlay upon rejection");
    assert.strictEqual(res.p5Status, "Room Full (4/4)", "5th player net-stat-status must be 'Room Full (4/4)'");
    assert.strictEqual(res.p5Role, "ROOM FULL (4/4)", "5th player net-stat-role must be 'ROOM FULL (4/4)'");
    assert(res.p5Message.includes("Room is full") || res.p5Message.includes("occupied"), "5th player message must describe room full / all slots occupied");
    assert.deepStrictEqual(res.p5Badges, ["ROOM FULL", "ROOM FULL", "ROOM FULL", "ROOM FULL"], "5th player slot badges must indicate ROOM FULL");
    assert.strictEqual(res.p5HasActionButtons, true, "5th player overlay must provide Play Local, Host Room, and Try Again buttons");
    assert.strictEqual(res.p5RecoveredToLocal, true, "Clicking 'Play Local' on rejected player must cleanly recover into Local mode");
    console.log("✓ 5th player full-room rejection, explicit signaling message, error overlay transition, and local recovery verified.");

    // 10. Two-Stage Protocol Version Guards (Signaling + UX)
    console.log("\n=== Verifying Two-Stage Protocol Version Guards ===");
    console.log(`Host Rejection: Reason="${res.hostRejectionReason}", HostVer=${res.hostRejectionHostVer}, ClientVer=${res.hostRejectionClientVer}, Msg="${res.hostRejectionMsg}"`);
    assert.strictEqual(res.hostRejectionReason, "version_mismatch", "Host must reject client with version_mismatch");
    assert.strictEqual(res.hostRejectionHostVer, 1, "Host version must be 1");
    assert.strictEqual(res.hostRejectionClientVer, 99, "Client version must reflect 99");
    assert(res.hostRejectionMsg.includes("Protocol version mismatch"), "Rejection message must indicate protocol version mismatch");

    console.log(`Mismatch UI: Visible=${res.mismatchOverlayVisible}, ConnectingHidden=${res.mismatchConnectingHidden}, Status="${res.mismatchStatus}", Role="${res.mismatchRole}", HostVal="${res.mismatchHostText}", ClientVal="${res.mismatchClientText}"`);
    assert.strictEqual(res.mismatchOverlayVisible, true, "Version mismatch overlay must be visible upon receiving version_mismatch rejection");
    assert.strictEqual(res.mismatchConnectingHidden, true, "Connecting spinner overlay must be hidden on version mismatch");
    assert.strictEqual(res.mismatchStatus, "Version Mismatch", "Status must report Version Mismatch");
    assert.strictEqual(res.mismatchRole, "VERSION MISMATCH", "Role badge must report VERSION MISMATCH");
    assert.strictEqual(res.mismatchHostText, "v1", "Host version element must display v1");
    assert.strictEqual(res.mismatchClientText, "v99", "Client version element must display v99");
    assert.strictEqual(res.mismatchHasActionButtons, true, "Version mismatch overlay must have Reload and Play Local buttons");
    assert.strictEqual(res.mismatchRecoveredToLocal, true, "Clicking 'Play Local' on version mismatch overlay must cleanly recover into Local mode");
    console.log("✓ Two-stage protocol version guard across signaling and UI, host rejection, error modal transition, and local recovery verified.");

    // 11. Cross-Browser / Cross-Machine Isolated MQTT Signaling Verification
    console.log("\n=== Verifying Cross-Browser/Cross-Machine Isolated MQTT Signaling ===");
    console.log(`MQTT Room: ${res.mqttRoomCode}, Host Status: "${res.mqttHostStatus}", Joiner Status: "${res.mqttJoinerStatus}"`);
    console.log(`MQTT Host Role: "${res.mqttHostRole}", Joiner Role: "${res.mqttJoinerRole}"`);
    console.log(`MQTT P1 Movement: Init=${res.mqttHostInitX} -> Final Host=${res.mqttHostFinalX}, Joiner Seen=${res.mqttJoinerSeenX}`);
    console.log(`MQTT Checksums: Host=0x${res.mqttHostChecksum.toString(16)}, Joiner=0x${res.mqttJoinerChecksum.toString(16)}`);

    assert.strictEqual(res.mqttHostStatus, "Connected", "Isolated MQTT Host must report 'Connected' status");
    assert.strictEqual(res.mqttJoinerStatus, "Connected", "Isolated MQTT Joiner must report 'Connected' status");
    assert.strictEqual(res.mqttHostRole, "P1 RUBY (HOST)", "Isolated MQTT Host role must be P1 RUBY (HOST)");
    assert(res.mqttJoinerRole.includes("P2 SAPPHIRE"), "Isolated MQTT Joiner role must be P2 SAPPHIRE");
    assert(res.mqttHostFinalX > res.mqttHostInitX, "P1 must move Right on MQTT Host");
    assert.strictEqual(res.mqttJoinerSeenX, res.mqttHostFinalX, "Joiner over isolated MQTT must observe exact P1 position from Host");
    assert.strictEqual(res.mqttHostChecksum, res.mqttJoinerChecksum, "Deterministic state checksums must match across isolated MQTT mesh");
    console.log("✓ Cross-browser/cross-machine isolated pure-MQTT signaling and WebRTC DataChannel connection verified without local transports.");

    console.log("\n==================================================================");
    console.log("🎉 ALL 4-PLAYER WEBRTC ROLLBACK MULTIPLAYER GATES PASSED! 🎉");
    console.log("==================================================================");
} catch (err) {
    console.error("\n❌ Headless Multiplayer Test Failed:", err);
    process.exit(1);
}
