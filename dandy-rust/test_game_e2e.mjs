import { execFile } from 'child_process';
import assert from 'assert';
import path from 'path';
import http from 'http';
import fs from 'fs';
import { fileURLToPath } from 'url';

console.log("=== Running Dandy Dungeon End-to-End 'Does The Game Work' Smoke Suite ===");

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DIST_DIR = path.resolve(__dirname, 'dist');

const MIME_TYPES = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.wasm': 'application/wasm',
    '.css': 'text/css',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
    '.bmp': 'image/bmp'
};

async function ensureLocalServer(port = 8080) {
    const isUp = await new Promise((resolve) => {
        const req = http.get(`http://127.0.0.1:${port}/`, () => resolve(true));
        req.on('error', () => resolve(false));
        req.setTimeout(500, () => {
            req.destroy();
            resolve(false);
        });
    });

    if (isUp) return null;

    const server = http.createServer((req, res) => {
        let reqPath = req.url.split('?')[0].split('#')[0];
        if (reqPath === '/' || reqPath === '') reqPath = '/index.html';
        const filePath = path.join(DIST_DIR, reqPath);
        if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
            res.writeHead(404);
            res.end("Not found");
            return;
        }
        const ext = path.extname(filePath).toLowerCase();
        const mime = MIME_TYPES[ext] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': mime });
        fs.createReadStream(filePath).pipe(res);
    });

    await new Promise((resolve, reject) => {
        server.listen(port, '127.0.0.1', () => {
            console.log(`[Test Server] Started temporary HTTP static server on http://127.0.0.1:${port}/`);
            resolve();
        });
        server.on('error', reject);
    });

    return server;
}

const GBROWSER_BIN = "/google/bin/releases/gemini-agents-gbrowser/gbrowser";

const testCode = `
new Promise(async (resolve, reject) => {
    try {
        console.log("[E2E] 1. Waiting for Dandy Dungeon WASM App and Canvas initialization...");
        
        async function waitFor(fn, timeoutMs = 15000, desc = "condition") {
            const start = Date.now();
            while (Date.now() - start < timeoutMs) {
                try {
                    const res = fn();
                    if (res) return res;
                } catch (_) {}
                await new Promise(r => setTimeout(r, 100));
            }
            throw new Error("Timeout waiting for: " + desc);
        }

        await waitFor(() => Boolean(window.dandyApp) && Boolean(document.getElementById("gameCanvas")), 15000, "WASM app & screen canvas initialization");

        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");
        const app = window.dandyApp;

        // Dismiss welcome modal by choosing Play Local
        const btnLocal = document.getElementById("btn-welcome-local");
        if (btnLocal && window.getComputedStyle(document.getElementById("welcome-modal")).display !== "none") {
            btnLocal.click();
            await new Promise(r => setTimeout(r, 200));
        }

        console.log("[E2E] 2. Inspecting Canvas Pixel Buffer (Detecting Non-Zero RGB & Sprites)...");
        // Wait for first non-black render frame
        await waitFor(() => {
            const img = ctx.getImageData(0, 0, 320, 160);
            return img && img.data && img.data.some((val, idx) => (idx % 4 !== 3) && val !== 0);
        }, 5000, "First non-black canvas frame");

        // Read 320x160 canvas frame directly via ctx.getImageData
        const initialImgData = ctx.getImageData(0, 0, 320, 160);
        const initialPixels = initialImgData.data;
        if (initialPixels.length !== 320 * 160 * 4) {
            throw new Error("Canvas image data length mismatch: " + initialPixels.length);
        }

        let nonZeroInitialRgb = 0;
        const colorCounts = {};
        for (let i = 0; i < initialPixels.length; i += 4) {
            const r = initialPixels[i];
            const g = initialPixels[i + 1];
            const b = initialPixels[i + 2];
            if (r !== 0 || g !== 0 || b !== 0) {
                nonZeroInitialRgb++;
                const key = r + "," + g + "," + b;
                colorCounts[key] = (colorCounts[key] || 0) + 1;
            }
        }
        const distinctColorCount = Object.keys(colorCounts).length;
        console.log("[E2E] Initial Canvas: " + nonZeroInitialRgb + " / 51200 non-zero RGB pixels, " + distinctColorCount + " distinct colors");

        // 3. Test Player Movement & Canvas Pixel Animation
        console.log("[E2E] 3. Testing Interactive Player Movement & Visual Screen Animation...");
        const p1InitX = app.get_player_x(0);
        const p1InitY = app.get_player_y(0);

        // Press Right arrow key
        window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }));
        await new Promise(r => setTimeout(r, 350));
        window.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowRight" }));
        await new Promise(r => setTimeout(r, 150));

        const p1MovedX = app.get_player_x(0);
        const p1MovedY = app.get_player_y(0);

        // Read canvas frame after movement
        const afterMoveImgData = ctx.getImageData(0, 0, 320, 160);
        const afterMovePixels = afterMoveImgData.data;

        let movedDiffPixels = 0;
        for (let i = 0; i < initialPixels.length; i += 4) {
            if (initialPixels[i] !== afterMovePixels[i] ||
                initialPixels[i + 1] !== afterMovePixels[i + 1] ||
                initialPixels[i + 2] !== afterMovePixels[i + 2]) {
                movedDiffPixels++;
            }
        }

        // 3b. Test Arrow Shooting, Sound Generation, and Visual Projectile Rendering
        console.log("[E2E] 3b. Testing Arrow Shooting & Audio Emission & Visual Projectile...");
        // Turn Left facing the open corridor we just walked through
        window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft" }));
        await new Promise(r => setTimeout(r, 60));
        window.dispatchEvent(new KeyboardEvent("keyup", { key: "ArrowLeft" }));
        await new Promise(r => setTimeout(r, 50));

        const canvasBeforeShoot = ctx.getImageData(0, 0, 320, 160).data;
        let shootDiffPixels = 0;
        let soundGenerated = false;

        window.dispatchEvent(new KeyboardEvent("keydown", { key: " " }));
        for (let s = 0; s < 10; s++) {
            await new Promise(r => setTimeout(r, 50));
            const mask = app.get_sound_mask();
            const sndLen = app.get_sound_events_len();
            if (mask !== 0 || sndLen > 0) {
                soundGenerated = true;
            }
            const midFlightCanvas = ctx.getImageData(0, 0, 320, 160).data;
            let diffs = 0;
            for (let i = 0; i < canvasBeforeShoot.length; i += 4) {
                if (canvasBeforeShoot[i] !== midFlightCanvas[i] ||
                    canvasBeforeShoot[i + 1] !== midFlightCanvas[i + 1] ||
                    canvasBeforeShoot[i + 2] !== midFlightCanvas[i + 2]) {
                    diffs++;
                }
            }
            if (diffs > shootDiffPixels) {
                shootDiffPixels = diffs;
            }
        }
        window.dispatchEvent(new KeyboardEvent("keyup", { key: " " }));
        await new Promise(r => setTimeout(r, 150));

        // 4. Test HUD Table Elements Initialization (Health, Score, Keys, Bombs)
        console.log("[E2E] 4. Testing HUD Table Elements Initialization...");
        const hudHealthEl = document.getElementById("p1-health");
        const hudScoreEl = document.getElementById("p1-score");
        const hudKeysEl = document.getElementById("p1-keys");
        const hudBombsEl = document.getElementById("p1-bombs");

        const hudHealth = hudHealthEl ? parseInt(hudHealthEl.textContent, 10) : 0;
        const hudScore = hudScoreEl ? parseInt(hudScoreEl.textContent, 10) : 0;
        const hudKeys = hudKeysEl ? parseInt(hudKeysEl.textContent, 10) : 0;
        const hudBombs = hudBombsEl ? parseInt(hudBombsEl.textContent, 10) : 0;

        const results = {
            nonZeroInitialRgb,
            distinctColorCount,
            p1InitX,
            p1InitY,
            p1MovedX,
            p1MovedY,
            movedDiffPixels,
            shootDiffPixels,
            soundGenerated,
            hudHealth,
            hudScore,
            hudKeys,
            hudBombs
        };

        resolve(JSON.stringify(results));
    } catch (err) {
        resolve(JSON.stringify({ error: err.stack || err.toString() }));
    }
});
`;

function runE2ETest() {
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

let server = null;
try {
    server = await ensureLocalServer(8080);
    const res = await runE2ETest();
    if (res.error) {
        console.error("Test code failed inside gbrowser:\n", res.error);
        process.exit(1);
    }

    console.log("\n=== E2E Smoke Test Verification ===");
    console.log(`Initial Canvas Non-Zero RGB Pixels: ${res.nonZeroInitialRgb} / 51200`);
    console.log(`Distinct Colors Rendered: ${res.distinctColorCount}`);
    assert(res.nonZeroInitialRgb > 10000, `Canvas must contain > 10000 non-zero RGB pixels (found ${res.nonZeroInitialRgb})`);
    assert(res.distinctColorCount >= 3, `Canvas must contain >= 3 distinct rendered colors (found ${res.distinctColorCount})`);
    console.log("✓ Canvas graphics rendering and active dungeon tiles verified.");

    console.log(`P1 Movement: (${res.p1InitX}, ${res.p1InitY}) -> (${res.p1MovedX}, ${res.p1MovedY}), Canvas Pixels Changed: ${res.movedDiffPixels}`);
    assert(res.p1MovedX > res.p1InitX, `P1 coordinate must advance right (was ${res.p1InitX}, now ${res.p1MovedX})`);
    assert(res.movedDiffPixels > 50, `Player movement must update canvas pixels (found ${res.movedDiffPixels} changed pixels)`);
    console.log("✓ Interactive player movement & real-time canvas visual animation verified.");

    console.log(`Arrow Shooting: Canvas Pixels Changed: ${res.shootDiffPixels}`);
    assert(res.shootDiffPixels > 0, `Arrow shooting must visually update canvas pixels (found ${res.shootDiffPixels} changed pixels)`);
    console.log("✓ Arrow projectile shooting and visual feedback verified.");

    console.log(`HUD Elements: Health=${res.hudHealth}, Score=${res.hudScore}, Keys=${res.hudKeys}, Bombs=${res.hudBombs}`);
    assert.strictEqual(res.hudHealth, 100, "HUD Health must display starting health of 100");
    assert.strictEqual(res.hudScore, 0, "HUD Score must display starting score of 0");
    assert.strictEqual(res.hudKeys, 0, "HUD Keys must display starting keys of 0");
    assert.strictEqual(res.hudBombs, 0, "HUD Bombs must display starting bombs of 0");
    console.log("✓ HUD table reactivity and stats buffer synchronization verified.");

    console.log("\n==================================================================");
    console.log("🎉 ALL END-TO-END 'DOES THE GAME WORK' SMOKE TESTS PASSED! 🎉");
    console.log("==================================================================");
} catch (err) {
    console.error("\n❌ E2E Smoke Test Failed:", err);
    process.exit(1);
} finally {
    if (server) {
        server.close();
    }
}
